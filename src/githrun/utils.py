import os
import sys
import tempfile
import json
import time
import shutil
import venv
import platform
import subprocess
import importlib.util
from pathlib import Path
from typing import Optional, Dict
from contextlib import contextmanager
from rich.console import Console

console = Console()

# Paths
APP_DIR = Path.home() / ".githrun"
CACHE_DIR = APP_DIR / "cache"
BIN_DIR = APP_DIR / "bin"
CONFIG_FILE = APP_DIR / "config.json"
CACHE_DURATION = 600  # 10 minutes

def ensure_dirs():
    APP_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)
    BIN_DIR.mkdir(exist_ok=True)

class ConfigManager:
    """Manages persistent configuration (Tokens, Bookmarks)."""
    
    @staticmethod
    def load() -> Dict:
        ensure_dirs()
        if not CONFIG_FILE.exists():
            return {"api_key": None, "bookmarks": {}}
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {"api_key": None, "bookmarks": {}}

    @staticmethod
    def save(data: Dict):
        ensure_dirs()
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def get_api_key() -> Optional[str]:
        # 1. Check Environment Variable
        if os.environ.get("GITHUB_TOKEN"):
            return os.environ["GITHUB_TOKEN"]
        
        # 2. Check .env file in current directory
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        if line.strip().startswith("GITHUB_TOKEN="):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except:
                pass

        # 3. Check Global Config
        config = ConfigManager.load()
        return config.get("api_key")

    @staticmethod
    def set_api_key(key: str):
        config = ConfigManager.load()
        config["api_key"] = key
        ConfigManager.save(config)

    @staticmethod
    def add_bookmark(name: str, url: str):
        config = ConfigManager.load()
        if "bookmarks" not in config:
            config["bookmarks"] = {}
        config["bookmarks"][name] = url
        ConfigManager.save(config)

    @staticmethod
    def get_bookmark(name: str) -> Optional[str]:
        config = ConfigManager.load()
        return config.get("bookmarks", {}).get(name)
    
    @staticmethod
    def list_bookmarks() -> Dict[str, str]:
        return ConfigManager.load().get("bookmarks", {})

# Cache Logic
def load_cache(key: str):
    ensure_dirs()
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if time.time() - data["timestamp"] < CACHE_DURATION:
                return data["content"]
        except:
            pass
    return None

def save_cache(key: str, content: any):
    ensure_dirs()
    cache_file = CACHE_DIR / f"{key}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"timestamp": time.time(), "content": content}, f)
    except:
        pass

# Dependency & Venv Logic
def check_package_installed(package_name: str) -> bool:
    if package_name in sys.builtin_module_names:
        return True
    try:
        return importlib.util.find_spec(package_name) is not None
    except Exception:
        return False

class VenvManager:
    """Manages temporary virtual environments for auto-installing dependencies."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="githrun_env_")
        self.venv_dir = Path(self.temp_dir)
        self.python_exe = self._get_python_exe()
        self.pip_exe = self._get_pip_exe()

    def _get_python_exe(self):
        if platform.system() == "Windows":
            return self.venv_dir / "Scripts" / "python.exe"
        return self.venv_dir / "bin" / "python"

    def _get_pip_exe(self):
        if platform.system() == "Windows":
            return self.venv_dir / "Scripts" / "pip.exe"
        return self.venv_dir / "bin" / "pip"

    def create(self):
        """Creates the virtual environment."""
        console.print("[blue]Creating temporary virtual environment...[/blue]")
        venv.create(self.venv_dir, with_pip=True)

    def install(self, packages: list):
        """Installs packages into the venv."""
        if not packages:
            return
        console.print(f"[blue]Installing dependencies: {', '.join(packages)}...[/blue]")
        subprocess.check_call([str(self.pip_exe), "install"] + packages, stdout=subprocess.DEVNULL)

    def cleanup(self):
        """Deletes the virtual environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

# Standard Helpers
def print_error(msg: str):
    console.print(f"[bold red]Error:[/bold red] {msg}")

def print_info(msg: str):
    console.print(f"[bold blue]Info:[/bold blue] {msg}")

def print_success(msg: str):
    console.print(f"[bold green]Success:[/bold green] {msg}")

def print_warning(msg: str):
    console.print(f"[bold yellow]Warning:[/bold yellow] {msg}")

@contextmanager
def temp_python_file(content: str):
    fd, path = tempfile.mkstemp(suffix=".py", text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
            tmp.write(content)
        yield path
    finally:
        if os.path.exists(path):
            os.remove(path)