"""Tests for server.py: _BearerTokenMiddleware and MCP tool wrappers."""

import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

# Prevent argparse from consuming pytest command-line arguments.
sys.argv = ["server.py"]

# gpiozero mock must be active before server.py imports hardware.leds.
pytest.importorskip("gpiozero")
from gpiozero import Device  # noqa: E402
from gpiozero.pins.mock import MockFactory  # noqa: E402

Device.pin_factory = MockFactory()

from server import (  # noqa: E402
    _BearerTokenMiddleware,
    gpio_led_blink,
    gpio_led_off,
    gpio_led_on,
    gpio_led_status,
    gpio_list_leds,
    temperature_list_sensors,
    temperature_read,
)

_TOKEN = "test-secret-token"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_middleware_app(api_key: str):
    """Wrap a trivial ASGI app in _BearerTokenMiddleware."""
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    app = Starlette(routes=[Route("/", lambda r: PlainTextResponse("ok"))])
    app.add_middleware(_BearerTokenMiddleware, api_key=api_key)
    return app


async def _get(app, path: str = "/", headers: dict | None = None) -> httpx.Response:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.get(path, headers=headers or {})


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_led_cache():
    import hardware.leds as leds_module
    leds_module._leds.clear()
    yield
    leds_module._leds.clear()


# ---------------------------------------------------------------------------
# _BearerTokenMiddleware
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_middleware_valid_token_passes():
    app = _make_middleware_app(_TOKEN)
    resp = await _get(app, headers={"Authorization": f"Bearer {_TOKEN}"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_middleware_wrong_token_returns_401():
    app = _make_middleware_app(_TOKEN)
    resp = await _get(app, headers={"Authorization": "Bearer wrong-token"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_middleware_no_header_returns_401():
    app = _make_middleware_app(_TOKEN)
    resp = await _get(app)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_middleware_malformed_scheme_returns_401():
    app = _make_middleware_app(_TOKEN)
    resp = await _get(app, headers={"Authorization": f"Token {_TOKEN}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_middleware_empty_token_returns_401():
    app = _make_middleware_app(_TOKEN)
    resp = await _get(app, headers={"Authorization": "Bearer "})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_middleware_401_body_contains_error_key():
    app = _make_middleware_app(_TOKEN)
    resp = await _get(app)
    assert resp.json()["error"] == "Unauthorized"


# ---------------------------------------------------------------------------
# gpio_list_leds
# ---------------------------------------------------------------------------

def test_gpio_list_leds_returns_leds_key():
    result = gpio_list_leds()
    assert "leds" in result


def test_gpio_list_leds_contains_known_pins():
    leds = {item["pin"]: item["colour"] for item in gpio_list_leds()["leds"]}
    assert leds[17] == "red"
    assert leds[27] == "yellow"
    assert leds[22] == "green"


# ---------------------------------------------------------------------------
# gpio_led_on / gpio_led_off / gpio_led_status
# ---------------------------------------------------------------------------

def test_gpio_led_on_returns_state_on():
    result = gpio_led_on(17)
    assert result == {"pin": 17, "state": "on"}


def test_gpio_led_off_returns_state_off():
    gpio_led_on(17)
    result = gpio_led_off(17)
    assert result == {"pin": 17, "state": "off"}


def test_gpio_led_status_reflects_on():
    gpio_led_on(22)
    result = gpio_led_status(22)
    assert result == {"pin": 22, "state": "on"}


def test_gpio_led_status_reflects_off():
    gpio_led_on(22)
    gpio_led_off(22)
    result = gpio_led_status(22)
    assert result == {"pin": 22, "state": "off"}


# ---------------------------------------------------------------------------
# gpio_led_blink
# ---------------------------------------------------------------------------

def test_gpio_led_blink_returns_cycles_and_off():
    result = gpio_led_blink(17, on_time=0.01, off_time=0.01, n=2)
    assert result == {"pin": 17, "cycles": 2, "state": "off"}


# ---------------------------------------------------------------------------
# temperature_list_sensors
# ---------------------------------------------------------------------------

def test_temperature_list_sensors_count_matches(tmp_path: Path):
    devices = tmp_path / "devices"
    devices.mkdir()
    (devices / "28-abcd12345678").mkdir()
    (devices / "28-deadbeef0001").mkdir()
    with patch("hardware.temperature.W1_DEVICES_PATH", devices):
        result = temperature_list_sensors()
    assert result["count"] == 2
    assert len(result["sensors"]) == 2


def test_temperature_list_sensors_empty_when_no_path(tmp_path: Path):
    with patch("hardware.temperature.W1_DEVICES_PATH", tmp_path / "nonexistent"):
        result = temperature_list_sensors()
    assert result == {"sensors": [], "count": 0}


# ---------------------------------------------------------------------------
# temperature_read
# ---------------------------------------------------------------------------

_W1_SLAVE = "50 01 4b 46 7f ff 0c 10 1c : crc=1c YES\n50 01 4b 46 7f ff 0c 10 1c t=21250\n"
_SENSOR = "28-abcd12345678"


@pytest.fixture()
def w1_root(tmp_path: Path):
    devices = tmp_path / "devices"
    devices.mkdir()
    sensor_dir = devices / _SENSOR
    sensor_dir.mkdir()
    (sensor_dir / "w1_slave").write_text(_W1_SLAVE)
    return devices


def test_temperature_read_celsius(w1_root: Path):
    with patch("hardware.temperature.W1_DEVICES_PATH", w1_root):
        result = temperature_read(_SENSOR)
    assert result["temperature_c"] == pytest.approx(21.25)


def test_temperature_read_fahrenheit_conversion(w1_root: Path):
    with patch("hardware.temperature.W1_DEVICES_PATH", w1_root):
        result = temperature_read(_SENSOR)
    expected_f = round(21.25 * 9 / 5 + 32, 2)
    assert result["temperature_f"] == pytest.approx(expected_f)


def test_temperature_read_returns_sensor_id(w1_root: Path):
    with patch("hardware.temperature.W1_DEVICES_PATH", w1_root):
        result = temperature_read(_SENSOR)
    assert result["sensor_id"] == _SENSOR
