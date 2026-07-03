# Copilot Instructions – raspi-mcp

> **Language**: All responses and user-facing messages from Copilot must be in English. Commit messages must be in English as specified. German text in this document is for reference only and should not influence output language.

## Git Remotes

| Remote   | Zweck                 |
|----------|-----------------------|
| `origin` | Lokaler Mirror        |
| `github` | GitHub (öffentlich)   |

Push-Regeln:
1. If the user does not explicitly trigger a push → do nothing.
2. Never push to `main` under any circumstances (see Branch-Workflow). If the current branch is `main` and a push is triggered, refuse and instruct the user to switch to `dev` or a feature branch.
3. Step 1 – Determine target remotes: If the user explicitly requests a push to `github` (e.g., says "push to github" or "push to both remotes"), target both `origin` and `github`. Otherwise, target `origin` only.
4. Step 2 – Push to `origin`: Execute `git push origin`. On failure → stop, output the raw git error, do not retry, do not roll back the local commit.
5. Step 3 – Push to `github` (only if targeted in step 1): Execute `git push github`. On failure → output the raw git error for `github` only, do not retry, do not attempt to undo the `origin` push.

Commit-Format: `<prefix>: kurze Beschreibung auf Englisch` (eine Zeile, maximal 72 Zeichen). Erlaubte Prefixe: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`. If the change does not clearly match `feat`, `fix`, `refactor`, `docs`, or `test`, use `chore`.

## Branch-Workflow

| Branch | Zweck |
|--------|-------|
| `main` | Stabile Releases. Kein direkter Push erlaubt. Änderungen nur via PR von `dev`. Branch Protection auf GitHub erzwingt dies. |
| `dev`  | **Standard-Arbeitsbranch.** Hier werden Features entwickelt, Commits gemacht und PRs erstellt. |

- Neue Features und Fixes: von `dev` abzweigen, Änderungen auf Feature-Branch entwickeln, PR gegen `dev` erstellen, Merge via Squash.
- Release: PR von `dev` → `main` erstellen; CI muss grün sein.
- Niemals direkt auf `main` pushen — auch nicht per `git push --force`.
- If the user requests a commit or push while on the `main` branch, refuse to execute it. Inform the user that direct commits to `main` are not allowed and instruct them to switch to `dev` or a feature branch first.
- Dependabot-PRs zielen direkt auf `main` (siehe `dependabot.yml`), damit `dev` beim aktiven Entwickeln nicht laufend rebased/verändert wird. Dependency-Bumps auf `main` werden beim nächsten `dev` → `main`-Sync (in umgekehrter Richtung: `main` → `dev`) zurück nach `dev` gezogen.
- When creating a PR, use the GitHub CLI (`gh pr create`). Title must follow the commit-format convention. Body should summarize the changes. Before creating a PR from `dev` → `main`, confirm CI is green. Never create a PR targeting `main` from any branch other than `dev`.

## Projektüberblick

MCP-Server für einen Raspberry Pi. Bietet MCP-Tools zur Steuerung von GPIO-LEDs (via `gpiozero`) und zum Auslesen von DS18B20-Temperatursensoren (via Linux 1-Wire Kernel-Interface `/sys/bus/w1/devices/`).

Der Server wird von einem separaten System (`agentic_rag`, Django/Celery) über HTTP angesprochen. Die einzige Schnittstelle ist das MCP-Protokoll (JSON-RPC 2.0 / Streamable HTTP).

## Hardware

- **Raspberry Pi** (Model 3 oder neuer), hostname `pi1`, erreichbar via `ssh pi@pi1`
- **Python 3.13.5** (Raspberry Pi OS Bookworm)
- **LEDs** an GPIO-Pins (BCM-Nummerierung), angeschlossen über Breadboard
- **DS18B20** Temperatursensoren via 1-Wire (GPIO 4, `dtoverlay=w1-gpio` in `/boot/firmware/config.txt`)

## Stack

- **Python 3.13** (kein Docker — GPIO-Zugriff in Containern ist unnötig kompliziert)
- **`mcp>=1.0`** — FastMCP ist seit v1.0 direkt enthalten (kein `[fastmcp]`-Extra mehr)
- **`gpiozero`** — LED-Steuerung; auf dem Pi vorinstalliert (`python3-gpiozero`)
- **`pydantic>=2`** — Input-Validierung für alle Tool-Schemas
- **`pytest` + `pytest-asyncio`** — Tests
- **`ruff`** — Linting
- **`systemd`** — Autostart des Servers auf dem Pi

## Projektstruktur

```
raspi-mcp/
├── pyproject.toml          # ruff, pytest, dependencies
├── server.py               # FastMCP server, alle Tool-Definitionen
├── hardware/
│   ├── __init__.py
│   ├── leds.py             # gpiozero LED-Steuerung
│   └── temperature.py      # DS18B20 via /sys/bus/w1/devices/
├── tests/
│   ├── test_leds.py        # gpiozero MockFactory
│   └── test_temperature.py # tmp_path mock für w1_slave-Dateien
├── systemd/
│   └── raspi-mcp.service   # systemd Unit für Autostart
└── .github/
    └── copilot-instructions.md
```

## MCP-Tools (aktuelle Schnittstelle)

| Tool | Beschreibung | Seiteneffekt |
|---|---|---|
| `gpio_led_on(pin)` | LED einschalten | `destructiveHint=False`, `idempotentHint=True` |
| `gpio_led_off(pin)` | LED ausschalten | `destructiveHint=False`, `idempotentHint=True` |
| `gpio_led_blink(pin, on_time, off_time, n)` | LED n-mal blinken | `destructiveHint=False`, `idempotentHint=False` |
| `gpio_led_status(pin)` | Aktuellen LED-Zustand lesen | `readOnlyHint=True` |
| `temperature_list_sensors()` | Alle DS18B20-Sensoren auflisten | `readOnlyHint=True` |
| `temperature_read(sensor_id)` | Temperatur in °C lesen | `readOnlyHint=True` |

Pin-Validierung: BCM-Nummern 1–40 (Pydantic `Field(ge=1, le=40)`). Note: This range is a simplification; actual valid BCM GPIO numbers are a subset. The 1–40 range is intentionally used as a broad guard.

## Konventionen

- **Alle MCP-Tool-Inputs** als `pydantic.BaseModel` mit `Field`-Constraints definieren
- **MCP-Annotations** (`readOnlyHint`, `destructiveHint`, `idempotentHint`) auf jedem Tool setzen
- **gpiozero MockFactory** für LED-Tests: `Device.pin_factory = MockFactory()` vor dem Import von `hardware.leds`
- **1-Wire-Tests**: `W1_DEVICES_PATH` via `unittest.mock.patch` auf `tmp_path`-Verzeichnis umleiten
- **Kein root-Zugriff nötig**: `gpiozero` und 1-Wire funktionieren als normaler `pi`-User, sofern der User in der Gruppe `gpio` ist
- Linting: `ruff check .` vor jedem Commit; bei auto-fixbaren Issues niemals automatisch `--fix` ausführen, Nutzer informieren. If `ruff check .` fails to execute (non-zero exit for reasons other than lint violations, e.g., tool not found), do not proceed with the commit and show the error output to the user. If `ruff check .` reports auto-fixable issues, show the ruff output to the user and stop before executing `git commit`. Do not stage or commit any files. Inform the user they must run `ruff check . --fix` themselves or explicitly say "commit anyway" before proceeding.
- Tests: `pytest` — bei Exit-Code != 0 nicht committen. If pytest exits with a non-zero code, do not commit, and show the full pytest output to the user with a message that the commit was blocked due to failing tests.


