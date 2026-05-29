# Copilot Instructions – raspi-mcp

## Git Remotes

| Remote   | Zweck                                      |
|----------|--------------------------------------------|
| `origin` | Bei jedem vom Nutzer ausgelösten Push-Befehl ohne explizite Remote-Angabe immer nach `origin` pushen. Niemals automatisch ohne expliziten Nutzerbefehl pushen. Bei Push-Fehler keinerlei Retry ausführen, keinen lokalen Commit zurücknehmen, und genau eine Fehlermeldung mit dem Git-Output an den Nutzer geben. |
| `github` | Nur pushen, wenn der Nutzer das Wort "github" oder "GitHub" explizit im Push-Befehl nennt. Dann sowohl zu `origin` als auch zu `github` pushen (`origin` zuerst). |

Commit-Format: `<prefix>: kurze Beschreibung auf Englisch` (eine Zeile, maximal 72 Zeichen). Erlaubte Prefixe: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`. Bei Unsicherheit `chore` verwenden.

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

Pin-Validierung: BCM-Nummern 1–40 (Pydantic `Field(ge=1, le=40)`).

## Konventionen

- **Alle MCP-Tool-Inputs** als `pydantic.BaseModel` mit `Field`-Constraints definieren
- **MCP-Annotations** (`readOnlyHint`, `destructiveHint`, `idempotentHint`) auf jedem Tool setzen
- **gpiozero MockFactory** für LED-Tests: `Device.pin_factory = MockFactory()` vor dem Import von `hardware.leds`
- **1-Wire-Tests**: `W1_DEVICES_PATH` via `unittest.mock.patch` auf `tmp_path`-Verzeichnis umleiten
- **Kein root-Zugriff nötig**: `gpiozero` und 1-Wire funktionieren als normaler `pi`-User, sofern der User in der Gruppe `gpio` ist
- Linting: `ruff check .` vor jedem Commit; bei auto-fixbaren Issues niemals automatisch `--fix` ausführen, Nutzer informieren
- Tests: `pytest` — bei Exit-Code != 0 nicht committen

## Deployment auf dem Pi

```bash
# Einmalig auf dem Pi:
sudo apt install -y python3-gpiozero python3-venv
cd ~/raspi-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install "mcp[fastmcp]>=1.0" "pydantic>=2"

# Server starten (Entwicklung):
python server.py   # HTTP auf 0.0.0.0:8080

# Autostart via systemd:
sudo cp systemd/raspi-mcp.service /etc/systemd/system/
sudo systemctl enable --now raspi-mcp
```

## Integration mit agentic_rag

Der `agentic_rag`-Stack (Django/Celery) verbindet sich via:
```
http://pi1:8080/mcp
```
Konfiguriert über `.env`-Variable `RASPI_MCP_URL`. Die beiden Repos sind vollständig unabhängig — keine Submodules, keine gemeinsamen Python-Pakete.

## Entwicklung ohne Hardware (Dev-Maschine)

```bash
pip install "mcp>=1.0" "pydantic>=2" gpiozero pytest pytest-asyncio ruff
pytest   # LED-Tests via MockFactory, Temperaturtests via tmp_path
python server.py   # Server läuft, GPIO-Calls gehen durch MockFactory
```
