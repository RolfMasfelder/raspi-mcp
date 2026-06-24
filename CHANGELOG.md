# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] – 2026-06-24

### Added

- MCP server over Streamable HTTP (port 8080) with Bearer token authentication
- `gpio_led_on`, `gpio_led_off`, `gpio_led_blink`, `gpio_led_status`, `gpio_list_leds` tools for GPIO-connected LEDs via `gpiozero`
- `temperature_list_sensors`, `temperature_read` tools for DS18B20 1-Wire sensors via `/sys/bus/w1/devices/`
- Pydantic input validation with BCM pin range guard (1–40) on all tools
- MCP annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) on all tools
- `--transport` flag: `streamable-http` (default), `sse`, `stdio`
- `--port` and `--host` flags; `RASPI_MCP_HOST`, `RASPI_MCP_PORT`, `RASPI_MCP_LOG_LEVEL` environment variables
- systemd unit file for autostart on Raspberry Pi
- `gpiozero` MockFactory-based tests for LED tools (no hardware required)
- `tmp_path`-based tests for temperature tools (no hardware required)
- CI workflow (GitHub Actions): `ruff check .` + `pytest` on every push to `dev` and PR to `main`
- Dependabot configuration targeting `dev` branch with automated lockfile regeneration

[0.1.0]: https://github.com/RolfMasfelder/raspi-mcp/releases/tag/v0.1.0
