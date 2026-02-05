import sys
import subprocess
import os
import re
import platform
import stat
from pathlib import Path
from typing import List, Dict, Optional
from .network import (
    convert_to_raw_url, 
    fetch_url_content, 
    fetch_gist_content,
    get_repo_details, 
    fetch_tree_recursively, 
    fetch_folder_contents
)
from .utils import (
    temp_python_file, 
    check_package_installed, 
    ConfigManager, 
    VenvManager, 
    BIN_DIR
)

def resolve_url(url: str) -> str:
    """Resolves bookmarks to full URLs."""
    bookmark = ConfigManager.get_bookmark(url)
    if bookmark:
        return bookmark
    return url

def execute_remote_code(url: str, args: List[str] = None, auto_install: bool = False) -> int:
    """Downloads and executes a Python script."""
    
    full_url = resolve_url(url)
    raw_url = convert_to_raw_url(full_url)
    
    if raw_url.startswith("gist:"):
        code_content = fetch_gist_content(raw_url.split(":")[1])
    else:
        code_content = fetch_url_content(raw_url)

    if not code_content:
        raise ValueError(f"Could not retrieve content from {full_url}")

    # Dependency Check
    missing_deps = scan_dependencies(code_content)
    
    if auto_install and missing_deps:
        # --- VIRTUAL ENV EXECUTION FLOW ---
        manager = VenvManager()
        try:
            manager.create()
            manager.install(missing_deps)
            
            # Save code to a file inside the temp dir (so it's near the venv)
            script_path = manager.venv_dir / "remote_script.py"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code_content)
                
            cmd = [str(manager.python_exe), str(script_path)]
            if args:
                cmd.extend(args)
            
            result = subprocess.run(cmd, capture_output=False)
            return result.returncode
        finally:
            manager.cleanup()
    else:
        # --- STANDARD EXECUTION FLOW ---
        if missing_deps:
            print(f"\033[93m[Warning] Missing packages: {', '.join(missing_deps)}. Use --auto-install to fix.\033[0m")

        with temp_python_file(code_content) as temp_file:
            cmd = [sys.executable, temp_file]
            if args:
                cmd.extend(args)
            result = subprocess.run(cmd, capture_output=False)
            return result.returncode

def install_tool(url: str, name: str) -> str:
    """Installs a remote script as a local command."""
    full_url = resolve_url(url)
    raw_url = convert_to_raw_url(full_url)
    content = fetch_url_content(raw_url)
    
    if not content:
        raise ValueError("Failed to download script.")
    
    target_path = BIN_DIR / f"{name}.py"
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Create executable shim
    if platform.system() == "Windows":
        bat_path = BIN_DIR / f"{name}.bat"
        with open(bat_path, "w") as f:
            f.write(f'@echo off\n"{sys.executable}" "{target_path}" %*')
        final_msg = f"Installed {name} to {BIN_DIR}.\nAdd this folder to your PATH to run it via `{name}`."
    else:
        # Linux/Mac
        shim_path = BIN_DIR / name
        with open(shim_path, "w") as f:
            f.write(f'#!/bin/sh\n"{sys.executable}" "{target_path}" "$@"')
        st = os.stat(shim_path)
        os.chmod(shim_path, st.st_mode | stat.S_IEXEC)
        final_msg = f"Installed {name} to {BIN_DIR}.\nAdd this folder to your PATH."

    return final_msg

def scan_dependencies(code: str) -> List[str]:
    imports = set()
    imports.update(re.findall(r'^\s*import\s+(\w+)', code, re.MULTILINE))
    imports.update(re.findall(r'^\s*from\s+(\w+)', code, re.MULTILINE))
    
    missing = []
    for imp in imports:
        if not check_package_installed(imp):
            missing.append(imp)
    return missing

def search_repository(repo_url: str, query: str) -> List[Dict[str, str]]:
    owner, repo = get_repo_details(repo_url)
    if not owner: raise ValueError("Invalid Repo URL")
    
    # Smart branch detection happens in network.py
    data = fetch_tree_recursively(owner, repo)
    if not data or "tree" not in data:
        return []

    results = []
    query_lower = query.lower()
    
    # Try to determine branch from data url or default to main for raw links
    branch = "main" 

    for item in data["tree"]:
        path = item["path"]
        if query_lower in path.lower():
            raw_link = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            results.append({"path": path, "type": item["type"], "raw_url": raw_link})
    return results

def get_folder_contents(url: str) -> List[Dict]:
    items = fetch_folder_contents(url)
    return items if items else []

def download_file(url: str, output_path: Optional[str] = None) -> str:
    full_url = resolve_url(url)
    raw_url = convert_to_raw_url(full_url)
    
    if raw_url.startswith("gist:"):
        content = fetch_gist_content(raw_url.split(":")[1])
        filename = "gist_script.py"
    else:
        content = fetch_url_content(raw_url)
        filename = raw_url.split("/")[-1]

    if not content:
        raise ValueError("Failed to download.")

    if not output_path:
        output_path = filename

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path

def download_folder(url: str, output_dir: Optional[str] = None) -> str:
    # Basic logic reused from previous step, ensuring resolve_url is called if we support folder bookmarks
    full_url = resolve_url(url)
    # ... (Rest of logic is same as previous, omitted for brevity but assumed present)
    # Re-implementing specifically for clarity:
    owner, repo = get_repo_details(full_url)
    parts = urlparse(full_url).path.strip("/").split("/")
    if len(parts) < 5 or parts[2] != "tree":
         raise ValueError("Invalid tree URL")
    
    target_path = "/".join(parts[4:])
    if not output_dir: output_dir = parts[-1]
    
    data = fetch_tree_recursively(owner, repo) # branch auto-detected
    if not data: raise ValueError("Could not fetch tree")
    
    count = 0
    os.makedirs(output_dir, exist_ok=True)
    for item in data["tree"]:
        if item['path'].startswith(target_path) and item['type'] == 'blob':
            rel = item['path'][len(target_path):].strip("/")
            local = os.path.join(output_dir, rel)
            os.makedirs(os.path.dirname(local), exist_ok=True)
            # Fetch
            raw = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{item['path']}"
            c = fetch_url_content(raw)
            if c:
                with open(local, "w", encoding="utf-8") as f: f.write(c)
                count += 1
    return f"{output_dir} ({count} files)"

# Config Wrappers for CLI
def login_github(token: str):
    ConfigManager.set_api_key(token)

def add_bookmark(name: str, url: str):
    ConfigManager.add_bookmark(name, url)

def list_bookmarks():
    return ConfigManager.list_bookmarks()