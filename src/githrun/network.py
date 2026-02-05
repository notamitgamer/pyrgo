import requests
from urllib.parse import urlparse
from .utils import print_error, load_cache, save_cache, ConfigManager

class RateLimitError(Exception):
    pass

def get_auth_headers():
    token = ConfigManager.get_api_key()
    if token:
        return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    return {"Accept": "application/vnd.github.v3+json"}

def convert_to_raw_url(url: str) -> str:
    """
    Converts GitHub/Gist URLs to raw content URLs.
    Supports bookmarks via ConfigManager in core.py, not here.
    """
    parsed = urlparse(url)
    
    if "gist.github.com" in parsed.netloc:
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2:
            return f"gist:{parts[1]}"
        return url

    if "github.com" in parsed.netloc:
        # Standard: user/repo/blob/BRANCH/path
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 4 and parts[2] == "blob":
            # Reconstruction for raw.githubusercontent
            # Format: user/repo/BRANCH/path
            new_path = "/".join([parts[0], parts[1]] + parts[3:])
            return f"https://raw.githubusercontent.com/{new_path}"
            
    return url

def fetch_url_content(url: str) -> str:
    try:
        # For raw.githubusercontent.com, headers usually aren't needed but auth helps with private repos
        headers = get_auth_headers()
        response = requests.get(url, headers=headers)
        
        if response.status_code == 404 and "Authorization" in headers:
            # Fallback: Sometimes raw links for private repos behave differently
            # We might need to use the API to get download_url if this fails
            pass

        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        if e.response is not None and e.response.status_code == 404:
            print_error("File not found (404). If this is a private repo, ensure you are logged in.")
        else:
            print_error(f"Failed to download: {e}")
        return None

def fetch_gist_content(gist_id: str):
    api_url = f"https://api.github.com/gists/{gist_id}"
    data = _fetch_api(api_url)
    if data:
        files = data.get("files", {})
        if files:
            return list(files.values())[0].get("content")
    return None

def get_repo_details(url: str):
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None, None

def fetch_tree_recursively(owner: str, repo: str, branch: str = None):
    cache_key = f"{owner}_{repo}_{branch or 'default'}_tree"
    
    cached = load_cache(cache_key)
    if cached: return cached

    # Determine branch if not provided
    if not branch:
        # Try to guess default branch
        repo_info = _fetch_api(f"https://api.github.com/repos/{owner}/{repo}")
        if repo_info:
            branch = repo_info.get("default_branch", "main")
        else:
            branch = "main"

    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    data = _fetch_api(url)
    
    if data:
        save_cache(cache_key, data)
        return data
    return None

def fetch_folder_contents(url: str):
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    
    # Check for branch in URL: github.com/user/repo/tree/BRANCH/path
    if len(parts) < 4 or parts[2] != "tree":
        # Root
        if len(parts) == 2:
             return _fetch_api(f"https://api.github.com/repos/{parts[0]}/{parts[1]}/contents")
        return None
    
    owner, repo, branch = parts[0], parts[1], parts[3]
    path = "/".join(parts[4:])
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    return _fetch_api(api_url)

def _fetch_api(url):
    try:
        headers = get_auth_headers()
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 403:
            # Check rate limit
            limit = resp.headers.get("X-RateLimit-Remaining")
            if limit == "0":
                raise RateLimitError("GitHub API Rate Limit Exceeded.")
        
        if resp.status_code == 200:
            return resp.json()
        return None
    except RateLimitError:
        raise
    except Exception:
        return None