"""
Raspberry Pi MCP Server

Provides MCP tools for GPIO/LED control and DS18B20 temperature reading.
Transport: Streamable HTTP (default, port 8080) — accessible over local network.

Usage:
    python server.py                    # HTTP on 0.0.0.0:8080
    python server.py --transport sse    # SSE (legacy clients)
    python server.py --transport stdio  # subprocess / Claude Code
"""

import argparse
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from hardware.leds import led_blink, led_off, led_on, led_status
from hardware.temperature import list_sensors, read_temperature

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

_parser = argparse.ArgumentParser(description="Raspi MCP Server")
_parser.add_argument(
    "--transport",
    choices=["streamable-http", "sse", "stdio"],
    default="streamable-http",
)
_parser.add_argument("--port", type=int, default=8080)
_parser.add_argument("--host", default="0.0.0.0")
_args = _parser.parse_args()

mcp = FastMCP("raspi-mcp", host=_args.host, port=_args.port)


# ---------------------------------------------------------------------------
# Shared field definitions
# ---------------------------------------------------------------------------

# Known LED wiring on this Raspberry Pi (BCM pin → colour)
_LED_CONFIG: dict[int, str] = {
    17: "red",
    27: "yellow",
    22: "green",
}

_PIN_FIELD = Field(
    ...,
    ge=1,
    le=40,
    description=(
        "BCM GPIO pin number of the LED. "
        "Known LEDs on this Pi: 17=red, 27=yellow, 22=green. "
        "Example: 17"
    ),
)

_SENSOR_ID_FIELD = Field(
    ...,
    min_length=1,
    description=(
        "1-Wire device ID as returned by temperature_list_sensors. "
        "Known sensors on this Pi: '10-0008024b541d', '28-0000084e3138'. "
        "Example: '28-0000084e3138'"
    ),
)


# ---------------------------------------------------------------------------
# LED tools
# ---------------------------------------------------------------------------

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def gpio_list_leds() -> dict[str, Any]:
    """List all LEDs wired to this Raspberry Pi with their BCM pin number and colour.

    Call this first to discover which pin to use for a given LED colour.
    Returns a list of objects with 'pin' (int) and 'colour' (str).
    Example response: {"leds": [{"pin": 17, "colour": "red"}, ...]}
    """
    return {"leds": [{"pin": pin, "colour": colour} for pin, colour in _LED_CONFIG.items()]}


@mcp.tool(annotations=ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=True
))
def gpio_led_on(pin: int = _PIN_FIELD) -> dict[str, Any]:
    """Turn an LED on by BCM pin number.

    Use gpio_list_leds first to find the correct pin for a given colour.
    Returns the pin number and new state.
    Example: {"pin": 17, "state": "on"}
    """
    led_on(pin)
    return {"pin": pin, "state": "on"}


@mcp.tool(annotations=ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=True
))
def gpio_led_off(pin: int = _PIN_FIELD) -> dict[str, Any]:
    """Turn an LED off by BCM pin number.

    Use gpio_list_leds first to find the correct pin for a given colour.
    Returns the pin number and new state.
    Example: {"pin": 17, "state": "off"}
    """
    led_off(pin)
    return {"pin": pin, "state": "off"}


@mcp.tool(annotations=ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=False
))
def gpio_led_blink(
    pin: int = _PIN_FIELD,
    on_time: float = Field(0.5, gt=0.0, le=10.0, description="Seconds ON per cycle. Default: 0.5"),
    off_time: float = Field(  # noqa: E501
        0.5, gt=0.0, le=10.0, description="Seconds OFF per cycle. Default: 0.5"
    ),
    n: int = Field(3, ge=1, le=20, description="Number of blink cycles (1–20). Default: 3"),
) -> dict[str, Any]:
    """Blink an LED n times (blocking until finished).

    Use gpio_list_leds first to find the correct pin for a given colour.
    All timing parameters are optional and have sensible defaults.
    Returns the pin, number of cycles executed, and final state (always 'off').
    Example: {"pin": 27, "cycles": 3, "state": "off"}
    """
    led_blink(pin, on_time=on_time, off_time=off_time, n=n)
    return {"pin": pin, "cycles": n, "state": "off"}


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def gpio_led_status(pin: int = _PIN_FIELD) -> dict[str, Any]:
    """Return the current state of an LED pin ('on' or 'off').

    Use gpio_list_leds first to find the correct pin for a given colour.
    Example response: {"pin": 22, "state": "on"}
    """
    state = led_status(pin)
    return {"pin": pin, "state": state}


# ---------------------------------------------------------------------------
# Temperature tools
# ---------------------------------------------------------------------------

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def temperature_list_sensors() -> dict[str, Any]:
    """List all connected 1-Wire temperature sensors by their device IDs.

    Call this first to discover valid sensor_id values for temperature_read.
    Returns a list of sensor ID strings and the total count.
    Currently known sensors on this Pi: '10-0008024b541d', '28-0000084e3138'.
    Example response: {"sensors": ["10-0008024b541d", "28-0000084e3138"], "count": 2}
    """
    sensors = list_sensors()
    return {"sensors": sensors, "count": len(sensors)}


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def temperature_read(sensor_id: str = _SENSOR_ID_FIELD) -> dict[str, Any]:
    """Read the current temperature from a 1-Wire sensor in both Celsius and Fahrenheit.

    Use temperature_list_sensors first to get a valid sensor_id.
    Known sensors on this Pi: '10-0008024b541d', '28-0000084e3138'.
    Returns sensor_id, temperature_c (float), and temperature_f (float).
    Example response: {"sensor_id": "28-0000084e3138", "temperature_c": 21.5, "temperature_f": 70.7}
    """
    celsius = read_temperature(sensor_id)
    return {
        "sensor_id": sensor_id,
        "temperature_c": celsius,
        "temperature_f": round(celsius * 9 / 5 + 32, 2),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info(
        "Starting raspi-mcp (transport=%s, host=%s, port=%d)",
        _args.transport, _args.host, _args.port,
    )
    mcp.run(transport=_args.transport)  # type: ignore[arg-type]
