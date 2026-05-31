"""Tests for hardware.temperature using a tmp_path mock of /sys/bus/w1/devices/."""

import pytest
from pathlib import Path
from unittest.mock import patch

from hardware.temperature import list_sensors, read_temperature


SENSOR_ID = "28-abcd12345678"
SENSOR_ID_DS18S20 = "10-0008024b541d"

VALID_W1_SLAVE = (
    "50 01 4b 46 7f ff 0c 10 1c : crc=1c YES\n"
    "50 01 4b 46 7f ff 0c 10 1c t=21250\n"
)

BAD_CRC_W1_SLAVE = (
    "50 01 4b 46 7f ff 0c 10 1c : crc=1c NO\n"
    "50 01 4b 46 7f ff 0c 10 1c t=21250\n"
)


@pytest.fixture()
def w1_root(tmp_path: Path):
    """Create a fake /sys/bus/w1/devices/ tree under tmp_path."""
    devices = tmp_path / "devices"
    devices.mkdir()
    sensor_dir = devices / SENSOR_ID
    sensor_dir.mkdir()
    return devices


def test_list_sensors_returns_ids(w1_root: Path):
    with patch("hardware.temperature.W1_DEVICES_PATH", w1_root):
        result = list_sensors()
    assert result == [SENSOR_ID]


def test_list_sensors_includes_ds18s20(w1_root: Path):
    (w1_root / SENSOR_ID_DS18S20).mkdir()
    with patch("hardware.temperature.W1_DEVICES_PATH", w1_root):
        result = list_sensors()
    assert set(result) == {SENSOR_ID, SENSOR_ID_DS18S20}


def test_list_sensors_empty_when_path_missing(tmp_path: Path):
    missing = tmp_path / "nonexistent"
    with patch("hardware.temperature.W1_DEVICES_PATH", missing):
        result = list_sensors()
    assert result == []


def test_read_temperature_valid(w1_root: Path):
    (w1_root / SENSOR_ID / "w1_slave").write_text(VALID_W1_SLAVE)
    with patch("hardware.temperature.W1_DEVICES_PATH", w1_root):
        temp = read_temperature(SENSOR_ID)
    assert temp == pytest.approx(21.25)


def test_read_temperature_crc_failure(w1_root: Path):
    (w1_root / SENSOR_ID / "w1_slave").write_text(BAD_CRC_W1_SLAVE)
    with patch("hardware.temperature.W1_DEVICES_PATH", w1_root):
        with pytest.raises(ValueError, match="CRC check failed"):
            read_temperature(SENSOR_ID)


def test_read_temperature_sensor_not_found(w1_root: Path):
    with patch("hardware.temperature.W1_DEVICES_PATH", w1_root):
        with pytest.raises(FileNotFoundError):
            read_temperature("28-doesnotexist")
