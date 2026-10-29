"""Lokaler Webserver für die GUI. REST-API wie auf dem ESP (src/WebUi.h), plus Bilder und Abgleich.

  GET  /api/info        Name, Version, Ladeschritte, Treiber, Datenordner
  GET  /api/state       Live-Werte (zählt als Lebenszeichen der GUI)
  POST /api/input       {"ch", "speed", "reversed"}
  GET  /api/config      Einstellungen
  POST /api/config      Einstellungen übernehmen (Felder: throttles, reverseMs, hubs, esp)
  POST /api/scan        BLE-Scan starten (5 s);  GET /api/scan  Ergebnis
  POST /api/estop       Not-Stopp
  POST /api/mkpair      Mould King einlernen (2 s Connect-Telegramm)
  POST /api/mkunlock    Linux: Mould King freischalten (Passwort-Fenster des Systems)
  POST /api/image/<id>  Bild für Hub (PNG/JPEG/WebP/GIF, ≤ 8 MB);  DELETE entfernt es
  GET  /img/<datei>     Hub-Bild
  GET  /help/<de|en>/<kapitel>  eingebaute Doku (HTML aus docs/), /help/img/<datei>
  POST /api/esp/fetch   {"host"} Hubs vom ESP lesen
  POST /api/esp/push    {"host", "ids"} Hubs ins ESP-Archiv schreiben
  POST /api/esp/live    {"host"} Live-Link starten, {"stop": true} beenden
  POST /api/focus       Fenster nach vorne holen (zweiter Start); {"window": false} = keins offen

Sicherheit: Standardmäßig nur 127.0.0.1. Schreibende Anfragen brauchen den Header
X-SRM: 1 (eine fremde Webseite kann ihn nicht setzen, ohne dass der Browser vorher fragt),
der Host-Header muss passen (gegen DNS-Rebinding). Die CSP verbietet der Seite jeden
Zugriff nach außen.
"""
import asyncio
import json
import logging
import mimetypes
import platform
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import MOTTO, MOTTO_EN, NAME, __version__, helpdocs
from .config import ConfigError
from .drivers import DRIVERS
from .sync import EspClient, LiveLink, SyncError, from_esp, push_to_esp

log = logging.getLogger("srm.http")

WEB = Path(__file__).resolve().parent / "web"
MAX_IMAGE = 8 * 1024 * 1024
MAX_JSON = 1024 * 1024
SCAN_S = 5.0
CSP = ("default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; "
       "script-src 'self' 'unsafe-inline'; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; "
       "base-uri 'none'; form-action 'none'")
_IMG_NAME = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{6}\.(png|jpg|webp|gif)$")
_STATIC = re.compile(r"^[A-Za-z0-9_\-/]+\.(html|ttf|txt|png|svg|css|js)$")


