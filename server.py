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

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from hardware.leds import led_on, led_off, led_blink, led_status
from hardware.temperature import read_temperature, list_sensors

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP("raspi-mcp")


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------

class LedPinInput(BaseModel):
    pin: int = Field(..., ge=1, le=40, description="GPIO BCM pin number (1–40)")


class LedBlinkInput(BaseModel):
    pin: int = Field(..., ge=1, le=40, description="GPIO BCM pin number (1–40)")
    on_time: float = Field(0.5, gt=0.0, le=10.0, description="Seconds LED stays on per cycle")
    off_time: float = Field(0.5, gt=0.0, le=10.0, description="Seconds LED stays off per cycle")
    n: int = Field(3, ge=1, le=20, description="Number of blink cycles")


class SensorIdInput(BaseModel):
    sensor_id: str = Field(..., min_length=1, description="1-Wire sensor ID (e.g. 28-01234567)")


# ---------------------------------------------------------------------------
# LED tools
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
def gpio_led_on(input: LedPinInput) -> dict:
    """Turn an LED on. The LED must be connected to the specified BCM GPIO pin."""
    led_on(input.pin)
    return {"pin": input.pin, "state": "on"}


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
def gpio_led_off(input: LedPinInput) -> dict:
    """Turn an LED off."""
    led_off(input.pin)
    return {"pin": input.pin, "state": "off"}


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    }
)
def gpio_led_blink(input: LedBlinkInput) -> dict:
    """Blink an LED n times with configurable on/off timing."""
    led_blink(input.pin, on_time=input.on_time, off_time=input.off_time, n=input.n)
    return {"pin": input.pin, "cycles": input.n, "state": "off"}


@mcp.tool(annotations={"readOnlyHint": True})
def gpio_led_status(input: LedPinInput) -> dict:
    """Return the current state (on/off) of an LED pin."""
    state = led_status(input.pin)
    return {"pin": input.pin, "state": state}


# ---------------------------------------------------------------------------
# Temperature tools
# ---------------------------------------------------------------------------

@mcp.tool(annotations={"readOnlyHint": True})
def temperature_list_sensors() -> dict:
    """List all connected DS18B20 1-Wire temperature sensors by their device IDs."""
    sensors = list_sensors()
    return {"sensors": sensors, "count": len(sensors)}


@mcp.tool(annotations={"readOnlyHint": True})
def temperature_read(input: SensorIdInput) -> dict:
    """Read the current temperature in Celsius from a DS18B20 sensor."""
    celsius = read_temperature(input.sensor_id)
    return {"sensor_id": input.sensor_id, "temperature_c": celsius, "temperature_f": round(celsius * 9 / 5 + 32, 2)}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raspi MCP Server")
    parser.add_argument(
        "--transport",
        choices=["streamable-http", "sse", "stdio"],
        default="streamable-http",
    )
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    logger.info("Starting raspi-mcp (transport=%s, host=%s, port=%d)", args.transport, args.host, args.port)
    mcp.run(transport=args.transport, host=args.host, port=args.port)  # type: ignore[arg-type]
