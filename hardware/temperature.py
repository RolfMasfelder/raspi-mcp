"""
DS18B20 temperature sensor reading via Linux 1-Wire kernel interface.

Sensors appear under /sys/bus/w1/devices/ as directories named
28-XXXXXXXXXXXX. Each sensor has a w1_slave file with lines like:

    50 01 4b 46 7f ff 0c 10 1c : crc=1c YES
    50 01 4b 46 7f ff 0c 10 1c t=21250

The temperature in millidegrees Celsius is the value after "t=".

To enable 1-Wire on a Raspberry Pi, add to /boot/config.txt:
    dtoverlay=w1-gpio
and reboot.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

W1_DEVICES_PATH = Path("/sys/bus/w1/devices")


def list_sensors() -> list[str]:
    """Return IDs of all connected DS18B20 sensors (directories starting with '28-')."""
    if not W1_DEVICES_PATH.exists():
        logger.warning("1-Wire device path %s does not exist", W1_DEVICES_PATH)
        return []
    return [d.name for d in W1_DEVICES_PATH.iterdir() if d.name.startswith("28-")]


def read_temperature(sensor_id: str) -> float:
    """
    Read temperature in Celsius from a DS18B20 sensor.

    Args:
        sensor_id: Sensor directory name, e.g. "28-01234567"

    Returns:
        Temperature as float in degrees Celsius.

    Raises:
        FileNotFoundError: Sensor directory or w1_slave file does not exist.
        ValueError: CRC check failed or temperature line could not be parsed.
    """
    sensor_path = W1_DEVICES_PATH / sensor_id / "w1_slave"
    if not sensor_path.exists():
        raise FileNotFoundError(f"Sensor not found: {sensor_path}")

    raw = sensor_path.read_text(encoding="ascii")
    lines = raw.strip().splitlines()

    if len(lines) < 2 or "YES" not in lines[0]:
        raise ValueError(f"CRC check failed for sensor {sensor_id}: {raw!r}")

    temp_part = lines[1].split("t=")
    if len(temp_part) != 2:
        raise ValueError(f"Cannot parse temperature from: {lines[1]!r}")

    millidegrees = int(temp_part[1].strip())
    return round(millidegrees / 1000.0, 3)
