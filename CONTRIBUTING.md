# Contributing to familiar-ai

Thank you for your interest! Here's how to get started.

## Development setup

```bash
git clone https://github.com/kmizu/familiar-ai
cd familiar-ai
uv sync
```

## Before submitting a PR

```bash
uv run ruff check .        # lint
uv run ruff format .       # format
uv run pytest -v           # tests
```

All three must pass cleanly.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) in **English**:

```
feat: add support for USB microphone input
fix: prevent camera reconnect loop on timeout
docs: clarify hardware requirements in README
chore: bump anthropic to 0.42.0
```

## Pull requests

- Keep PRs focused — one thing per PR
- Add tests for new behavior
- Update `CHANGELOG.md` under `[Unreleased]`

## Code style

- Python 3.10+, formatted with `ruff`
- Line length: 100
- Async-first (`asyncio`)

## Questions?

Open an issue — we're happy to help.
