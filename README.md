# raspi-mcp

MCP server for Raspberry Pi GPIO/LED control and DS18B20 temperature sensors.

## Requirements

- Raspberry Pi with Raspberry Pi OS Bookworm (Python 3.11+)
- `gpiozero` (pre-installed on Raspi OS)
- DS18B20 sensor connected via 1-Wire (GPIO 4 by default)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "mcp[fastmcp]>=1.0" pydantic>=2
```

Enable 1-Wire in `/boot/firmware/config.txt` (Bookworm) or `/boot/config.txt` (older):
```
dtoverlay=w1-gpio
```
Then reboot.

## Run

```bash
# HTTP on port 8080 (default — accessible from local network)
python server.py

# SSE transport (legacy clients)
python server.py --transport sse

# stdio (subprocess / Claude Code)
python server.py --transport stdio
```

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
pip install -e ".[dev]"
pytest
```

The temperature tests mock `/sys/bus/w1/devices/` via `tmp_path`.
The LED tests use `gpiozero`'s built-in `MockFactory` — no hardware needed.

## systemd autostart

```bash
sudo cp systemd/raspi-mcp.service /etc/systemd/system/
sudo systemctl enable --now raspi-mcp
```

## Note on Python version

Raspberry Pi OS Buster ships Python 3.7 — too old for the MCP SDK (requires ≥3.11).
Upgrade to Bookworm first (`sudo apt full-upgrade` or fresh image).
