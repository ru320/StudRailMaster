# For developers: building, testing, internals

🇩🇪 [Deutsch](../../de/entwickler/bauen.md) · [Drivers](drivers.md) · [README](../../../README.md)

## Repository layout

| Path | Content |
|---|---|
| `app/` | PC app (Python package `studrailmaster`) |
| `app/studrailmaster/web/` | user interface (one HTML file), fonts, icon, demo pictures |
| `app/packaging/` | PyInstaller recipe, icons |
| `drivers/` | hub manifests + test vectors, shared by ESP and PC |
| `src/`, `lib/`, `test/`, `platformio.ini` | ESP32 firmware (PlatformIO, Arduino) |
| `hardware/` | KiCad schematic, printable case (coming later) |
| `tools/` | generators and test helpers |
| `.github/workflows/` | builds the installers |

## PC app

```bash
cd app
python3 -m venv .venv
.venv/bin/pip install -e ".[window,dev]"
.venv/bin/python -m pytest              # tests (drivers, control, server, sync, offline rules)
.venv/bin/python -m studrailmaster --demo
```

Useful during development: `--browser` (browser dev tools), `--no-gui --port 8765`, `?splash=0` and `?lang=en` in the URL.

### Ready-made programs

```bash
cd app
pyinstaller packaging/studrailmaster.spec    # result in app/dist/
```

