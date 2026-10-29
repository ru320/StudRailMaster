"""Abgleich mit der ZugFern-Fernbedienung (ESP32) über deren REST-API im Heimnetz.

  * Übergabe (6.1): Hubs vom ESP holen bzw. in dessen Archiv schreiben.
  * Live-Link (6.2): Der ESP ist Master. Er funkt mit den Hubs (und später IR), der PC zeigt
    seinen Zustand und darf mitfahren, solange am ESP „Schieberegler (GUI)“ eingestellt ist.
    Der lokale Funk des PCs ruht in dieser Zeit (JMC-Hubs nehmen nur eine Verbindung an).
    Beim Start meldet sich der PC per /api/live an, beim Beenden gibt der ESP den Funk ab
    (Stopp senden, Hubs trennen), damit der PC sie wieder selbst fahren kann.

Nur Adressen im lokalen Netz sind erlaubt (privat, link-local, .local), Proxys werden
ignoriert – das Programm soll nie ins Internet funken.
"""
import ipaddress
import json
import logging
import socket
import threading
import time
import urllib.error
import urllib.request

from . import NAME
from .config import new_id, normalize_address
from .drivers import DRIVERS
from .i18n import t

log = logging.getLogger("srm.sync")

TIMEOUT_S = 3.0
POLL_S = 0.3  # wie die ESP-GUI; zählt dort als Lebenszeichen
CONFIG_REFRESH_S = 5.0
ESP_MAX_ARCHIVE = 16
ESP_THROTTLES = 4

# Zustandsnamen der ESP-API → Schlüssel der PC-App
ESP_STATES = {"aus": "off", "verbindet": "connecting", "verbunden": "ready", "getrennt": "backoff",
              "sendet": "sending", "lernt ein": "pairing", "Fehler": "error", "beim PC": "off"}

_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class SyncError(Exception):
    pass


def check_host(host: str) -> str:
    """Nur Geräte im lokalen Netz. Gibt den Host zurück oder wirft SyncError."""
    host = (host or "").strip().lower()
    if not host or any(c in host for c in "/?#@ "):
        raise SyncError(t("ungültige Adresse", "invalid address"))
    name = host.split(":")[0]
    try:
        infos = socket.getaddrinfo(name, 80, proto=socket.IPPROTO_TCP)
    except OSError:
        raise SyncError(t(f"{name} nicht gefunden", f"{name} not found")) from None
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not (ip.is_private or ip.is_link_local or ip.is_loopback):
            raise SyncError(t(f"{name} liegt nicht im lokalen Netz – abgelehnt",
                              f"{name} is not on the local network – refused"))
    return host


