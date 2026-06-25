# TODO – Public Repo Vorbereitung (raspi-mcp)

Iterative Checkliste für die Umstellung von privat → öffentlich auf GitHub.
Abarbeitung in der angegebenen Reihenfolge empfohlen (Sicherheit zuerst).

---

## 1 – Sicherheits-Audit (vor Veröffentlichung zwingend)

- [x] **Secrets / Credentials im Git-Verlauf prüfen**
  `git log --all --full-diff -p | grep -iE "key|secret|token|password|bearer"` ausführen.
  Falls Treffer: History mit `git filter-repo` bereinigen **bevor** das Repo public gesetzt wird.
  Nur Beschreibungen zur Verwendung von Bearer-Token, API-Keys, Passwörtern etc. sind erlaubt — keine echten Secrets im Repo.

- [x] **`.gitignore` absichern**
  Sicherstellen, dass `.env`, `*.env`, `raspi-mcp.env`, `*.pem`, `*.key` eingetragen sind —
  damit lokal erzeugte Secrets nie versehentlich committed werden.

- [x] **`SECURITY.md` anlegen**
  Responsible-Disclosure-Prozess beschreiben (z. B. „Sicherheitslücken bitte per GitHub
  Private Vulnerability Reporting melden, kein öffentliches Issue"). GitHub zeigt diese
  Datei automatisch im Security-Tab an.

- [ ] **Private Vulnerability Reporting auf GitHub aktivieren**
  Repository → Settings → Security → „Enable private vulnerability reporting".

---

## 2 – Branch Protection (main)

- [x] **Branch `main` anlegen** (falls noch nicht vorhanden) und als Default-Branch setzen.

- [x] **Branch-Protection-Regel für `main` einrichten** (Settings → Branches → Add rule):
  - [x] Require a pull request before merging (no direct push)
  - [x] Require at least 1 approving review (optional bei Solo-Projekt, aber empfohlen für
        externe Contributions)
  - [x] Require status checks to pass before merging → CI-Workflow eintragen (siehe §3)
  - [x] Require branches to be up to date before merging
  - [x] Do not allow bypassing the above settings (auch für Admins)

- [x] **`dev` als Standard-Arbeitsbranch** in `.github/copilot-instructions.md` und README
  dokumentieren (Workflow: `dev` → PR → `main`).

- [x] **Dependabot `target-branch`** bleibt `dev` — korrekt so, da PRs von `dev` → `main`
  gehen. Kommentar in `dependabot.yml` ergänzt.

---

## 3 – CI-Workflow (GitHub Actions)

- [x] **Neuen Workflow `ci.yml` anlegen**: Läuft auf jedem Push auf `dev` und bei jedem PR
  gegen `main`.
  - `ruff check .` (Linting)
  - `pytest` (alle Tests, inkl. MockFactory + tmp_path Mocks)
  - Python-Version: 3.13 (matrix optional: 3.11, 3.12, 3.13)

- [ ] **Status-Check** in der Branch-Protection-Regel für `main` auf diesen Workflow zeigen
  lassen (erst nach erstem erfolgreichen Run auswählbar).

- [ ] **SBOM-Workflow (`sbom.yml`) anlegen**:
  Erzeugt bei jedem Release-Tag (`v*`) automatisch ein SPDX-SBOM via
  `anchore/sbom-action` und hängt es als Release-Asset an.
  Alternativ: SBOM bei jedem Merge in `main` als Artefakt sichern.

- [ ] **Dependabot-Workflow `update-lockfiles.yml`** prüfen:
  Gilt aktuell nur für `pyproject.toml`-Änderungen — passt. Sicherstellen, dass der
  PR_CREATION_TOKEN nach Repo-Veröffentlichung noch gültig ist (PAT mit `repo`-Scope).

---

## 4 – Dokumentation

- [x] **README.md erweitern**:
  - [x] Badges: CI-Status, License, Python-Version
  - [x] Hardware-Voraussetzungen (Raspberry Pi Modell, OS-Version) klarer hervorheben
  - [x] Wiring-Diagramm oder Fritzing-Skizze (auch ASCII-Art reicht) für LED- und
        DS18B20-Verkabelung
  - [x] Abschnitt „Quick Start" für neue Contributor ganz oben (3–5 Schritte)
  - [x] Link zu `CONTRIBUTING.md`
  - [x] Erwähnung, dass `venv/` lokal genutzt wird (nicht `.venv/` — `.gitignore`
        abgleichen: aktuell ist `.venv/` ignoriert, aber `venv/` nicht — **Bug beheben**)

- [x] **`CONTRIBUTING.md` anlegen**:
  - Entwicklungsumgebung auf Dev-Maschine ohne Hardware (MockFactory, tmp_path)
  - Commit-Format (`feat/fix/refactor/docs/test/chore: …`, max 72 Zeichen)
  - Branch-Workflow: Feature-Branch von `dev`, PR gegen `dev`, Merge via Squash
  - Linting: `ruff check .` vor Commit; niemals `--fix` ohne Review
  - Tests: `pytest` muss mit Exit-Code 0 durchlaufen
  - PR-Template verwenden (siehe §5)

- [x] **`CODE_OF_CONDUCT.md` anlegen**:
  Contributor Covenant v3.0 (aktuellste Version, Stand 2026-06-24).
  Bei Solo-Projekt optional, aber Best Practice für public repos.

- [x] **`CHANGELOG.md` anlegen** (Keep-a-Changelog-Format):
  Initiale Version 0.1.0 eintragen mit bisherigen Features.

---

## 5 – GitHub-Community-Standards

GitHub prüft public repos automatisch auf folgende Dateien (Insights → Community):

- [x] `LICENSE` — Lizenz wählen und Datei anlegen (Empfehlung: MIT oder Apache 2.0;
      bei Hardware-Projekten manchmal CERN OHL für Hardware-Teile relevant)
- [x] `README.md` — vorhanden, aber noch erweitern (siehe §4)
- [x] `CONTRIBUTING.md` — anlegen (siehe §4)
- [x] `CODE_OF_CONDUCT.md` — anlegen (siehe §4)
- [x] `SECURITY.md` — anlegen (siehe §1)
- [x] `.github/PULL_REQUEST_TEMPLATE.md` — anlegen:
  - Checkliste: `ruff check .` ✓, `pytest` ✓, Beschreibung der Änderung
  - Typ der Änderung (feat / fix / refactor / docs)
  - Verweis auf ggf. zugehöriges Issue
- [x] `.github/ISSUE_TEMPLATE/` — anlegen:
  - `bug_report.md` (Hardware-Modell, OS-Version, Fehlerbeschreibung, Logs)
  - `feature_request.md`

---

## 6 – SBOM (Software Bill of Materials)

- [x] **Einmalig manuell erzeugen** und als `sbom.spdx.json` ins Repo-Root committen
  (oder als Release-Asset — kein Commit ins Repo nötig):
  ```bash
  pip install cyclonedx-bom
  cyclonedx-py environment --output-format json > sbom.cyclonedx.json
  ```
  Oder via GitHub Actions `anchore/sbom-action` (empfohlen, läuft bei jedem Release).
  **→ Erledigt: `SBOM.json` (CycloneDX 1.6) + `SBOM.md` (lesbare Version), aktualisierbar
  via `python scripts/generate_sbom.py --apply`.**

- [x] **`sbom.spdx.json` / `sbom.cyclonedx.json` in `.gitignore`** eintragen, wenn
  lokal erzeugt und nicht committed werden soll.

---

## 7 – pyproject.toml / Metadaten

- [ ] **Fehlende Metadaten ergänzen**:
  ```toml
  [project]
  license = { text = "MIT" }   # nach Lizenzwahl anpassen
  authors = [{ name = "…", email = "…" }]
  keywords = ["raspberry-pi", "mcp", "gpio", "ds18b20", "iot"]
  classifiers = [
      "Programming Language :: Python :: 3",
      "License :: OSI Approved :: MIT License",
      "Operating System :: POSIX :: Linux",
  ]
  [project.urls]
  Homepage = "https://github.com/<user>/raspi-mcp"
  ```

---

## 8 – .gitignore bereinigen

- [ ] `venv/` eintragen (aktuell fehlt es — nur `.venv/` ist eingetragen)
- [ ] `.env` und `raspi-mcp.env` eintragen
- [ ] `sbom.*.json` eintragen (falls lokal erzeugt)

---

## 9 – Repo-Einstellungen auf GitHub (nach Veröffentlichung)

- [ ] **Topics setzen**: `raspberry-pi`, `mcp`, `gpio`, `ds18b20`, `iot`, `python`,
      `fastmcp`, `gpiozero`
- [ ] **Description** im Repo-Header setzen (ein Satz)
- [ ] **Website** setzen (falls vorhanden)
- [ ] **Issues und Discussions aktivieren** (falls externe Beiträge gewünscht)
- [ ] **Wikis deaktivieren** (Doku liegt im README / docs/)
- [ ] **Sponsoring** konfigurieren (optional, `FUNDING.yml`)
- [ ] **GitHub Actions Permissions**: Sicherstellen, dass Workflows nur
      `read`-Permission auf `contents` haben, außer wo explizit `write` benötigt wird

---

## Prioritäten auf einen Blick

| Priorität | Aufgabe | Pflicht vor Public? |
|-----------|---------|---------------------|
| 🔴 Kritisch | Secrets-Audit im Git-Verlauf | Ja |
| 🔴 Kritisch | `venv/` in `.gitignore` | Ja |
| 🔴 Kritisch | `LICENSE`-Datei | Ja |
| 🟠 Hoch | `SECURITY.md` + Private Vulnerability Reporting | Ja |
| 🟠 Hoch | Branch Protection `main` + CI-Workflow | Ja |
| 🟡 Mittel | `CONTRIBUTING.md`, PR-Template, Issue-Templates | Empfohlen |
| 🟡 Mittel | README-Badges, Quick Start, Wiring | Empfohlen |
| 🟢 Optional | `CODE_OF_CONDUCT.md`, CHANGELOG, SBOM | Nach Bedarf |
| 🟢 Optional | pyproject.toml Metadaten, Topics, FUNDING.yml | Nach Bedarf |
