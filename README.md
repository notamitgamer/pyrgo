# Pyrgo 

> **Execute Python code directly from GitHub, explore remote repositories, and find files instantly.**

Pyrgo is a lightweight CLI tool that turns GitHub into your remote Python interpreter. Whether you want to quickly test a script without cloning a massive repo, inspect a file's content, or map out a project structure, Pyrgo handles it in seconds.

## Features

* **Remote Execution**: Run Python scripts directly from raw GitHub URLs.
* **Safety First**: Inspect code before execution to ensure no malicious activity.
* **Repo Exploration**: View the contents of remote folders without leaving your terminal.
* **Deep Search**: Find specific files inside complex repositories instantly.
* **Smart Caching**: (Coming Soon) Caches files locally to save bandwidth.

## Installation

```bash
pip install pyrgo
```

## Usage

### 1. Run a Script
Don't clone the whole repo just to run one file.

```bash
# Basic run
pyrgo run [https://github.com/notamitgamer/adpkg/blob/main/test1.py](https://github.com/notamitgamer/adpkg/blob/main/test1.py)

# Inspect source code before running (Recommended)
pyrgo run [https://github.com/notamitgamer/adpkg/blob/main/test1.py](https://github.com/notamitgamer/adpkg/blob/main/test1.py) --inspect
```

### 2. Show Folder Structure
Visualize what's inside a remote directory.

```bash
pyrgo show [https://github.com/notamitgamer/adpkg/tree/main/subfolder](https://github.com/notamitgamer/adpkg/tree/main/subfolder)
```

### 3. Find a File
Searching for a config file or specific logic?

```bash
# Syntax: pyrgo find <repo-url> <filename-or-extension>
pyrgo find [https://github.com/notamitgamer/adpkg](https://github.com/notamitgamer/adpkg) "config.py"
pyrgo find [https://github.com/notamitgamer/adpkg](https://github.com/notamitgamer/adpkg) ".json"
```

## Development

We use `poetry` for dependency management.

1.  Clone the repo.
2.  Install dependencies: `poetry install`
3.  Run the CLI locally: `poetry run pyrgo --help`

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

## Security

Found a bug? Please check our [Security Policy](SECURITY.md).

## License

This project is licensed under the MIT License.