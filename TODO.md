# TODO – raspi-mcp

## Sicherheit

- [x] **Path-Traversal-Schutz für `sensor_id`**
  `pattern=r"^(28|10|22)-[0-9a-f]{12}$"` in `_SENSOR_ID_FIELD` ergänzt.
  `min_length` wurde durch das Pattern ersetzt.

- [x] **Authentication (API Key / Bearer Token)**
  `_BearerTokenMiddleware` in `server.py` implementiert. Systemd-Unit liest
  `RASPI_MCP_API_KEY` aus `/etc/raspi-mcp.env`. Ohne gesetzten Key läuft der
  Server mit Warnung aber ohne Auth (stdio-Transport bleibt immer ohne Auth).

## Code-Style / Best Practices

- [x] **`argparse` in `main()` verlagern**
  Erledigt – `server.py` ist jetzt importierbar ohne CLI-Parsing.

- [x] **`ruff target-version` auf `"py313"` hochsetzen**
  Erledigt. Auch `pi1_bak/` von ruff ausgeschlossen.

- [x] **`list_sensors()` sortiert zurückgeben**
  Erledigt – `sorted(...)` ergänzt.

- [x] **`_leds`-Dict eng typisieren**
  Erledigt – `dict[int, "LED"]` via `TYPE_CHECKING`-Guard.

- [x] **`requirements.txt` und `requirements-dev.txt` via pip-compile generieren**
  `pyproject.toml` ist Single Source of Truth. Beide Dateien werden per
  `pip-compile` generiert und nicht mehr von Hand gepflegt. Workflow im README
  dokumentiert.

## Tests

- [x] **Unit-Tests für `server.py`-Tool-Wrapper**
  `tests/test_server.py` erstellt: 6 Middleware-Tests + 12 Tool-Wrapper-Tests
  (LEDs, Blink, Temperaturen, Fahrenheit-Umrechnung, `gpio_list_leds`).

---

## Authentication – Vorschlag: Shared Secret (Bearer Token)

**Empfehlung: API-Key-Middleware via HTTP-Header `Authorization: Bearer <token>`**

Passt am besten zum Setup (ein Client: `agentic_rag`, HTTP-Transport, kein Browser):

1. Token wird als Umgebungsvariable `RASPI_MCP_API_KEY` konfiguriert (`.env` auf dem Pi,
   im systemd-Unit als `EnvironmentFile=`).
2. FastMCP / Starlette-Middleware prüft jeden Request auf den Header – bei fehlendem
   oder falschem Token → `401 Unauthorized`.
3. `agentic_rag` trägt denselben Key in seiner `.env` als `RASPI_MCP_API_KEY` ein und
   sendet ihn im Header.

**Warum kein mTLS / OAuth?**
- mTLS: Zertifikatsverwaltung ist für ein Heimnetz-Pi unverhältnismäßig aufwändig.
- OAuth: Kein Browser-Flow, kein Identity-Provider – unnötige Komplexität.
- Bearer Token ist stateless, einfach rotierbar und reicht für eine Vertrauensgrenze
  zwischen zwei privaten Diensten vollständig aus.

**Sicherheitshinweis:** HTTPS empfehlenswert, damit der Token nicht im Klartext übertragen
wird. Einfachste Lösung: nginx-Reverse-Proxy auf dem Pi mit selbst-signiertem Zertifikat,
oder WireGuard-VPN wenn `agentic_rag` ohnehin auf einer anderen Maschine läuft.