def image_type(data: bytes) -> str:
    """Erkennt das Format am Inhalt, nicht am Content-Type. SVG absichtlich nicht (Skripte)."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return ""


class App:
    """Alles, was der Handler braucht."""

    def __init__(self, store, engine, lan: bool = False):
        self.store = store
        self.engine = engine
        self.lan = lan
        self.port = 0
        self.scan_running = False
        self.scan_devices: list[dict] = []
        self.scan_error = ""
        self._live_lock = threading.Lock()

    def info(self) -> dict:
        return {
            "name": NAME,
            "version": __version__,
            "motto": MOTTO,
            "mottoEn": MOTTO_EN,
            "platform": f"{platform.system()} {platform.release()}",
            "os": sys.platform,
            "python": platform.python_version(),
            "demo": self.engine.radio.demo,
            "ready": self.engine.ready.is_set(),
            "steps": self.engine.steps,
            "drivers": [d.info() for d in DRIVERS.values()],
            "dataDir": str(self.store.folder),
            "lan": self.lan,
            "loadError": self.store.load_error,
        }

    def state(self) -> dict:
        self.engine.gui_alive()
        s = self.engine.state()
        live = self.engine.live
        s["mode"] = "live" if live else "local"
        s["live"] = live.status(self.store.get()["hubs"]) if live else None
        return s

    # ----- Scan -----
    def start_scan(self) -> None:
        if self.scan_running:
            return
        self.scan_running, self.scan_error = True, ""

        async def run():
            try:
                devices = await self.engine.radio.scan(SCAN_S)
                known = {h["mac"]: h["id"] for h in self.store.get()["hubs"] if h["mac"]}
                for d in devices:
                    services = d.pop("services", [])
                    d["type"] = next((k for k, drv in DRIVERS.items()
                                      if drv.kind == "gatt" and drv.matches(d["name"], services)), "")
                    d["known"] = known.get(d["mac"].lower()) or known.get(d["mac"].upper()) or ""
                self.scan_devices = devices
            except Exception as e:  # noqa: BLE001
                self.scan_error = str(e) or type(e).__name__
            finally:
                self.scan_running = False

        asyncio.run_coroutine_threadsafe(run(), self.engine.loop)

    # ----- ESP -----
    def _client(self, body: dict) -> EspClient:
        host = body.get("host") or self.store.get()["esp"]["host"]
        client = EspClient(host)
        if client.host != self.store.get()["esp"]["host"]:
            self.store.update({"esp": {"host": client.host}})
        return client

    def esp_fetch(self, body: dict) -> dict:
        client = self._client(body)
        return {"host": client.host, "hubs": from_esp(client.config())}

    def esp_push(self, body: dict) -> dict:
        client = self._client(body)
        ids = set(body.get("ids") or [])
        hubs = [h for h in self.store.get()["hubs"] if h["id"] in ids]
        return push_to_esp(client, hubs)

    def esp_live(self, body: dict) -> dict:
        with self._live_lock:
            old = self.engine.live
            if body.get("stop"):
                if old:
                    old.stop()
                    self.engine.set_live(None)
                return {"live": False}
            client = self._client(body)
            client.state()  # erreichbar? sonst Fehler, bevor der lokale Funk abgeschaltet wird
            if old:
                old.stop(release=old.client.host != client.host)  # gleicher ESP: neuer Link meldet sich gleich an
            live = LiveLink(client)
            live.start()
            self.engine.set_live(live)
            return {"live": True, "host": client.host}

    def input(self, body: dict) -> None:
        self.engine.gui_alive()
        ch = body.get("ch", -1)
        if not isinstance(ch, int):
            raise ValueError("ungültiger Kanal")
        live = self.engine.live
        if live:
            live.client.input(ch, body.get("speed"), body.get("reversed"))
        else:
            self.engine.set_input(ch, body.get("speed"), body.get("reversed"))

    def estop(self) -> None:
        self.engine.estop("gui")
        live = self.engine.live
        if live:
            live.client.estop()


class Handler(BaseHTTPRequestHandler):
    server_version = "StudRailMaster"
    sys_version = ""
    app: App = None  # wird in serve() gesetzt

    def log_message(self, fmt, *args):  # nur Fehler ins Log
        pass

    # ----- Antworten -----
    def _headers(self, code: int, ctype: str, length: int, extra: dict | None = None, frame: bool = False):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        # Hilfe-Seiten laufen als iframe in der eigenen GUI
        self.send_header("Content-Security-Policy", CSP.replace("frame-ancestors 'none'", "frame-ancestors 'self'") if frame else CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()

    def _json(self, code: int, obj) -> None:
        data = json.dumps(obj, ensure_ascii=False).encode()
        self._headers(code, "application/json; charset=utf-8", len(data))
        self.wfile.write(data)

    def _error(self, code: int, msg: str) -> None:
        self._json(code, {"error": msg})

    def _file(self, path: Path, cache: bool = False) -> None:
        try:
            data = path.read_bytes()
        except OSError:
            self._error(404, "nicht gefunden")
            return
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if ctype.startswith("text/"):
            ctype += "; charset=utf-8"
        self._headers(200, ctype, len(data), {"Cache-Control": "max-age=86400"} if cache else None)
        self.wfile.write(data)

    # ----- Prüfungen -----
    def _host_ok(self) -> bool:
        if self.app.lan:
            return True
        host = (self.headers.get("Host") or "").lower()
        return host in {f"127.0.0.1:{self.app.port}", f"localhost:{self.app.port}", f"[::1]:{self.app.port}"}

    def _body(self, limit: int) -> bytes:
        n = int(self.headers.get("Content-Length") or 0)
        if n > limit:
            raise ValueError("zu groß")
        return self.rfile.read(n) if n else b""

    def _json_body(self) -> dict:
        raw = self._body(MAX_JSON)
        body = json.loads(raw or b"{}")
        if not isinstance(body, dict):
            raise ValueError("ungültiges JSON")
        return body

    # ----- GET -----
    def do_GET(self):  # noqa: N802
        if not self._host_ok():
            return self._error(403, "Host")
        path = self.path.split("?")[0]
        app = self.app
        if path in ("/", "/index.html"):
            return self._file(WEB / "index.html")
        if path == "/api/info":
            return self._json(200, app.info())
        if path == "/api/state":
            return self._json(200, app.state())
        if path == "/api/config":
            return self._json(200, app.store.get())
        if path == "/api/scan":
            return self._json(200, {"running": app.scan_running, "devices": app.scan_devices, "error": app.scan_error})
        if path.startswith("/help/img/"):
            f = helpdocs.image(path[10:])
            return self._file(f, cache=True) if f else self._error(404, "nicht gefunden")
        if path.startswith("/help/"):
            parts = path[6:].split("/")
            html_page = helpdocs.page(*parts) if len(parts) == 2 else None
            if html_page is None:
                return self._error(404, "nicht gefunden")
            data = html_page.encode()
            self._headers(200, "text/html; charset=utf-8", len(data), frame=True)
            return self.wfile.write(data)
        if path.startswith("/img/"):
            name = path[5:]
            if not _IMG_NAME.match(name):
                return self._error(404, "nicht gefunden")
            return self._file(app.store.images / name, cache=True)
        rel = path.lstrip("/")
        if _STATIC.match(rel) and ".." not in rel:
            return self._file(WEB / rel, cache=True)
        self._error(404, "nicht gefunden")

    # ----- POST / DELETE -----
    def _write_ok(self) -> bool:
        if not self._host_ok():
            self._error(403, "Host")
            return False
        if self.headers.get("X-SRM") != "1":
            self._error(403, "X-SRM")
            return False
        return True

    def do_POST(self):  # noqa: N802
        if not self._write_ok():
            return
        path = self.path.split("?")[0]
        app = self.app
        try:
            if path.startswith("/api/image/"):
                data = self._body(MAX_IMAGE)
                ext = image_type(data)
                if not ext:
                    return self._error(415, "nur PNG, JPEG, WebP oder GIF")
                return self._json(200, app.store.set_image(path[11:], data, ext))
            body = self._json_body()
            if path == "/api/config":
                return self._json(200, app.store.update(body))
            if path == "/api/input":
                app.input(body)
                return self._json(200, {})
            if path == "/api/estop":
                app.estop()
                return self._json(200, {})
            if path == "/api/scan":
                app.start_scan()
                return self._json(202, {})
            if path == "/api/mkunlock":
                from . import linux

                err = linux.unlock()
                if err:
                    return self._error(400, err)
                app.engine.reset_advertisers()
                return self._json(200, {})
            if path == "/api/mkpair":
                app.engine.pair(body.get("type", "mk4"))
                return self._json(200, {})
            if path == "/api/esp/fetch":
                return self._json(200, app.esp_fetch(body))
            if path == "/api/esp/push":
                return self._json(200, app.esp_push(body))
            if path == "/api/esp/live":
                return self._json(200, app.esp_live(body))
            if path == "/api/focus":
                from .window import focus_window

                return self._json(200, {"window": focus_window()})
        except (ConfigError, SyncError, ValueError) as e:
            return self._error(400, str(e))
        self._error(404, "nicht gefunden")

    def do_DELETE(self):  # noqa: N802
        if not self._write_ok():
            return
        path = self.path.split("?")[0]
        if path.startswith("/api/image/"):
            try:
                return self._json(200, self.app.store.set_image(path[11:], None))
            except ConfigError as e:
                return self._error(400, str(e))
        self._error(404, "nicht gefunden")


def serve(app: App, port: int = 0) -> ThreadingHTTPServer:
    """Startet den Server in einem Hintergrund-Thread. port 0 = freier Port."""
    handler = type("BoundHandler", (Handler,), {"app": app})
    host = "0.0.0.0" if app.lan else "127.0.0.1"
    httpd = ThreadingHTTPServer((host, port), handler)
    httpd.daemon_threads = True
    app.port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, name="http", daemon=True).start()
    return httpd

