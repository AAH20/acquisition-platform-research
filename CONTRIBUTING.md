# Contributing to Acquisition Platform

Thank you for your interest in contributing to the Acquisition Platform! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- A GitHub account

### Setting Up Development Environment

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/acquisition-platform-research.git
   cd acquisition-platform-research
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   make install
   ```

4. **Install pre-commit hooks**

   ```bash
   pre-commit install
   ```

## Development Workflow

### Creating a Branch

Create a new branch for your feature or bug fix:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### Making Changes

1. Make your changes in the appropriate module under `src/acquisition_platform/`
2. Add or update tests in `tests/`
3. Update documentation if needed

### Running Tests

Before submitting your changes, ensure all tests pass:

```bash
make test
```

### Code Quality

Run linting and type checking:

```bash
make lint
make typecheck
```

### Formatting

Format your code before committing:

```bash
make format
```

## Pull Request Process

1. **Update your branch**

   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run all checks**

   ```bash
   make all
   ```

3. **Commit your changes**

   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

4. **Push to your fork**

   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**

   - Go to the repository on GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template
   - Submit

## Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add dynamic pricing algorithm
fix: resolve entity resolution edge case
docs: update API documentation
```

## Code Style

- Follow PEP 8
- Use type hints for all function parameters and return values
- Maximum line length: 100 characters
- Use descriptive variable and function names
- Add docstrings to all public modules, classes, and functions

## Testing

- Write tests for all new features
- Maintain or improve code coverage
- Use pytest fixtures for test data
- Follow the Arrange-Act-Assert pattern

## Reporting Bugs

When reporting bugs, please include:

- A clear description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Python version and OS
- Relevant code snippets or tracebacks

## Feature Requests

When requesting features, please include:

- A clear description of the feature
- Use cases and motivation
- Any relevant examples or references

## License

By contributing, you agree that your contributions will be licensed under the AGPL-3.0 License.

## Questions?

If you have questions, please:

1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/NousResearch/hermes-agent/issues)
3. Open a new issue with the `question` label

Thank you for contributing!