class EspClient:
    def __init__(self, host: str):
        self.host = check_host(host)
        self.base = f"http://{self.host}"

    def _req(self, path: str, body=None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data, method="GET" if body is None else "POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with _opener.open(req, timeout=TIMEOUT_S) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read()).get("error", "")
            except ValueError:
                msg = ""
            raise SyncError(msg or f"HTTP {e.code}") from None
        except (OSError, ValueError) as e:
            raise SyncError(t("ESP nicht erreichbar: ", "ESP not reachable: ") + str(e)) from None

    def config(self) -> dict:
        return self._req("/api/config")

    def set_config(self, patch: dict) -> dict:
        return self._req("/api/config", patch)

    def state(self) -> dict:
        return self._req("/api/state")

    def input(self, ch: int, speed=None, reversed_=None) -> None:
        body = {"ch": ch}
        if speed is not None:
            body["speed"] = speed
        if reversed_ is not None:
            body["reversed"] = reversed_
        self._req("/api/input", body)

    def estop(self) -> None:
        self._req("/api/estop", {})

    def live(self, name: str) -> None:
        """Live-Link anmelden: Der ESP funkt (holt den Funk ggf. vom PC zurück)."""
        self._req("/api/live", {"name": name})

    def release(self) -> None:
        """Live-Link beenden: Der ESP stoppt alle Motoren und trennt die Hubs."""
        self._req("/api/live", {"release": True})


# ---------- Übergabe der Hub-Komponenten ----------

def hub_key(h: dict) -> tuple:
    """Woran derselbe Hub auf beiden Seiten erkannt wird."""
    if DRIVERS[h.get("type", "jmc")].kind == "gatt":
        return (h.get("type", "jmc"), (h.get("mac") or "").lower())
    return (h["type"], h.get("slot", 0), h.get("name", ""))


def _is_empty(h: dict) -> bool:
    return not h.get("mac") and h.get("type", "jmc") != "mk4" and not any(r.get("source") for r in h.get("routes", []))


def from_esp(esp_cfg: dict) -> list[dict]:
    """ESP-Hubs (aktive Plätze + Archiv) als Hubs der PC-App, erst einmal abgestellt."""
    out = []
    for where, hubs in (("slot", esp_cfg.get("hubs", [])), ("archive", esp_cfg.get("archive", []))):
        for i, h in enumerate(hubs):
            if _is_empty(h) or h.get("type", "jmc") not in DRIVERS:
                continue
            try:
                mac = normalize_address(h.get("mac", ""))
            except ValueError:
                mac = ""
            out.append({
                "id": new_id(), "name": h.get("name", ""), "type": h.get("type", "jmc"), "mac": mac,
                "slot": h.get("slot", 0), "enabled": False, "image": "", "note": "",
                "routes": [{"source": r.get("source", 0), "invert": bool(r.get("invert"))} for r in h.get("routes", [])],
                "esp": {"where": where, "index": i, "enabled": bool(h.get("enabled"))},
            })
    return out


def to_esp(hub: dict) -> tuple[dict, str]:
    """Hub der PC-App → ESP-Format. Zweiter Wert: Warnung (leer = alles übernommen)."""
    warn = []
    if "esp32" not in DRIVERS[hub["type"]].spec.get("runsOn", []):
        raise SyncError(t(f"Hub-Typ {hub['type']} gibt es auf dem ESP nicht", f"hub type {hub['type']} not on the ESP"))
    mac = hub.get("mac", "")
    if DRIVERS[hub["type"]].kind == "gatt" and "-" in mac:
        raise SyncError(t("macOS kennt die echte MAC-Adresse nicht – bitte am ESP scannen",
                          "macOS does not know the real MAC address – please scan on the ESP"))
    routes = []
    for r in hub["routes"]:
        s = r["source"]
        if s > ESP_THROTTLES:
            warn.append(t(f"Regler {s} gibt es am ESP nicht", f"throttle {s} does not exist on the ESP"))
            s = 0
        routes.append({"source": s, "invert": r["invert"]})
    esp = {"name": hub["name"][:23], "type": hub["type"], "mac": mac, "slot": hub.get("slot", 0),
           "enabled": False, "routes": routes}
    return esp, "; ".join(warn)


def push_to_esp(client: EspClient, hubs: list[dict]) -> dict:
    """Schreibt Hubs ins Archiv des ESP (gleicher Hub = aktualisieren)."""
    cfg = client.config()
    archive = cfg.get("archive", [])
    active_keys = {hub_key(h) for h in cfg.get("hubs", []) if not _is_empty(h)}
    result = {"added": [], "updated": [], "skipped": []}
    for hub in hubs:
        try:
            esp, warn = to_esp(hub)
        except SyncError as e:
            result["skipped"].append({"name": hub["name"], "reason": str(e)})
            continue
        key = hub_key(esp)
        if key in active_keys:
            result["skipped"].append({"name": hub["name"], "reason": t("ist am ESP gerade aktiv", "active on the ESP")})
            continue
        idx = next((i for i, a in enumerate(archive) if hub_key(a) == key), None)
        if idx is not None:
            archive[idx] = esp
            result["updated"].append({"name": hub["name"], "warning": warn})
        elif len(archive) >= ESP_MAX_ARCHIVE:
            result["skipped"].append({"name": hub["name"], "reason": t("ESP-Archiv voll", "ESP archive full")})
        else:
            archive.append(esp)
            result["added"].append({"name": hub["name"], "warning": warn})
    if result["added"] or result["updated"]:
        client.set_config({"archive": archive})
    return result


# ---------- Live-Link ----------

class LiveLink:
    """Fragt den ESP alle 300 ms ab; Eingaben gehen an ihn weiter."""

    def __init__(self, client: EspClient):
        self.client = client
        self.name = f"{NAME} · {socket.gethostname()}"[:40]
        self.ok = False
        self.error = ""
        self.esp_state: dict = {}
        self.esp_config: dict = {}
        self._cfg_at = 0.0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="live-link", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self, release: bool = True) -> None:
        """Abfragen beenden; release=True: Der ESP gibt die Hubs an den PC zurück."""
        self._stop.set()
        if release:
            try:
                self.client.release()
            except SyncError as e:  # alte Firmware ohne /api/live oder ESP weg
                log.warning(t("Live-Link: Funk nicht zurückbekommen (%s)", "live link: radio not handed back (%s)"), e)

    def _register(self) -> None:
        try:
            self.client.live(self.name)
        except SyncError as e:
            if str(e) != "HTTP 404":
                raise  # ESP nicht erreichbar: wie eine fehlgeschlagene Abfrage
            # alte Firmware ohne /api/live: geht trotzdem, nur ohne Anzeige und Funk-Übergabe am ESP
            log.info(t("Live-Link: ESP-Firmware ohne /api/live", "live link: ESP firmware without /api/live"))

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                if not self.ok:  # auch nach einem Neustart des ESP wieder anmelden
                    self._register()
                if time.monotonic() - self._cfg_at > CONFIG_REFRESH_S:
                    self.esp_config = self.client.config()
                    self._cfg_at = time.monotonic()
                self.esp_state = self.client.state()
                if not self.ok:
                    log.info(t("Live-Link zu %s steht", "live link to %s up"), self.client.host)
                self.ok, self.error = True, ""
            except SyncError as e:
                if self.ok:
                    log.warning(t("Live-Link: %s", "live link: %s"), e)
                self.ok, self.error = False, str(e)
            self._stop.wait(POLL_S)

    def status(self, local_hubs: list[dict]) -> dict:
        """Zustand für die GUI: Kanäle und Hubs des ESP, Bilder von gleichen lokalen Hubs."""
        images = {hub_key(h): h["image"] for h in local_hubs if h.get("image")}
        s, c = self.esp_state, self.esp_config
        hubs = []
        states = s.get("hubs") or []
        for i, h in enumerate(c.get("hubs", [])):
            hs = states[i] if i < len(states) else {}
            hubs.append({
                "id": f"esp{i}", "name": h.get("name", ""), "type": h.get("type", "jmc"),
                "enabled": h.get("enabled", False), "routes": h.get("routes", []),
                "image": images.get(hub_key(h), ""),
                "state": ESP_STATES.get(hs.get("state", ""), hs.get("state", "")), "ready": hs.get("ready", False),
                "ports": hs.get("ports", [0, 0, 0, 0]), "pairConflict": hs.get("pairConflict", []),
            })
        return {
            "host": self.client.host, "ok": self.ok, "error": self.error,
            "input": s.get("input", "web"), "estop": s.get("estop", False),
            "channels": s.get("channels", []), "hubs": hubs,
            "net": s.get("net", {}), "uptime": s.get("uptime", 0),
        }
