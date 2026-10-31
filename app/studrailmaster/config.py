"""Einstellungen: eine JSON-Datei im Datenordner, Bilder im Unterordner images/.

Aufbau angelehnt an die ESP-Konfiguration (src/Config.*), damit Hubs zwischen beiden
übergeben werden können. Unterschiede: beliebig viele Hubs und Fahrregler, jeder Hub hat
eine feste id und optional ein Bild; „abgestellt“ = enabled false (ersetzt das ESP-Archiv).
"""
import copy
import json
import os
import re
import secrets
import sys
import threading
from pathlib import Path

from . import SLUG
from .drivers import DRIVERS

SCHEMA = 1
MAX_THROTTLES = 16
MAX_HUBS = 200
MAX_REVERSE_MS = 20000
MAX_NAME = 40
MAX_NOTE = 500
ESP_HOST = "StudRailMasterQuadro.local"  # Standard-Gerätename der Fernbedienung
OLD_ESP_HOST = "zugfern.local"  # Name älterer Firmware, wird beim Laden ersetzt

_MAC = re.compile(r"^[0-9a-f]{2}(:[0-9a-f]{2}){5}$")
_UUID = re.compile(r"^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$")  # macOS
_ID = re.compile(r"^[0-9a-f]{8}$")
_IMAGE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{6}\.(png|jpg|webp|gif)$")


class ConfigError(ValueError):
    pass


def data_dir(override: str | None = None) -> Path:
    """Datenordner je Betriebssystem (oder --data)."""
    if override:
        return Path(override).expanduser().resolve()
    home = Path.home()
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or home / "AppData" / "Roaming")
        return base / "StudRailMaster"
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Stud Rail Master"
    base = Path(os.environ.get("XDG_DATA_HOME") or home / ".local" / "share")
    return base / SLUG


def new_id() -> str:
    return secrets.token_hex(4)


def new_hub(hub_type: str = "jmc", name: str = "") -> dict:
    d = DRIVERS[hub_type]
    return {
        "id": new_id(),
        "name": name or d.name,
        "type": hub_type,
        "mac": "",
        "slot": 0,
        "enabled": False,
        "routes": [{"source": 0, "invert": False} for _ in d.ports],
        "image": "",
        "note": "",
    }


def default_config() -> dict:
    return {
        "schema": SCHEMA,
        "throttles": 4,
        "reverseMs": 5000,
        "hubs": [],
        "esp": {"host": ESP_HOST},
    }


def normalize_address(addr: str) -> str:
    """MAC (Linux/Windows) klein, macOS-UUID groß; leer bleibt leer. Sonst ConfigError."""
    a = (addr or "").strip()
    if not a:
        return ""
    if _MAC.match(a.lower()):
        return a.lower()
    if _UUID.match(a.upper()):
        return a.upper()
    raise ConfigError(f"ungültige Adresse: {a}")


def _hub(src: dict, throttles: int, label: str) -> dict:
    if not isinstance(src, dict):
        raise ConfigError(f"{label}: kein Objekt")
    hub_type = src.get("type", "jmc")
    if hub_type not in DRIVERS:
        raise ConfigError(f"{label}: unbekannter Hub-Typ {hub_type}")
    d = DRIVERS[hub_type]
    h = new_hub(hub_type)
    hid = str(src.get("id") or h["id"])
    if not _ID.match(hid):
        raise ConfigError(f"{label}: ungültige id")
    h["id"] = hid
    h["name"] = str(src.get("name") or h["name"]).strip()[:MAX_NAME]
    h["note"] = str(src.get("note") or "")[:MAX_NOTE]
    h["enabled"] = bool(src.get("enabled", False))
    img = str(src.get("image") or "")
    if img and not _IMAGE.match(img):
        raise ConfigError(f"{label}: ungültiger Bildname")
    h["image"] = img
    if d.kind == "gatt":
        try:
            h["mac"] = normalize_address(str(src.get("mac") or ""))
        except ConfigError as e:
            raise ConfigError(f"{label}: {e}") from None
        if not h["mac"]:
            h["enabled"] = False
    else:
        slot = src.get("slot", 0)
        if not isinstance(slot, int) or not 0 <= slot < d.spec.get("slots", 1):
            raise ConfigError(f"{label}: ungültiger Slot")
        h["slot"] = slot
    routes = src.get("routes") or []
    for p in range(len(d.ports)):
        r = routes[p] if p < len(routes) and isinstance(routes[p], dict) else {}
        s = r.get("source", 0)
        if not isinstance(s, int) or s < 0:
            raise ConfigError(f"{label}: ungültige Regler-Nummer")
        h["routes"][p] = {"source": s if s <= throttles else 0, "invert": bool(r.get("invert", False))}
    return h


