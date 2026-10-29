# Für Entwickler: Bauen, Testen, Technik

🇬🇧 [English](../../en/dev/building.md) · [Treiber](treiber.md) · [README](../../../README.de.md)

## Aufbau des Repos

| Pfad | Inhalt |
|---|---|
| `app/` | PC-Programm (Python-Paket `studrailmaster`) |
| `app/studrailmaster/web/` | Oberfläche (eine HTML-Datei), Schriften, Icon, Demo-Bilder |
| `app/packaging/` | PyInstaller-Rezept, Icons |
| `drivers/` | Hub-Steckbriefe + Testvektoren, gemeinsam für ESP und PC |
| `src/`, `lib/`, `test/`, `platformio.ini` | ESP32-Firmware (PlatformIO, Arduino) |
| `hardware/` | Stückliste, druckbares Gehäuse mit CAD-Modell (Vorschau, ungetestet), Schaltplan folgt |
| `tools/` | Generatoren und Testhelfer |
| `.github/workflows/` | baut die Installer |

## PC-Programm

```bash
cd app
python3 -m venv .venv
.venv/bin/pip install -e ".[window,dev]"
.venv/bin/python -m pytest              # Tests (Treiber, Steuerung, Server, Abgleich, Offline-Regeln)
.venv/bin/python -m studrailmaster --demo
```

Beim Entwickeln praktisch: `--browser` (Entwicklerwerkzeuge des Browsers), `--no-gui --port 8765`, in der Adresse `?splash=0` und `?lang=en`.

### Fertige Programme

```bash
cd app
pyinstaller packaging/studrailmaster.spec    # Ergebnis in app/dist/
```

