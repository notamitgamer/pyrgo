import os
import sys
import shutil
import githrun
from rich.console import Console
from rich.panel import Panel

console = Console()

# --- CONFIGURATION ---
# We use the repo you mentioned in the chat for testing
TEST_REPO = "https://github.com/notamitgamer/adpkg"
TEST_FILE = "https://github.com/notamitgamer/adpkg/blob/main/test1.py"
TEST_FOLDER = "https://github.com/notamitgamer/adpkg/tree/main/"
DOWNLOAD_TARGET = "test_download_artifact.py"

def print_header(title):
    console.print(Panel(f"[bold white]{title}[/bold white]", style="bold blue"))

def test_cli_command(cmd, description):
    console.print(f"\n[bold cyan]🔹 Testing CLI: {description}[/bold cyan]")
    console.print(f"[dim]Command: {cmd}[/dim]")
    
    exit_code = os.system(cmd)
    
    if exit_code == 0:
        console.print("[bold green]✔ Passed[/bold green]")
        return True
    else:
        console.print("[bold red]✘ Failed[/bold red]")
        return False

def test_python_api():
    print_header("Testing Python Source Code API")
    
    # 1. Search Repository
    console.print("\n[bold cyan]🔹 API: githrun.search_repository()[/bold cyan]")
    try:
        results = githrun.search_repository(TEST_REPO, "test1.py")
        if results:
            console.print(f"[green]✔ Success: Found {len(results)} matches.[/green]")
            for item in results[:1]: # Show first match
                console.print(f"   Found: {item['path']} ({item['raw_url']})")
        else:
            console.print("[yellow]⚠ Warning: No results found (API limit might be hit).[/yellow]")
    except Exception as e:
        console.print(f"[bold red]✘ Error:[/bold red] {e}")

    # 2. Get Folder Contents
    console.print("\n[bold cyan]🔹 API: githrun.get_folder_contents()[/bold cyan]")
    try:
        items = githrun.get_folder_contents(TEST_FOLDER)
        if items:
            console.print(f"[green]✔ Success: Fetched {len(items)} items from folder.[/green]")
        else:
            console.print("[yellow]⚠ Warning: Folder appears empty or API error.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]✘ Error:[/bold red] {e}")

    # 3. Download File
    console.print("\n[bold cyan]🔹 API: githrun.download_file()[/bold cyan]")
    try:
        path = githrun.download_file(TEST_FILE, output_path="api_download_test.py")
        if os.path.exists(path):
            console.print(f"[green]✔ Success: File downloaded to {path}[/green]")
            os.remove(path) # Cleanup
        else:
            console.print("[bold red]✘ Failed: File not found after download call.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]✘ Error:[/bold red] {e}")

def main():
    # Ensure we are in the right directory or package is installed
    if not shutil.which("githrun"):
        console.print("[bold red]CRITICAL: 'githrun' command not found.[/bold red]")
        console.print("Please run [bold]pip install .[/bold] in the root directory first.")
        return

    print_header("Starting githrun Feature Tests")

    # --- CLI TESTS ---
    
    # 1. Help Command
    test_cli_command("githrun --help", "Help Menu")

    # 2. Run Command (Non-interactive)
    # --yes skips the confirmation prompt
    test_cli_command(f"githrun run {TEST_FILE} --yes", "Run Remote Script")

    # 3. Inspect Mode
    # Should print code but not run it
    test_cli_command(f"githrun run {TEST_FILE} --inspect", "Inspect Code")

    # 4. Show Folder
    test_cli_command(f"githrun show {TEST_FOLDER}", "Show Folder Contents")

    # 5. Find File (Non-interactive)
    # Typer converts `interactive=True` to a flag `--no-interactive`
    test_cli_command(f"githrun find {TEST_REPO} test --no-interactive", "Find File")

    # 6. Download
    test_cli_command(f"githrun download {TEST_FILE} -o {DOWNLOAD_TARGET}", "Download File")
    if os.path.exists(DOWNLOAD_TARGET):
        console.print("[dim]   Verifying file existence... OK (Deleting now)[/dim]")
        os.remove(DOWNLOAD_TARGET)

    # 7. Bookmarks
    test_cli_command(f"githrun bookmark add test-bm {TEST_FILE}", "Add Bookmark")
    test_cli_command("githrun bookmark list", "List Bookmarks")
    test_cli_command("githrun run test-bm --yes", "Run from Bookmark")

    # --- API TESTS ---
    test_python_api()

    print_header("Test Suite Completed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Tests aborted by user.[/bold red]")