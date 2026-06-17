"""
LED control via gpiozero.

Uses gpiozero's MockFactory automatically when gpiozero detects no real GPIO
hardware (e.g. during tests). For explicit test overrides, set
``Device.pin_factory = MockFactory()`` before importing this module.
"""

import logging
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from gpiozero import LED

logger = logging.getLogger(__name__)

# gpiozero is optional when running on non-Pi hardware (dev/test machines).
# We import it lazily so the module can be loaded without it installed.
try:
    from gpiozero import LED  # type: ignore[import]

    _GPIOZERO_AVAILABLE = True
except ImportError:
    _GPIOZERO_AVAILABLE = False
    logger.warning("gpiozero not available — LED operations will be no-ops")

_leds: dict[int, "LED"] = {}  # pin -> LED instance


def _get_led(pin: int) -> object:
    """Return a cached LED instance for the given BCM pin."""
    if pin not in _leds:
        if not _GPIOZERO_AVAILABLE:
            raise RuntimeError("gpiozero is not installed; cannot control LEDs")
        _leds[pin] = LED(pin, active_high=False)
    return _leds[pin]


def led_on(pin: int) -> None:
    """Turn the LED on the given BCM pin on."""
    led = _get_led(pin)
    led.on()  # type: ignore[union-attr]
    logger.debug("LED pin %d → ON", pin)


def led_off(pin: int) -> None:
    """Turn the LED on the given BCM pin off."""
    led = _get_led(pin)
    led.off()  # type: ignore[union-attr]
    logger.debug("LED pin %d → OFF", pin)


def led_blink(pin: int, on_time: float = 0.5, off_time: float = 0.5, n: int = 3) -> None:
    """Blink the LED n times (blocking)."""
    led = _get_led(pin)
    led.blink(on_time=on_time, off_time=off_time, n=n, background=False)  # type: ignore[union-attr]
    logger.debug("LED pin %d blinked %d times", pin, n)


def led_status(pin: int) -> Literal["on", "off"]:
    """Return 'on' or 'off' for the current LED state."""
    led = _get_led(pin)
    return "on" if led.is_lit else "off"  # type: ignore[union-attr]