Linux-AppImage: Unter Linux bringt das Programm Qt WebEngine (PySide6, Extra `window`) als eigene Fenster-Engine mit – WebKitGTK lässt sich nicht portabel einpacken; die Chromium-Sandbox ist im fertigen Programm aus (`QTWEBENGINE_DISABLE_SANDBOX`, sonst scheitert sie an gesperrten User-Namespaces, die Seite kommt nur von 127.0.0.1). PyInstaller baut unter Linux einen Ordner, `packaging/linux/build_appimage.sh dist/StudRailMaster StudRailMaster-x86_64.AppImage` (braucht [appimagetool](https://github.com/AppImage/appimagetool)). Beim Start trägt sich das Programm unter Linux selbst ins Startmenü ein (`~/.local/share/applications/stud-rail-master.desktop`, nicht bei Starts aus einem Temp-Ordner).

PyInstaller baut nur für das System, auf dem es läuft. Der GitHub-Workflow [`.github/workflows/stud-rail-master.yml`](../../../.github/workflows/stud-rail-master.yml) baut alle drei auf GitHubs Rechnern:

- bei jedem Push / Pull-Request: Treiber-Tests der ESP-Seite (`pio test -e native`), App-Tests und Programme für Windows, macOS und Linux als Download-Artefakte;
- bei einem Tag `v*` (z. B. `git tag v0.9.0 && git push --tags`): zusätzlich ein Release mit den drei Dateien.

Die Programme sind nicht signiert (dafür braucht es kostenpflichtige Zertifikate); beim ersten Start erscheint eine Warnung, siehe [Installation](../installation.md).

## Aus dem Quellcode installieren

Am einfachsten: `app/start.sh` (Linux), `app/start.command` (macOS) bzw. `app/start.bat` (Windows). Legt beim ersten Mal `app/.venv` an, installiert `-e ".[window]"` und richtet sich neu ein, sobald sich `pyproject.toml` ändert. Zusätze werden durchgereicht (`./start.sh --demo`).

Von Hand:

Python 3.10 oder neuer, am besten mit [pipx](https://pipx.pypa.io/):

```bash
pipx install "./app[window]"
stud-rail-master
```

Ohne `[window]` öffnet sich das Programm im Browser. Unter Linux braucht das eigene Fenster WebKitGTK:

```bash
sudo apt install python3-gi gir1.2-webkit2-4.1     # Debian/Ubuntu
pipx install --system-site-packages "./app[window]"
```

### Mould King unter Linux: Hintergrund

Mould-King-Hubs werden über BLE-Werbung mit exakt festgelegten Daten gesteuert (`02 01 02 1B FF F0 FF …`). BlueZ kann die nicht erzeugen, darum gehen HCI-Kommandos direkt an den Controller (Legacy-Advertising, bei Controllern, die BlueZ schon mit Extended Advertising benutzt hat, Extended mit Legacy-PDU). Dafür braucht es `CAP_NET_RAW`.

Reihenfolge in `radio/__init__.py` (`LinuxAdvertiser`):

1. Direkt aus dem Programm (`radio/adv_linux.py`) – klappt, wenn der Prozess das Recht hat (root oder `setcap`).
2. Über das Hilfsprogramm **`srm-hci-helper`** (`packaging/linux/srm-hci-helper.c`, ~200 Zeilen C, statisch gebaut). Es kann nur Werbung setzen, senden und abschalten und spricht über stdin/stdout. Nur dieses kleine Programm bekommt das Recht – nicht Python, nicht das ganze Programm (mit Sonderrechten ignoriert glibc außerdem `LD_LIBRARY_PATH`, was gepackte Programme stört).
3. Sonst bietet die GUI **Mould King freischalten** an (`linux.py`): kopiert das mitgelieferte Hilfsprogramm nach `~/.local/lib/stud-rail-master/` (eine AppImage ist `nosuid` eingehängt, dort wirkt `setcap` nicht) und ruft `pkexec setcap cap_net_raw+ep …` auf. Nach einem Update unterscheidet sich die Prüfsumme → erneut freischalten.

Das Hilfsprogramm baut der Workflow; lokal: `cc -O2 -static -o app/studrailmaster/bin/srm-hci-helper app/packaging/linux/srm-hci-helper.c`.

Ohne Hilfsprogramm (Installation aus dem Quellcode) geht auch eine Umgebung mit **eigener Kopie** des Interpreters:

```bash
python3 -m venv --copies ~/stud-rail-master
~/stud-rail-master/bin/pip install "./app[window]"
sudo setcap cap_net_raw,cap_net_admin+eip ~/stud-rail-master/bin/python3
```

> Nie `setcap` auf das System-Python oder auf einen Interpreter, der nur ein Symlink darauf ist – sonst bekäme jedes Python-Skript das Recht.

Unter Windows sendet `radio/adv_windows.py` über WinRT (Flags setzt Windows selbst, am Hub noch ungetestet). macOS erlaubt keine eigenen Herstellerdaten in der Werbung.

## Kommandozeile

```
stud-rail-master [--demo] [--browser] [--no-gui] [--port N] [--lan] [--data ORDNER] [--hci N] [-v]
```

| Option | Bedeutung |
|---|---|
| `--demo` | simulierte Hubs (`radio/sim.py`), eigener Datenordner `demo/` |
| `--browser` | Standard-Browser statt pywebview |
| `--no-gui` | nur Server, Adresse steht im Log |
| `--port N` | fester Port statt eines freien |
| `--lan` | auf allen Schnittstellen statt nur 127.0.0.1 – ohne Passwort! |
| `--data ORDNER` | anderer Datenordner |
| `--hci N` | Linux: Adapter für Mould King |
| `-v` | ausführliches Log |

In der Adresse helfen `?splash=0` (ohne Ladebildschirm) und `?lang=en`.

## Technik: Sicherheit und Datenschutz

- Der Webserver (`server.py`) hört nur auf 127.0.0.1 und prüft den Host-Header (gegen DNS-Rebinding).
- Schreibende Anfragen brauchen den Header `X-SRM: 1`; eine fremde Webseite kann ihn nicht ohne Rückfrage des Browsers setzen.
- Eine Content-Security-Policy verbietet der Seite jeden Zugriff nach außen; Schriften liegen im Paket.
- Hochgeladene Bilder werden am Inhalt erkannt (PNG, JPEG, WebP, GIF), SVG ist absichtlich nicht erlaubt.
- `sync.py` verbindet sich nur mit privaten, link-lokalen oder Loopback-Adressen und ignoriert Proxys.
- Tests in `app/tests/test_app.py` prüfen diese Regeln.

## ESP-Schnittstelle

Abgleich und Live-Link nutzen die REST-API der Fernbedienung (`src/WebUi.h`):

| Anfrage | Wofür |
|---|---|
| `GET /api/config` | Hubs + Archiv lesen |
| `POST /api/config` `{"archive": [...]}` | Archiv schreiben |
| `GET /api/state` | Live-Werte, zählt als Lebenszeichen der GUI |
| `POST /api/input` `{"ch", "speed", "reversed"}` | mitfahren |
| `POST /api/estop` | Not-Stopp |
| `POST /api/live` `{"name"}` | Live-Link anmelden (ESP zeigt den PC an, holt den Funk ggf. zurück) |
| `POST /api/live` `{"release": true}` | Live-Link beenden: Not-Stopp, 500 ms Stopp senden, dann Hubs trennen (MK4: Werbung aus) |

Beim Abgeben steht in `/api/state` `"radio": "pc"`, die Hubs melden `beim PC`, die Anfahrsperre bleibt. Zurück holt der Funk ein neuer Live-Link oder der Knopf **Funk zurückholen** in der ESP-GUI (`POST /api/live {}`). Der Zustand liegt nur im RAM, nach einem Neustart funkt der ESP wieder selbst. Ältere Firmware ohne `/api/live` (404) geht weiter, nur ohne Anzeige und Rückgabe.

Gleicher Hub = gleicher Typ + MAC (JMC) bzw. gleicher Slot + Name (Mould King). Geplant: WebSocket statt Abfragen, mDNS-Dienst `_studrail._tcp`, ESP als Funkbrücke (Mould King unter macOS, IR).

## ESP32-Firmware

```bash
pio run -e esp32dev -t upload     # USB
pio run -e ota -t upload          # WLAN (StudRailMasterQuadro.local; anderer Name: --upload-port Name.local)
pio test -e native                # Protokoll + gemeinsame Treiber-Vektoren auf dem PC
```

`src/secrets.h` (WLAN, OTA-Passwort) gehört nicht ins Repo; Vorlage ist `src/secrets.h.example`.

## Veröffentlichen (aus dem privaten Repo)

Das Projekt liegt zusammen mit Notizen und Halbfertigem in einem privaten Repo. [`tools/publish.py`](../../../tools/publish.py) kopiert nur, was in [`publish.list`](../../../publish.list) freigegeben ist:

Es gleicht einen Parallelordner ab (Standard `~/Dokumente/stud-rail-master`), der ein eigenes git-Repo ist und 1:1 dem öffentlichen Repo entspricht:

```bash
python3 tools/publish.py                       # anzeigen, was rausginge
python3 tools/publish.py --sync                # Parallelordner abgleichen (beim ersten Mal git init)
python3 tools/publish.py --commit "v0.9.0"     # abgleichen + dort committen
cd ~/Dokumente/stud-rail-master && git push    # selbst
```

Sicherungen: nur in git eingecheckte Dateien; eine Sperrliste (Geheimnisse, Logs, Mitschnitte, Einkaufsliste …), die immer gilt; Abbruch, wenn ein Passwort aus `src/secrets.h` in einer Datei steht; das Ziel darf nicht im privaten Repo liegen; committet wird nur mit eigener `user.email` im Zielrepo; es wird nie gepusht.

---

*In Herbrechtingen ist es immer am schönsten!*
