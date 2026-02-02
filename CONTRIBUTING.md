# Contributing to GLTCH

Thanks for your interest in contributing to GLTCH!

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Setup

```bash
# Clone
git clone https://github.com/your-username/glitch_agent.git
cd glitch_agent

# Install Python deps
pip install -r requirements.txt
pip install pytest ruff mypy

# Install Node deps
npm install

# Run development
npm run dev
```

## Code Style

### Python

- Use type hints
- Keep lines under 100 characters
- Use `ruff` for linting
- Follow existing patterns

### TypeScript

- Strict typing (no `any`)
- Use ESM modules
- Follow existing patterns

## Testing

```bash
# Python
pytest tests/

# TypeScript
npm test
```

## Commit Messages

Use conventional commits:

- `feat: add new feature`
- `fix: fix a bug`
- `docs: update documentation`
- `refactor: code cleanup`
- `test: add tests`
- `chore: maintenance`

## Pull Requests

1. Update documentation if needed
2. Add tests for new features
3. Ensure CI passes
4. Request review

## Code of Conduct

Be respectful. No harassment. Keep it professional.

## Questions?

Open an issue or start a discussion.