def validate(src: dict) -> dict:
    """Prüft eine komplette Konfiguration und gibt sie normalisiert zurück."""
    c = default_config()
    t = src.get("throttles", c["throttles"])
    if not isinstance(t, int) or not 1 <= t <= MAX_THROTTLES:
        raise ConfigError(f"Fahrregler: 1 bis {MAX_THROTTLES}")
    c["throttles"] = t
    ms = src.get("reverseMs", c["reverseMs"])
    if not isinstance(ms, (int, float)) or not 0 <= ms <= MAX_REVERSE_MS:
        raise ConfigError(f"Richtungswechsel: 0 bis {MAX_REVERSE_MS // 1000} s")
    c["reverseMs"] = int(ms)
    hubs = src.get("hubs", [])
    if not isinstance(hubs, list) or len(hubs) > MAX_HUBS:
        raise ConfigError(f"höchstens {MAX_HUBS} Hubs")
    c["hubs"] = [_hub(h, t, f"Hub {i + 1}") for i, h in enumerate(hubs)]
    ids = [h["id"] for h in c["hubs"]]
    if len(set(ids)) != len(ids):
        raise ConfigError("doppelte Hub-id")
    # Zwei aktive Hubs auf demselben Slot bzw. derselben Adresse bekämen dieselben Befehle
    seen = {}
    for h in c["hubs"]:
        if not h["enabled"]:
            continue
        key = (h["type"], h["slot"]) if DRIVERS[h["type"]].kind == "advert" else ("gatt", h["mac"])
        if key in seen:
            raise ConfigError(f"„{seen[key]}“ und „{h['name']}“ belegen dieselbe Adresse bzw. denselben Slot")
        seen[key] = h["name"]
    esp = src.get("esp") or {}
    host = str(esp.get("host") or "").strip()[:100]
    c["esp"] = {"host": ESP_HOST if host.lower() in ("", OLD_ESP_HOST) else host}
    return c


class Store:
    """Thread-sichere Konfiguration mit Revisionszähler (wie cfg::revision() auf dem ESP)."""

    def __init__(self, folder: Path):
        self.folder = folder
        self.file = folder / "config.json"
        self.images = folder / "images"
        self.images.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.revision = 1
        self._data = default_config()
        self.load_error = ""
        if self.file.exists():
            try:
                self._data = validate(json.loads(self.file.read_text(encoding="utf-8")))
            except (OSError, ValueError) as e:
                # Defekte Datei nicht überschreiben, sondern beiseitelegen
                self.load_error = str(e)
                self.file.replace(self.file.with_suffix(".defekt.json"))

    def get(self) -> dict:
        with self._lock:
            return copy.deepcopy(self._data)

    def _save(self, data: dict) -> None:
        tmp = self.file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.file)

    def update(self, patch: dict) -> dict:
        """Übernimmt geänderte Felder (hubs wird als Ganzes ersetzt), prüft und speichert."""
        if not isinstance(patch, dict):
            raise ConfigError("ungültiges JSON")
        with self._lock:
            merged = copy.deepcopy(self._data)
            for key in ("throttles", "reverseMs", "hubs", "esp"):
                if key in patch:
                    merged[key] = patch[key]
            data = validate(merged)
            self._save(data)
            old_images = {h["image"] for h in self._data["hubs"]}
            self._data = data
            self.revision += 1
        # Bilder gelöschter Hubs aufräumen
        for name in old_images - {h["image"] for h in data["hubs"]}:
            if name:
                (self.images / name).unlink(missing_ok=True)
        return copy.deepcopy(data)

    def set_image(self, hub_id: str, data: bytes | None, ext: str = "") -> dict:
        """Speichert (oder entfernt bei data=None) das Bild eines Hubs."""
        with self._lock:
            hub = next((h for h in self._data["hubs"] if h["id"] == hub_id), None)
            if hub is None:
                raise ConfigError("unbekannter Hub")
            old = hub["image"]
            if data is None:
                hub["image"] = ""
            else:
                # neuer Name bei jedem Upload, damit der Browser nicht das alte Bild zeigt
                name = f"{hub_id}-{secrets.token_hex(3)}.{ext}"
                (self.images / name).write_bytes(data)
                hub["image"] = name
            self._save(self._data)
            self.revision += 1
        if old:
            (self.images / old).unlink(missing_ok=True)
        return copy.deepcopy(hub)
