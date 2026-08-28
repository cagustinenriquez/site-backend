# Contributing

Thanks for your interest in contributing! This document provides guidelines for contributing to the site-backend.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/site-backend.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Follow the setup instructions in [GETTING_STARTED.md](./GETTING_STARTED.md)

## Development Workflow

1. Make your changes
2. Ensure tests pass: `npm test`
3. Commit your changes with a clear message
4. Push to your fork
5. Submit a pull request to the main repository

## Code Style

- Follow the existing code style
- Use meaningful variable and function names
- Keep functions focused and single-purpose
- Add comments only when the "why" is non-obvious

## Testing

- Write tests for new features
- Ensure all tests pass before submitting a PR
- Aim for meaningful test coverage

```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```

## Commit Messages

Use clear, descriptive commit messages:

- `feat: add new feature` - for new features
- `fix: resolve issue with X` - for bug fixes
- `docs: update documentation` - for documentation updates
- `refactor: improve code structure` - for refactoring
- `test: add tests for X` - for test additions

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure CI/CD checks pass
4. Request review from maintainers
5. Address feedback and iterate

## Questions or Issues?

Feel free to open an issue on GitHub for bugs or feature requests.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
