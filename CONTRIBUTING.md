# Contributing to Pyrgo

First off, thanks for taking the time to contribute! 

The following is a set of guidelines for contributing to Pyrgo. These are just guidelines, not rules. Use your best judgment and feel free to propose changes to this document in a pull request.

## How Can I Contribute?

### Reporting Bugs
This section guides you through submitting a bug report for Pyrgo. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

- **Use a clear and descriptive title** for the issue to identify the problem.
- **Describe the exact steps which reproduce the problem** in as many details as possible.
- **Provide specific examples** to demonstrate the steps.

### Pull Requests

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone [https://github.com/your-username/pyrgo.git](https://github.com/your-username/pyrgo.git)
    cd pyrgo
    ```
3.  **Create a virtual environment** to keep dependencies isolated:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scriptsctivate`
    ```
4.  **Install dependencies** (we use Poetry/pip):
    ```bash
    pip install -r requirements.txt
    ```
5.  **Create a new branch** for your feature or fix:
    ```bash
    git checkout -b feature/amazing-feature
    ```
6.  **Commit your changes** with clear messages:
    ```bash
    git commit -m "Add some amazing feature"
    ```
7.  **Push to the branch**:
    ```bash
    git push origin feature/amazing-feature
    ```
8.  **Open a Pull Request** on the main Pyrgo repository.

## Style Guide
- We follow **PEP 8** standards.
- Please write clear comments for complex logic.
- If you add a new feature, please add a corresponding test case (if applicable).