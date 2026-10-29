"""Grundlagen der Treiber.

Ein Treiber besteht aus zwei Teilen:
  * Steckbrief drivers/<id>.json (gemeinsam mit dem ESP): Transport, UUIDs, Ports, Heartbeat,
    Einschränkungen und Testvektoren.
  * Kodierung ohne Ein-/Ausgabe: Python hier in drivers/<id>.py, C++ in lib/ des ESP-Projekts.
    Beide erzeugen für dieselben Eingaben dieselben Bytes (geprüft gegen die Testvektoren).

Das Funken selbst (bleak, HCI, NimBLE) gehört nicht zum Treiber, sondern zu radio/ bzw. src/.
Darum lässt sich ein Treiber ohne Änderung zwischen PC und ESP verschieben.
"""
import json
from pathlib import Path


def spec_dirs():
    """Suchorte der Steckbriefe: im Paket (Wheel, PyInstaller) oder im Quellbaum."""
    here = Path(__file__).resolve().parent
    yield here / "specs"
    yield here.parents[2] / "drivers"  # ZugFern/drivers neben app/


def load_spec(driver_id: str) -> dict:
    for d in spec_dirs():
        f = d / f"{driver_id}.json"
        if f.is_file():
            return json.loads(f.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"Steckbrief {driver_id}.json nicht gefunden")


class Driver:
    kind = ""

    def __init__(self, spec: dict):
        self.spec = spec
        self.id = spec["id"]
        self.name = spec["name"]
        self.ports = spec["ports"]
        self.heartbeat_ms = spec.get("heartbeatMs", 100)
        self.shared_speed = spec.get("sharedSpeed", [])

    def info(self) -> dict:
        """Kurzbeschreibung für die GUI."""
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "ports": self.ports,
            "sharedSpeed": self.shared_speed,
            "slots": self.spec.get("slots", 0),
            "watchdog": self.spec.get("watchdog", False),
            "runsOn": self.spec.get("runsOn", []),
        }


class GattDriver(Driver):
    """Ein Hub = eine BLE-Verbindung, Befehle per Write auf eine Characteristic."""

    kind = "gatt"

    def __init__(self, spec: dict):
        super().__init__(spec)
        tr = spec["transport"]
        self.service_uuid = tr["service"]
        self.write_uuid = tr["write"]
        self.with_response = tr.get("withResponse", True)
        self.name_prefix = tr.get("namePrefix", "")
        self.advertised_service = tr.get("advertisedService", "").lower()
        self.notify = tr.get("notify", False)
        self.arm_frames = spec.get("armWithStop", 0)

    def encode(self, percent) -> bytes:
        """Sollwerte −100…100 je Port → ein Paket."""
        raise NotImplementedError

    def stop(self) -> bytes:
        raise NotImplementedError

    def messages(self, frame: bytes) -> list[bytes]:
        """Frame → einzelne Writes (LEGO: eine Nachricht je Port). Standard: ein Write."""
        return [frame]

    def matches(self, name: str, services) -> bool:
        """Erkennt den Hub im Scan an Namen oder beworbenem Service."""
        if self.advertised_service and self.advertised_service in {s.lower() for s in services}:
            return True
        return bool(self.name_prefix) and name.startswith(self.name_prefix)


class AdvertDriver(Driver):
    """Keine Verbindung: ein Sender steuert per Werbung mehrere Hubs (Slots)."""

    kind = "advert"

    def __init__(self, spec: dict):
        super().__init__(spec)
        self.slots = spec.get("slots", 1)
        self.pair_ms = spec.get("pairMs", 2000)

    def encode(self, slots) -> bytes:
        """{slot: [Sollwerte −100…100 je Port]} → komplette Werbedaten."""
        raise NotImplementedError

    def pair(self) -> bytes:
        """Werbedaten zum Einlernen."""
        raise NotImplementedError

    def stop(self) -> bytes:
        raise NotImplementedError
