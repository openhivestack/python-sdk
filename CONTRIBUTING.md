# Contributing to Openhive

First off, thank you for considering contributing to Openhive! It's people like you that make the open-source community such a great place.

## How Can I Contribute?

### Reporting Bugs

If you find a bug, please open an issue and provide as much detail as possible, including:
- A clear and descriptive title.
- Steps to reproduce the bug.
- The expected behavior and what actually happened.
- Your environment details (e.g., Node.js version, OS).

### Suggesting Enhancements

If you have an idea for an enhancement, please open an issue to discuss it. This allows us to coordinate our efforts and prevent duplicated work.

### Pull Requests

1.  **Fork the repository** and create your branch from `main`.
2.  **Install dependencies** by running `yarn install`.
3.  **Make your changes** in a separate branch.
4.  **Ensure the test suite passes** by running `npx nx test <package-name>`.
5.  **Make sure your code lints** by running `npx nx lint <package-name>`.
6.  **Submit a pull request** with a clear description of your changes.

## Development Workflow

- **Build a package:** `npx nx build <package-name>`
- **Run tests:** `npx nx test <package-name>`
- **Lint a package:** `npx nx lint <package-name>`

## Code of Conduct

We have a [Code of Conduct](CODE_OF_CONDUCT.md) that all contributors are expected to follow. Please be respectful and considerate of others.
