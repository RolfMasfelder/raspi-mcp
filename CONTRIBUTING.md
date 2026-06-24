# Contributing to raspi-mcp

## Development environment (no Raspberry Pi needed)

All tests run on a standard Linux/macOS/Windows machine — no GPIO hardware required.

```bash
git clone https://github.com/RolfMasfelder/raspi-mcp.git
cd raspi-mcp
pip install -r requirements-dev.txt
pytest        # LED tests use gpiozero MockFactory; temperature tests use tmp_path
```

The venv directory is `venv/` (listed in `.gitignore`).

## Branch workflow

| Branch | Purpose |
|--------|---------|
| `main` | Stable releases — no direct push |
| `dev`  | Default working branch |

1. Branch off `dev`: `git checkout -b feat/my-feature dev`
2. Develop and commit on your feature branch.
3. Open a PR against `dev`; merge via Squash.
4. Releases are created by PR `dev → main` (CI must be green).

## Commit format

```
<prefix>: short description in English   (max 72 characters)
```

Allowed prefixes: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.

## Before committing

```bash
ruff check .   # lint — fix reported issues before committing; never run --fix blindly
pytest         # all tests must pass (exit code 0)
```

## Pull request

Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md) — it includes a checklist
for lint, tests, and change description.
