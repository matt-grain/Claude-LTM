# Development Guide

## Setup

```bash
# Clone and install
git clone <repo-url>
cd LTM
uv sync --all-groups
```

## Running Tests

```bash
# All tests
uv run pytest tests/ -q

# Specific test file
uv run pytest tests/test_storage.py -v

# With coverage
uv run pytest tests/ --cov=ltm
```

## Linting & Type Checking

```bash
# Lint
uv run ruff check .

# Auto-fix lint issues
uv run ruff check . --fix

# Type check
uv run pyright
```

## Building

```bash
# Build wheel and sdist
uv build

# Output in dist/
ls dist/
# ltm-0.2.0-py3-none-any.whl
# ltm-0.2.0.tar.gz
```

## Release Process

### 1. Update version in pyproject.toml

```bash
# Edit pyproject.toml
version = "0.3.0"
```

### 2. Commit the changes

```bash
git add -A
git commit -m "Release v0.3.0

- Feature X
- Fix Y
- Improvement Z"
```

### 3. Create an annotated tag

```bash
git tag -a v0.3.0 -m "LTM v0.3.0

## What's New

- Feature X: description
- Fix Y: description
- Improvement Z: description

## Upgrade

Download the wheel from release assets or build from source."
```

### 4. Push to trigger the release

```bash
git push origin main
git push origin v0.3.0
```

The GitHub Actions release workflow will:
- Run all tests
- Build the wheel
- Create a GitHub Release with the tag message as release notes
- Attach the `.whl` and `.tar.gz` files

### Prerelease versions

Tags containing `-` are marked as prereleases:

```bash
git tag -a v0.3.0-beta -m "Beta release for testing"
git push origin v0.3.0-beta
```

## CI/CD

### On every push/PR to main:
- Lint with ruff
- Type check with pyright
- Run pytest
- Build wheel (uploaded as artifact)

### On version tags (v*):
- Run tests
- Build wheel
- Create GitHub Release with assets

## Project Structure

```
ltm/
├── cli.py              # CLI entry point
├── core/               # Core models and types
├── storage/            # SQLite storage layer
├── commands/           # Slash commands (/remember, /recall, etc.)
├── hooks/              # Claude Code hooks (session_start, session_end)
├── lifecycle/          # Decay and injection logic
└── tools/              # Setup and seed import tools

tests/                  # Test suite
commands/               # Skill YAML definitions
seeds/                  # Starter memory seeds
```
