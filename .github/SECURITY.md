# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub Issues.**

Use [GitHub Private Vulnerability Reporting](https://github.com/RolfMasfelder/raspi-mcp/security/advisories/new)
to disclose security issues privately. GitHub shows this option under the **Security** tab of the
repository.

Include in your report:
- A description of the vulnerability and its potential impact
- Steps to reproduce or a proof-of-concept
- Affected versions
- Any suggested mitigations (optional)

You will receive a response within **7 days**. If the issue is confirmed, a fix will be prepared
and a CVE will be requested if appropriate. You will be credited in the release notes unless you
prefer to remain anonymous.

## Scope

This project runs on a local Raspberry Pi and is intended for personal/homelab use. Network
exposure should be limited to trusted local networks. Do not expose the MCP HTTP endpoint to the
public internet without additional authentication and firewall rules.
