"""Tests for hardware.leds using gpiozero MockFactory."""

import pytest

# Skip entire module if gpiozero is not installed
pytest.importorskip("gpiozero")

from gpiozero import Device  # noqa: E402
from gpiozero.pins.mock import MockFactory  # noqa: E402

# Activate mock pin factory before importing the module under test
Device.pin_factory = MockFactory()

from hardware.leds import led_blink, led_off, led_on, led_status  # noqa: E402


@pytest.fixture(autouse=True)
def reset_leds():
    """Clear LED instance cache between tests."""
    import hardware.leds as leds_module
    leds_module._leds.clear()
    yield
    leds_module._leds.clear()


def test_led_on_sets_state():
    led_on(17)
    assert led_status(17) == "on"


def test_led_off_sets_state():
    led_on(17)
    led_off(17)
    assert led_status(17) == "off"


def test_led_status_default_off():
    assert led_status(18) == "off"


def test_led_blink_ends_off():
    led_blink(17, on_time=0.01, off_time=0.01, n=2)
    assert led_status(17) == "off"


def test_led_on_idempotent():
    led_on(17)
    led_on(17)  # second call must not raise
    assert led_status(17) == "on"