Linux AppImage: on Linux the program ships Qt WebEngine (PySide6, extra `window`) as its own window engine – WebKitGTK cannot be packaged portably; the Chromium sandbox is off in the packaged program (`QTWEBENGINE_DISABLE_SANDBOX`, otherwise it fails on restricted user namespaces; the page only comes from 127.0.0.1). PyInstaller builds a folder on Linux, `packaging/linux/build_appimage.sh dist/StudRailMaster StudRailMaster-x86_64.AppImage` (needs [appimagetool](https://github.com/AppImage/appimagetool)). On Linux the program adds itself to the application menu on start (`~/.local/share/applications/stud-rail-master.desktop`, not when started from a temp folder).

PyInstaller only builds for the system it runs on. The GitHub workflow [`.github/workflows/stud-rail-master.yml`](../../../.github/workflows/stud-rail-master.yml) builds all three on GitHub's machines:

- every push / pull request: driver tests on the ESP side (`pio test -e native`), app tests and programs for Windows, macOS and Linux as downloadable artifacts;
- a tag `v*` (e.g. `git tag v0.9.0 && git push --tags`): additionally a release with the three files attached.

The programs are not code-signed (that needs paid certificates); users see a warning on first start, see [Installation](../install.md).

## Installing from source

Easiest: `app/start.sh` (Linux), `app/start.command` (macOS) or `app/start.bat` (Windows). The first run creates `app/.venv`, installs `-e ".[window]"` and sets up again whenever `pyproject.toml` changes. Extra options are passed on (`./start.sh --demo`).

By hand:

Python 3.10 or newer, ideally with [pipx](https://pipx.pypa.io/):

```bash
pipx install "./app[window]"
stud-rail-master
```

Without `[window]` the program opens in the browser. On Linux the own window needs WebKitGTK:

```bash
sudo apt install python3-gi gir1.2-webkit2-4.1     # Debian/Ubuntu
pipx install --system-site-packages "./app[window]"
```

### Mould King on Linux: background

Mould King hubs are driven by BLE advertising with an exact data layout (`02 01 02 1B FF F0 FF …`). BlueZ cannot produce it, so HCI commands go straight to the controller (legacy advertising; on controllers BlueZ has already used with extended advertising, extended with a legacy PDU). This needs `CAP_NET_RAW`.

Order in `radio/__init__.py` (`LinuxAdvertiser`):

1. Directly from the program (`radio/adv_linux.py`) – works if the process has the capability (root or `setcap`).
2. Via the helper **`srm-hci-helper`** (`packaging/linux/srm-hci-helper.c`, ~200 lines of C, statically linked). It can only set, send and stop advertising and talks via stdin/stdout. Only this small program gets the capability – not Python, not the whole program (with capabilities glibc also ignores `LD_LIBRARY_PATH`, which breaks packaged programs).
3. Otherwise the GUI offers **Unlock Mould King** (`linux.py`): copies the bundled helper to `~/.local/lib/stud-rail-master/` (an AppImage is mounted `nosuid`, `setcap` has no effect there) and runs `pkexec setcap cap_net_raw+ep …`. After an update the checksum differs → unlock again.

The workflow builds the helper; locally: `cc -O2 -static -o app/studrailmaster/bin/srm-hci-helper app/packaging/linux/srm-hci-helper.c`.

Without the helper (installation from source) an environment with its **own copy** of the interpreter also works:

```bash
python3 -m venv --copies ~/stud-rail-master
~/stud-rail-master/bin/pip install "./app[window]"
sudo setcap cap_net_raw,cap_net_admin+eip ~/stud-rail-master/bin/python3
```

> Never run `setcap` on the system Python or on an interpreter that is only a symlink to it – every Python script would get the capability.

On Windows `radio/adv_windows.py` uses WinRT (Windows sets the flags itself; not yet tested on a hub). macOS does not allow own manufacturer data in advertising.

## Command line

```
stud-rail-master [--demo] [--browser] [--no-gui] [--port N] [--lan] [--data DIR] [--hci N] [-v]
```

| Option | Meaning |
|---|---|
| `--demo` | simulated hubs (`radio/sim.py`), own data folder `demo/` |
| `--browser` | default browser instead of pywebview |
| `--no-gui` | server only, URL is in the log |
| `--port N` | fixed port instead of a free one |
| `--lan` | listen on all interfaces instead of 127.0.0.1 – no password! |
| `--data DIR` | different data folder |
| `--hci N` | Linux: adapter for Mould King |
| `-v` | verbose log |

In the URL, `?splash=0` (no loading screen) and `?lang=en` help.

## Internals: security and privacy

- The web server (`server.py`) listens on 127.0.0.1 only and checks the Host header (against DNS rebinding).
- Writing requests need the header `X-SRM: 1`; another website cannot set it without the browser asking first.
- A Content-Security-Policy forbids the page any outside access; fonts are bundled.
- Uploaded pictures are recognised by content (PNG, JPEG, WebP, GIF); SVG is deliberately not allowed.
- `sync.py` only connects to private, link-local or loopback addresses and ignores proxies.
- Tests in `app/tests/test_app.py` check these rules.

## ESP interface

Sync and live link use the remote's REST API (`src/WebUi.h`):

| Request | Used for |
|---|---|
| `GET /api/config` | read hubs + archive |
| `POST /api/config` `{"archive": [...]}` | write the archive |
| `GET /api/state` | live values, counts as the GUI's sign of life |
| `POST /api/input` `{"ch", "speed", "reversed"}` | drive along |
| `POST /api/estop` | emergency stop |
| `POST /api/live` `{"name"}` | sign in the live link (ESP shows the PC, takes the radio back if needed) |
| `POST /api/live` `{"release": true}` | end the live link: emergency stop, send stop for 500 ms, then disconnect the hubs (MK4: advertising off) |

While released, `/api/state` reports `"radio": "pc"`, hubs report `beim PC`, the start lock stays on. The radio comes back with a new live link or the **Take radio back** button in the ESP GUI (`POST /api/live {}`). The state is RAM only; after a restart the ESP drives again. Older firmware without `/api/live` (404) still works, just without display and hand-back.

Same hub = same type + MAC (JMC) or same slot + name (Mould King). Planned: WebSocket instead of polling, mDNS service `_studrail._tcp`, ESP as radio bridge (Mould King on macOS, IR).

## ESP32 firmware

```bash
pio run -e esp32dev -t upload     # USB
pio run -e ota -t upload          # Wi-Fi (StudRailMasterQuadro.local; other name: --upload-port name.local)
pio test -e native                # protocol + shared driver vectors on the PC
```

`src/secrets.h` (Wi-Fi, OTA password) is not part of the repository; copy `src/secrets.h.example`.

## Publishing (from the private repository)

The project lives in a private repository together with notes and work in progress. [`tools/publish.py`](../../../tools/publish.py) copies only what is released in [`publish.list`](../../../publish.list):

It syncs a parallel folder (default `~/Dokumente/stud-rail-master`) that is its own git repository and matches the public repository 1:1:

```bash
python3 tools/publish.py                       # show what would be published
python3 tools/publish.py --sync                # sync the parallel folder (git init on first run)
python3 tools/publish.py --commit "v0.9.0"     # sync + commit there
cd ~/Dokumente/stud-rail-master && git push    # yourself
```

Safety nets: only files committed to git; a block list (secrets, logs, captures, shopping list …) that always applies; it aborts if a password from `src/secrets.h` appears in any file; the target must not be inside the private repository; it only commits with a repository-local `user.email`; it never pushes.

---

*In Herbrechtingen ist es immer am schönsten!*
