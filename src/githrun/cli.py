import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt
from typing import Optional

from .core import (
    execute_remote_code, 
    search_repository, 
    get_folder_contents, 
    download_file, 
    download_folder,
    install_tool,
    login_github,
    add_bookmark,
    list_bookmarks
)
from .network import RateLimitError, fetch_url_content, fetch_gist_content, convert_to_raw_url
from .utils import print_error, print_info, print_warning, print_success, ConfigManager

app = typer.Typer(help="Githrun: Run Python code from GitHub instantly.")
bookmark_app = typer.Typer(help="Manage bookmarks.")
app.add_typer(bookmark_app, name="bookmark")

console = Console()

# --- MAIN COMMANDS ---

@app.command()
def login(token: str = typer.Argument(..., help="Your GitHub Personal Access Token.")):
    """
    Authenticate with GitHub to increase rate limits and access private repos.
    """
    login_github(token)
    print_success("GitHub token saved successfully!")

@app.command()
def install(
    url: str = typer.Argument(..., help="URL of the script."),
    name: str = typer.Option(..., "--name", "-n", help="Name of the command tool.")
):
    """
    Install a remote script as a local command-line tool.
    """
    try:
        msg = install_tool(url, name)
        print_success(msg)
    except Exception as e:
        print_error(str(e))

@app.command()
def run(
    url: str = typer.Argument(..., help="GitHub URL, Gist URL, or Bookmark Name."),
    inspect: bool = typer.Option(False, "--inspect", "-i", help="Print code without running."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
    auto_install: bool = typer.Option(False, "--auto-install", help="Auto-install missing dependencies.")
):
    """Download and execute a remote Python script."""
    try:
        # Check bookmarks
        b_url = ConfigManager.get_bookmark(url)
        if b_url:
            print_info(f"Resolved bookmark '{url}' to: {b_url}")
            url = b_url

        if inspect:
            raw = convert_to_raw_url(url)
            if raw.startswith("gist:"):
                content = fetch_gist_content(raw.split(":")[1])
            else:
                content = fetch_url_content(raw)
            if content:
                console.print(Syntax(content, "python", theme="monokai", line_numbers=True))
            return

        if not yes:
            console.print(f"\n[bold yellow]SECURITY WARNING:[/bold yellow] Running remote code from:")
            console.print(f"[underline]{url}[/underline]\n")
            if not typer.confirm("Execute this script?"):
                raise typer.Exit()

        execute_remote_code(url, auto_install=auto_install)

    except RateLimitError:
        print_error("GitHub API Rate Limit Exceeded (60 reqs/hr).")
        if typer.confirm("Would you like to add an API Key to increase limits?"):
            token = Prompt.ask("Enter GitHub Token")
            login_github(token)
            print_success("Token saved! Please try running the command again.")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

# --- BOOKMARK COMMANDS ---

@bookmark_app.command("add")
def bookmark_add(name: str, url: str):
    """Save a URL as a bookmark."""
    add_bookmark(name, url)
    print_success(f"Bookmark '{name}' added.")

@bookmark_app.command("list")
def bookmark_list():
    """List all saved bookmarks."""
    bookmarks = list_bookmarks()
    if not bookmarks:
        print_warning("No bookmarks found.")
        return
    
    table = Table(title="Bookmarks")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="green")
    for name, url in bookmarks.items():
        table.add_row(name, url)
    console.print(table)

# --- EXISTING COMMANDS (UPDATED) ---

@app.command()
def find(
    repo_url: str = typer.Argument(..., help="GitHub repository URL."),
    query: str = typer.Argument(..., help="Search query (filename)."),
    interactive: bool = typer.Option(True, help="Enable interactive selection.")
):
    """Search for files in a repo."""
    try:
        with console.status("Scanning..."):
            from .core import search_repository
            results = search_repository(repo_url, query)
        
        if not results:
             print_warning("No results.")
             return

        table = Table(title=f"Results for {query}")
        table.add_column("#", style="yellow")
        table.add_column("Path", style="cyan")
        
        for idx, r in enumerate(results):
            table.add_row(str(idx+1), r['path'])
        console.print(table)

        if interactive:
            choice = Prompt.ask("Select file # to Run (or 'q')")
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(results):
                    execute_remote_code(results[idx]['raw_url'])

    except RateLimitError:
        print_error("Rate Limit Hit.")
        print_info("Use 'githrun login <token>' to fix this.")
    except Exception as e:
        print_error(str(e))

@app.command()
def download(
    url: str = typer.Argument(..., help="GitHub file or folder URL."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output path.")
):
    """Download file or folder."""
    try:
        from .core import download_folder, download_file
        if "/tree/" in url:
            path = download_folder(url, output)
            print_success(f"Downloaded folder: {path}")
        else:
            path = download_file(url, output)
            print_success(f"Downloaded file: {path}")
    except Exception as e:
        print_error(str(e))

@app.command()
def show(url: str = typer.Argument(..., help="GitHub folder URL.")):
    """Show folder contents."""
    try:
        from .core import get_folder_contents
        items = get_folder_contents(url)
        
        if not items:
            print_error("Empty folder or invalid URL.")
            return

        table = Table(title="Contents")
        table.add_column("Name")
        table.add_column("Type")
        
        for item in items:
            itype = "Dir" if item['type'] == 'dir' else "File"
            table.add_row(item['name'], itype)
        console.print(table)
    except Exception as e:
        print_error(str(e))

if __name__ == "__main__":
    app()