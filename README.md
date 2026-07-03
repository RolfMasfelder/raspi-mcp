# raspi-mcp

[![CI](https://github.com/RolfMasfelder/raspi-mcp/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/RolfMasfelder/raspi-mcp/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

MCP server for Raspberry Pi GPIO/LED control and DS18B20 temperature sensors.

Exposes GPIO-connected LEDs and DS18B20 1-Wire temperature sensors as
[MCP tools](https://modelcontextprotocol.io/) over HTTP (Streamable HTTP transport).
Authentication is enforced via a Bearer token on all HTTP transports.

## Quick Start (dev machine, no hardware)

```bash
git clone https://github.com/RolfMasfelder/raspi-mcp.git
cd raspi-mcp
pip install -r requirements-dev.txt
pytest                               # 29 tests — no hardware needed
python server.py --transport stdio   # stdio mode, no token required
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor workflow.

---

## Hardware wiring

### LEDs

| BCM pin | Colour |
|---------|--------|
| 17      | red    |
| 27      | yellow |
| 22      | green  |

```
3.3V/5V  ──────────────────────────── (not used for LED)
GND      ───────────────────────────┬─
                                    │
BCM 17  ───── 220 Ω ──[LED red]─────┤
BCM 27  ───── 220 Ω ──[LED yellow]──┤
BCM 22  ───── 220 Ω ──[LED green]───┘  (cathodes → GND)
```

### DS18B20 temperature sensors

| Sensor ID         | Interface |
|-------------------|-----------|
| `10-0008024b541d` | 1-Wire    |
| `28-0000084e3138` | 1-Wire    |

1-Wire data line: GPIO 4 (requires `dtoverlay=w1-gpio` in `/boot/firmware/config.txt`).

```
Pi 3.3V ──── 4.7 kΩ ──┬── DS18B20 VDD (pin 3)
Pi BCM4 ───────────────┤── DS18B20 DATA (pin 2)
Pi GND  ───────────────┘── DS18B20 GND (pin 1)
```

Both sensors share the same data line (1-Wire supports multiple devices in parallel).

---

## Installation

Three scenarios are supported. Choose the one that fits your use case:

| Scenario | Hardware needed | Auth required | Autostart |
|---|---|---|---|
| [A — Raspberry Pi (production)](#scenario-a--raspberry-pi-production) | yes | yes | systemd |
| [B — Development machine (no Pi)](#scenario-b--development-machine-no-pi) | no | no (stdio) | — |
| [C — Raspberry Pi (development)](#scenario-c--raspberry-pi-development) | yes | yes | manual |

---

### Scenario A — Raspberry Pi (production)

Full deployment with systemd autostart and Bearer token authentication.
The server listens on `0.0.0.0:8080` and is reachable from the local network.

#### A1 — Enable 1-Wire

Add to `/boot/firmware/config.txt` (Bookworm) or `/boot/config.txt` (older):

```txt
dtoverlay=w1-gpio
```

Then reboot.

#### A2 — Install system dependencies

`gpiozero` is installed system-wide to keep GPIO bindings intact:

```bash
sudo apt install -y python3-gpiozero python3-venv
```

#### A3 — Clone the repository

```bash
cd ~
git clone https://github.com/RolfMasfelder/raspi-mcp.git raspi-mcp
cd raspi-mcp
```

On subsequent updates:

```bash
cd ~/raspi-mcp
git pull
```

#### A4 — Create venv and install Python dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> `gpiozero` is intentionally excluded from `requirements.txt` — it is managed by `apt` (step A2).

#### A5 — Configure the Bearer token

The server requires the environment variable `RASPI_MCP_API_KEY` to be set.
It is read from `/etc/raspi-mcp.env` by systemd at startup.

Generate a token and write the file (do this once):

```bash
echo "RASPI_MCP_API_KEY=$(openssl rand -hex 32)" | sudo tee /etc/raspi-mcp.env
sudo chmod 600 /etc/raspi-mcp.env   # root-readable only
```

The same token must be configured on every client that connects to the server
(see [Connect from MCP client](#connect-from-mcp-client) below).

#### A6 — Install and start the systemd service

```bash
sudo cp systemd/raspi-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now raspi-mcp
```

Verify:

```bash
sudo systemctl status raspi-mcp
```

#### A7 — Verify

```bash
# Read the token from the env file
TOKEN=$(sudo grep RASPI_MCP_API_KEY /etc/raspi-mcp.env | cut -d= -f2)

# Health check (should return HTTP 200 with MCP endpoint info)
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8080/mcp
```

---

### Scenario B — Development machine (no Pi)

Run tests and the server locally without any Raspberry Pi hardware.
GPIO calls go through `gpiozero`'s `MockFactory`; the 1-Wire filesystem is
replaced by a `tmp_path` mock.

No Bearer token is required when using the `stdio` transport (the default for
local MCP clients such as Claude Desktop or VS Code Copilot).

#### B1 — Install dependencies

```bash
pip install -r requirements-dev.txt
```

> This installs runtime dependencies plus dev tools (`pytest`, `ruff`, `pip-tools`).
> `gpiozero` is included here (unlike on the Pi, where it is managed by `apt`).

#### B2 — Run the tests

```bash
pytest
```

All tests run without hardware. LED tests use `gpiozero`'s built-in `MockFactory`;
temperature tests mock `/sys/bus/w1/devices/` via `tmp_path`.

#### B3 — Run the server locally (stdio, no auth)

The `stdio` transport is designed for subprocess-based MCP clients and does not
require a Bearer token:

```bash
python server.py --transport stdio
```

Configure your MCP client (e.g. Claude Desktop, `mcp.json`):

```json
{
  "raspi": {
    "type": "stdio",
    "command": "python",
    "args": ["/path/to/raspi-mcp/server.py", "--transport", "stdio"]
  }
}
```

#### B4 — Run the server locally (HTTP, with auth)

Copy `.env.example` to `.env`, fill in a generated token, then source the file:

```bash
cp .env.example .env
# Edit .env: set RASPI_MCP_API_KEY=$(openssl rand -hex 32)
source .env
python server.py   # HTTP on 0.0.0.0:8080
```

---

### Scenario C — Raspberry Pi (development)

Develop directly on the Pi without the systemd service running.
Useful when iterating on server code with real hardware attached.

Follow steps A1 through A4 first (1-Wire, system deps, clone, venv).

#### C1 — Configure the server for manual runs

Instead of `/etc/raspi-mcp.env` (used by systemd), use a local `.env` file.
It is already listed in `.gitignore` and will never be committed.

```bash
cp .env.example .env
# Edit .env: set RASPI_MCP_API_KEY to a generated token
#   openssl rand -hex 32
# Optionally adjust RASPI_MCP_HOST, RASPI_MCP_PORT, RASPI_MCP_LOG_LEVEL.
source .env
```

All variables in `.env.example` are documented with comments.

If the production service (`raspi-mcp.service`) is already running, stop it first
to free port 8080:

```bash
sudo systemctl stop raspi-mcp
```

#### C2 — Start the server manually

```bash
source venv/bin/activate
python server.py   # HTTP on 0.0.0.0:8080, auth enabled
```

Stop with `Ctrl-C`. Restart the production service afterwards if needed:

```bash
sudo systemctl start raspi-mcp
```

#### C3 — Lint and test before committing

```bash
pip install -r requirements-dev.txt   # includes ruff, pytest
ruff check .
pytest
```

---

## Tools

| Tool | Description |
|---|---|
| `gpio_led_on` | Turn LED on (by BCM pin) |
| `gpio_led_off` | Turn LED off |
| `gpio_led_blink` | Blink LED n times |
| `gpio_led_status` | Read current LED state |
| `gpio_list_leds` | List all configured LED pins |
| `temperature_list_sensors` | List connected DS18B20 sensors |
| `temperature_read` | Read temperature in °C (and °F) from a sensor |

Pin numbers use BCM numbering. Valid range: 1–40.

---

## Connect from MCP client

### HTTP transport (production / Scenario A and C)

Every HTTP request must include an `Authorization` header with the Bearer token
configured in [step A5](#a5--configure-the-bearer-token):

Beispiel für VS-Code ~/.config/Code/User/mcp.json
```json
{
  "servers": {
    "github": {
              ...
    },
    
    "raspi": {
      "type": "streamable_http",
      "url": "http://pi1:8080/mcp",
      "headers": {
        "Authorization": "Bearer <your-token>"
      }
    }         
  }
} 
```

Beispiel für LM Studio
```json
{
  "mcpServers": {
    "raspi-mcp": {
      "type": "streamable_http",
      "url": "http://pi1:8080/mcp",
      "headers": {
        "Authorization": "Bearer <your-token>"
      }
    }
  }
}
```

Replace `pi1` with your Pi's hostname or IP address.
Replace `<your-token>` with the value from `/etc/raspi-mcp.env`.

> For the `agentic_rag` Django/Celery stack: set `RASPI_MCP_URL=http://pi1:8080/mcp`
> and `RASPI_MCP_API_KEY=<your-token>` in the `.env` file of that project.

### stdio transport (local dev / Scenario B)

No `Authorization` header is needed. See [Scenario B3](#b3--run-the-server-locally-stdio-no-auth).

---

## Dependency management

`pyproject.toml` is the single source of truth for all dependencies.
`requirements.txt` (runtime) and `requirements-dev.txt` (runtime + dev tools) are
generated with [pip-compile](https://pip-tools.readthedocs.io/) and must **not** be
edited by hand.

After changing `pyproject.toml`, regenerate both files:

```bash
pip-compile pyproject.toml --output-file requirements.txt --no-emit-options
pip-compile pyproject.toml --extra dev --output-file requirements-dev.txt --no-emit-options
```

Then commit `pyproject.toml`, `requirements.txt`, and `requirements-dev.txt` together.

---

## Logs on Raspberry Pi

```bash
# All logs since last boot
journalctl -u raspi-mcp.service -b

# Follow live
journalctl -u raspi-mcp.service -f

# With precise timestamps
journalctl -u raspi-mcp.service -b -o short-precise
```

---

## Note on Python version

Raspberry Pi OS Buster ships Python 3.7 — too old for the MCP SDK (requires ≥3.11).
Use Bookworm or newer (`sudo apt full-upgrade` or a fresh image).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).