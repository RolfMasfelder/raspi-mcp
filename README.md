# raspi-mcp

MCP server for Raspberry Pi GPIO/LED control and DS18B20 temperature sensors.

## Requirements

- Raspberry Pi with Raspberry Pi OS Bookworm (Python 3.11+)
- `gpiozero` (pre-installed on Raspi OS)
- DS18B20 sensor connected via 1-Wire (GPIO 4 by default)

## Setup on Raspberry Pi

### 1 — Enable 1-Wire

Add to `/boot/firmware/config.txt` (Bookworm) or `/boot/config.txt` (older):

```txt
dtoverlay=w1-gpio
```

Then reboot.

### 2 — Install system dependencies

`gpiozero` is installed system-wide to keep GPIO bindings intact:

```bash
sudo apt install -y python3-gpiozero python3-venv
```

### 3 — Clone the repository

The repository has a git remote `origin` configured on the Pi.
On first setup, clone it:

```bash
cd ~
git clone <origin-url> raspi-mcp
cd raspi-mcp
```

On subsequent updates, pull the latest changes:

```bash
cd ~/raspi-mcp
git pull
```

### 4 — Create venv and install Python dependencies

```bash
cd ~/raspi-mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> `requirements.txt` is generated from `pyproject.toml` (see [Dependency management](#dependency-management) below).
> `gpiozero` is intentionally excluded — it is managed by `apt` (see step 2).

### 5 — Verify the installation

```bash
source venv/bin/activate
python server.py --help
```

## Run

```bash
# HTTP on port 8080 (default — accessible from local network)
python server.py

# SSE transport (legacy clients)
python server.py --transport sse

# stdio (subprocess / Claude Code)
python server.py --transport stdio
```

## Hardware wiring

### LEDs

| BCM pin | Colour |
|---------|--------|
| 17      | red    |
| 27      | yellow |
| 22      | green  |

### DS18B20 temperature sensors

| Sensor ID        | Interface |
|------------------|-----------|
| `10-0008024b541d` | 1-Wire    |
| `28-0000084e3138` | 1-Wire    |

1-Wire data line: GPIO 4 (requires `dtoverlay=w1-gpio` in `/boot/firmware/config.txt`).

## Tools

| Tool | Description |
|---|---|
| `gpio_led_on` | Turn LED on (by BCM pin) |
| `gpio_led_off` | Turn LED off |
| `gpio_led_blink` | Blink LED n times |
| `gpio_led_status` | Read current LED state |
| `temperature_list_sensors` | List connected DS18B20 sensors |
| `temperature_read` | Read temperature in °C from a sensor |

## Connect from MCP client

```json
{
  "raspi": {
    "type": "streamable_http",
    "url": "http://<raspberry-pi-ip>:8080/mcp"
  }
}
```

## Tests (dev machine)

```bash
pip install -r requirements-dev.txt
pytest
```

The temperature tests mock `/sys/bus/w1/devices/` via `tmp_path`.
The LED tests use `gpiozero`'s built-in `MockFactory` — no hardware needed.

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

Then commit all three files together.

## systemd autostart

```bash
sudo cp systemd/raspi-mcp.service /etc/systemd/system/
sudo systemctl enable --now raspi-mcp
```

## Note on Python version

Raspberry Pi OS Buster ships Python 3.7 — too old for the MCP SDK (requires ≥3.11).
Upgrade to Bookworm first (`sudo apt full-upgrade` or fresh image).
