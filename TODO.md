# TODO – raspi-mcp

## Sicherheit

- [ ] **Path-Traversal-Schutz für `sensor_id`**
  `_SENSOR_ID_FIELD` um ein `pattern`-Constraint erweitern, damit nur gültige
  1-Wire-IDs akzeptiert werden:
  ```python
  pattern=r"^(28|10|22)-[0-9a-f]{12}$"
  ```

- [x] **Authentication (API Key / Bearer Token)**
  `_BearerTokenMiddleware` in `server.py` implementiert. Systemd-Unit liest
  `RASPI_MCP_API_KEY` aus `/etc/raspi-mcp.env`. Ohne gesetzten Key läuft der
  Server mit Warnung aber ohne Auth (stdio-Transport bleibt immer ohne Auth).

## Code-Style / Best Practices

- [ ] **`argparse` in `main()` verlagern**
  `_parser.parse_args()` läuft derzeit auf Modulebene → `server.py` ist nicht
  importierbar ohne CLI-Parsing. Alles ab `_parser = …` in eine `main()`-Funktion
  einwickeln und mit `if __name__ == "__main__": main()` aufrufen.

- [ ] **`ruff target-version` auf `"py313"` hochsetzen**
  Der Pi läuft mit Python 3.13 – `pyproject.toml` sagt noch `"py311"`.

- [ ] **`list_sensors()` sortiert zurückgeben**
  `iterdir()` ist nicht deterministisch → `sorted(...)` ergänzen.

- [ ] **`_leds`-Dict eng typisieren**
  `dict[int, object]` → `dict[int, "LED"]` via `TYPE_CHECKING`-Guard, ohne die
  optionale `gpiozero`-Abhängigkeit zur Laufzeit zu erzwingen.

- [ ] **`requirements.txt` entfernen oder generieren**
  Doppelte Pflege mit `pyproject.toml`. Entweder komplett entfernen und Pi-Deploy
  auf `pip install -e .` umstellen, oder per `pip-compile` aus `pyproject.toml`
  ableiten.

## Tests

- [ ] **Unit-Tests für `server.py`-Tool-Wrapper**
  Die MCP-Tool-Funktionen (Fahrenheit-Umrechnung, Rückgabestruktur, `gpio_list_leds`
  etc.) sind bisher ungetestet. Hardware-Module sind gut abgedeckt.

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
