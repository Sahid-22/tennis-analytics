# Contributing to SportRadar Tennis Analytics

Thank you for your interest in contributing! This document outlines the process for setting up your environment and submitting changes.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-github-username>/sportradar-tennis-analytics.git
   cd SportRadar_Tennis_Analytics
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   make dev
   ```

4. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```

## Code Style

This project follows strict code style guidelines:
- We use `ruff` for linting and formatting.
- Maximum line length is 100 characters.
- Double quotes are preferred for strings.
- Type hints are mandatory. Check with `make typecheck`.

## Testing

- We use `pytest` for running tests.
- Run tests locally with `make test`.
- All tests must pass before a PR can be merged.
- Aim for a minimum of 60% test coverage.

## Pull Request Process

1. Create a new branch for your feature or bugfix: `git checkout -b feature/your-feature-name`
2. Make your changes and commit them with descriptive messages.
3. Push your branch and open a Pull Request against the `main` branch.
4. Ensure all CI checks pass.
5. Request a review from the maintainers.

## Commit Messages

- Use clear and concise commit messages.
- Start with a capitalized, imperative verb (e.g., "Add feature", "Fix bug").
- Keep the first line under 72 characters.
- Provide additional context in the body if necessary.
