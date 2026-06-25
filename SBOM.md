# Software Bill of Materials (SBOM) – raspi-mcp

**Generated:** 25. June 2026
**Format:** CycloneDX 1.6
**Generation Method:** Automated (scripts/generate_sbom.py)

## Project Overview

**raspi-mcp** – MCP server for Raspberry Pi GPIO/LED control and DS18B20 temperature sensors.

- **Repository:** https://github.com/RolfMasfelder/raspi-mcp
- **Version:** 0.1.0
- **License:** MIT

## Runtime Environment

- **Python:** 3.13
- **OS:** Raspberry Pi OS Bookworm (Linux, arm64)
- **Hardware:** Raspberry Pi 3+
- **Deployment:** systemd service (no Docker)

## Direct Dependencies

| Component | Version | License | Purpose |
|-----------|---------|---------|---------|
| mcp | 1.28.0 | MIT | MCP protocol server (FastMCP) |
| pydantic | 2.13.4 | MIT | Input validation and schema definition |

## Transitive Dependencies

### ASGI Server Stack

| Component | Version | License | Purpose |
|-----------|---------|---------|---------|
| starlette | 1.3.1 | BSD-3-Clause | Lightweight ASGI framework |
| uvicorn | 0.49.0 | BSD-3-Clause | ASGI server |
| anyio | 4.14.0 | MIT | Async I/O abstraction layer |
| h11 | 0.16.0 | MIT | HTTP/1.1 implementation |
| sse-starlette | 3.4.5 | MIT | Server-Sent Events for Starlette |
| python-multipart | 0.0.32 | Apache-2.0 | Multipart form data parser |

### HTTP Client Stack

| Component | Version | License | Purpose |
|-----------|---------|---------|---------|
| httpx | 0.28.1 | BSD-3-Clause | Async HTTP client |
| httpx-sse | 0.4.3 | MIT | SSE client for httpx |
| httpcore | 1.0.9 | BSD-3-Clause | HTTP core implementation |
| certifi | 2026.6.17 | MPL-2.0 | Mozilla root CA certificate bundle |
| idna | 3.18 | BSD-3-Clause | Internationalized domain name handling |

### Security & Authentication

| Component | Version | License | Purpose |
|-----------|---------|---------|---------|
| pyjwt | 2.13.0 | MIT | JSON Web Token implementation |
| cryptography | 49.0.0 | Apache-2.0 | Cryptographic primitives |
| cffi | 2.0.0 | MIT | C Foreign Function Interface |
| pycparser | 3.0 | BSD-3-Clause | C parser (cffi dependency) |

### Data Validation & Typing

| Component | Version | License | Purpose |
|-----------|---------|---------|---------|
| pydantic-core | 2.46.4 | MIT | Pydantic core engine (Rust) |
| pydantic-settings | 2.14.2 | MIT | Settings management with Pydantic |
| annotated-types | 0.7.0 | MIT | Runtime type annotation metadata |
| typing-extensions | 4.15.0 | PSF-2.0 | Typing backports |
| typing-inspection | 0.4.2 | MIT | Runtime type hint inspection |
| python-dotenv | 1.2.2 | BSD-3-Clause | .env file loader |

### JSON Schema & Utilities

| Component | Version | License | Purpose |
|-----------|---------|---------|---------|
| jsonschema | 4.26.0 | MIT | JSON Schema validation |
| jsonschema-specifications | 2025.9.1 | MIT | JSON Schema meta-schemas |
| referencing | 0.37.0 | MIT | JSON reference resolution |
| rpds-py | 2026.5.1 | MIT | Persistent data structures (Rust) |
| attrs | 26.1.0 | MIT | Class attribute definition helpers |
| click | 8.4.1 | BSD-3-Clause | Command-line toolkit |

## Update Procedure

Run after every `pip-compile` update:

```bash
# Preview changes (dry-run)
python scripts/generate_sbom.py

# Apply changes
python scripts/generate_sbom.py --apply
```
