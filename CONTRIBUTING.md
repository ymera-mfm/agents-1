# Contributing to Project Agent

We welcome contributions to the Project Agent! To ensure a smooth and effective collaboration, please follow these guidelines.

## How to Contribute

### 1. Fork the Repository
Fork the `project-agent` repository to your GitHub account.

### 2. Clone Your Fork
Clone your forked repository to your local machine:
```bash
git clone https://github.com/your-username/project-agent.git
cd project-agent
```

### 3. Create a New Branch
Create a new branch for your feature or bug fix. Use a descriptive name:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-description
```

### 4. Make Your Changes
-   Implement your feature or fix the bug.
-   Ensure your code adheres to the project's coding standards.
-   Write clear, concise, and well-documented code.

### 5. Test Your Changes
-   Run existing tests to ensure no regressions have been introduced.
-   Write new unit and integration tests for your changes.
-   Ensure all tests pass.

### 6. Commit Your Changes
Commit your changes with a clear and descriptive commit message. Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification:
```bash
git commit -m "feat: Add new feature for X"
# or
git commit -m "fix: Resolve bug in Y"
```

### 7. Push to Your Fork
```bash
git push origin feature/your-feature-name
```

### 8. Create a Pull Request
-   Go to the original `project-agent` repository on GitHub.
-   Click on the "New Pull Request" button.
-   Provide a detailed description of your changes, including:
    -   What problem does this PR solve?
    -   How was it solved?
    -   Any relevant context or dependencies.
    -   Screenshots or examples (if applicable).
-   Link to any related issues.

## Coding Standards
-   **Python Formatting**: Adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines. Use `black` for automatic formatting.
-   **Type Hinting**: Use type hints for all function arguments and return values.
-   **Docstrings**: Write comprehensive docstrings for all modules, classes, and functions.
-   **Logging**: Use the `logging` module for all application logs.

## Security Guidelines
-   **Never hardcode sensitive information** (API keys, passwords, etc.). Use environment variables or a secure secrets management system.
-   **Validate all input** to prevent common vulnerabilities like SQL injection and XSS.
-   **Follow the principle of least privilege**.

## Code of Conduct
By contributing, you agree to abide by the project's Code of Conduct. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for more information.

Thank you for contributing to the Project Agent!
