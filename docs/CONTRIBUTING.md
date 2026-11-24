# Contributing to OtoWall

Thank you for your interest in contributing to OtoWall! This guide outlines the development workflow, testing standards, and pull request procedures.

---

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/codewithevilxd/OtoWall.git
   cd OtoWall
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # Linux/macOS: source .venv/bin/activate
   ```

3. **Install the package in editable mode with development dependencies:**
   ```powershell
   pip install -e ".[dev,windows]"   # On Linux/macOS, use [dev,linux] or [dev,macos]
   ```

---

## Code Style & Formatting

We use [Ruff](https://github.com/astral-sh/ruff) for fast linting and code formatting.

- Check code style:
  ```bash
  ruff check src tests scripts
  ```
- Format code:
  ```bash
  ruff format src tests scripts
  ```

---

## Running Tests

All unit and integration tests are powered by [Pytest](https://docs.pytest.org/):

```bash
pytest -q
```

To run a specific test module:
```bash
pytest tests/test_ascii_composer.py -v
```

> [!NOTE]
> All wallpaper platform calls are mocked during testing. Running pytest will never mutate your real desktop wallpaper.

---

## Submitting Pull Requests

1. Create a feature branch:
   ```bash
   git checkout -b feature/my-new-style
   ```
2. Commit your changes with clear, descriptive commit messages.
3. Verify that all tests pass: `pytest -q`.
4. Push your branch and open a Pull Request against `master`.
