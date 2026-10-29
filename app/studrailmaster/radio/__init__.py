"""Funkschicht: alles, was wirklich sendet. Die Treiber (drivers/) liefern nur Bytes.

    Radio.gatt_link(adresse, treiber)  → Link: hält eine BLE-Verbindung, sendet Pakete + Heartbeat
    Radio.advertiser()                 → Advertiser: sendet Werbedaten (Mould King)
    Radio.scan(sekunden)               → gefundene Geräte mit Namen

Alle Methoden laufen im asyncio-Loop des Funk-Threads (siehe engine.py).
"""
import sys

from ..i18n import t


class Link:
    """Gemeinsame Felder für die GUI. state: off, connecting, ready, backoff."""

    def __init__(self, address: str, driver):
        self.address = address
        self.driver = driver
        self.state = "connecting"
        self.error = ""
        self.reconnects = 0
        self.rssi = 0
        self.frame = driver.stop()

    def start(self) -> None:
        raise NotImplementedError

    def set_frame(self, frame: bytes) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        """Stopp senden, Verbindung trennen."""
        raise NotImplementedError


class Advertiser:
    """ok: Sender bereit; reason: warum nicht."""

    ok = False
    reason = ""
    unlock = False  # Linux: fehlt nur das Recht, das „Mould King freischalten“ setzt

    async def start(self) -> bool:
        raise NotImplementedError

    def set(self, payload: bytes) -> None:
        """Komplette Werbedaten (≤ 31 Byte, mit Flags) senden, bis neue kommen."""
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError


class Unsupported(Advertiser):
    def __init__(self, reason: str):
        self.reason = reason

    async def start(self) -> bool:
        return False

    def set(self, payload: bytes) -> None:
        pass

    async def close(self) -> None:
        pass


def create(demo: bool = False, hci: int = 0):
    if demo:
        from .sim import SimRadio

        return SimRadio()
    from .ble import BleRadio

    return BleRadio(hci)


class LinuxAdvertiser(Advertiser):
    """Direkt per HCI, wenn das Programm das Recht hat (root/setcap), sonst über das
    freigeschaltete Hilfsprogramm; fehlt beides, meldet es unlock = True."""

    def __init__(self, hci: int = 0):
        self.hci = hci
        self.inner: Advertiser | None = None

    async def start(self) -> bool:
        from .. import linux
        from .adv_helper import HelperAdvertiser
        from .adv_linux import HciAdvertiser

        direct = HciAdvertiser(self.hci)
        if await direct.start():
            self.inner = direct
        elif direct.permission and linux.helper_ready():
            helper = HelperAdvertiser(linux.HELPER, self.hci)
            if await helper.start():
                self.inner = helper
            else:
                self.reason = helper.reason
                self.unlock = "permission" in helper.reason  # Recht nie gesetzt → nochmal anbieten
        else:
            self.reason = direct.reason
            self.unlock = direct.permission and linux.can_unlock()
        self.ok = self.inner is not None
        if self.ok:
            self.reason = ""
        return self.ok

    def set(self, payload: bytes) -> None:
        if self.inner:
            self.inner.set(payload)
            self.reason = self.inner.reason

    async def close(self) -> None:
        if self.inner:
            await self.inner.close()
            self.inner = None
        self.ok = False


def make_advertiser(hci: int = 0) -> Advertiser:
    """Werbung mit frei wählbaren Herstellerdaten – geht nicht auf jedem System."""
    if sys.platform.startswith("linux"):
        return LinuxAdvertiser(hci)
    if sys.platform == "win32":
        from .adv_windows import WinAdvertiser

        return WinAdvertiser()
    return Unsupported(
        t(
            "macOS erlaubt Programmen keine eigenen Herstellerdaten in der Bluetooth-Werbung. "
            "Mould-King-Hubs lassen sich hier nicht steuern (geplant: über die ZugFern-Fernbedienung).",
            "macOS does not let programs put their own manufacturer data into Bluetooth advertising. "
            "Mould King hubs cannot be driven here (planned: via the ZugFern remote).",
        )
    )
