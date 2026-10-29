"""BLE über bleak (Linux: BlueZ, Windows: WinRT, macOS: CoreBluetooth).

Ablauf je Hub wie HubLink auf dem ESP: verbinden, Stopp zum Freischalten, dann Paket bei
Änderung und als Heartbeat; bei Abbruch neu verbinden mit Backoff 1…10 s.
"""
import asyncio
import logging

from ..i18n import t
from . import Link, make_advertiser

log = logging.getLogger("srm.ble")

CONNECT_TIMEOUT_S = 10.0
WRITE_TIMEOUT_S = 2.0
BACKOFF_MAX_S = 10.0


class BleRadio:
    demo = False

    def __init__(self, hci: int = 0):
        self.hci = hci
        # Nur ein Verbindungsaufbau bzw. Scan gleichzeitig (wie radioMutex auf dem ESP);
        # BlueZ und WinRT mögen parallele Connects nicht.
        self.lock = asyncio.Lock()
        self.ble_ok = None  # None = noch nicht geprüft
        self.ble_error = ""

    async def check(self) -> bool:
        """Kurzer Scan, um zu sehen, ob ein Bluetooth-Adapter da ist."""
        try:
            from bleak import BleakScanner

            async with self.lock:
                await BleakScanner.discover(timeout=1.0)
            self.ble_ok, self.ble_error = True, ""
        except Exception as e:  # noqa: BLE001 – jede Ursache soll in der GUI landen
            self.ble_ok, self.ble_error = False, str(e) or type(e).__name__
        return self.ble_ok

    def gatt_link(self, address: str, driver) -> "GattLink":
        return GattLink(self, address, driver)

    def advertiser(self):
        return make_advertiser(self.hci)

    async def scan(self, seconds: float) -> list[dict]:
        from bleak import BleakScanner

        async with self.lock:
            found = await BleakScanner.discover(timeout=seconds, return_adv=True)
        out = []
        for dev, adv in found.values():
            name = adv.local_name or dev.name
            if not name:
                continue  # Hubs melden sich mit Namen (z. B. JG_JMC-C734)
            out.append({"mac": dev.address, "name": name, "rssi": adv.rssi, "services": list(adv.service_uuids or [])})
        self.ble_ok = True
        return out


class GattLink(Link):
    def __init__(self, radio: BleRadio, address: str, driver):
        super().__init__(address, driver)
        self._radio = radio
        self._client = None
        self._char = None
        self._task = None
        self._wake = asyncio.Event()

    def start(self) -> None:
        self._task = asyncio.get_running_loop().create_task(self._run(), name=f"hub {self.address}")

    def set_frame(self, frame: bytes) -> None:
        if frame != self.frame:
            self.frame = frame
            self._wake.set()

    async def _write(self, frame: bytes) -> None:
        for msg in self.driver.messages(frame):  # LEGO: eine Nachricht je Port
            await asyncio.wait_for(
                self._client.write_gatt_char(self._char, msg, response=self.driver.with_response),
                WRITE_TIMEOUT_S,
            )

    def _notified(self, _char, data: bytearray) -> None:
        # LEGO meldet u. a. angesteckte Geräte (0x04) und Fehler (0x05); nur fürs Log
        if len(data) >= 3 and data[2] == 0x05:
            log.warning(t("%s meldet Fehler: %s", "%s reports error: %s"), self.address, data.hex(" "))
        else:
            log.debug("%s ← %s", self.address, data.hex(" "))

    async def _session(self) -> None:
        from bleak import BleakClient

        self.state = "connecting"
        async with self._radio.lock:
            log.info(t("verbinde mit %s …", "connecting to %s …"), self.address)
            client = BleakClient(self.address, timeout=CONNECT_TIMEOUT_S, disconnected_callback=lambda _c: self._wake.set())
            self._client = client
            await client.connect()
        self._char = client.services.get_characteristic(self.driver.write_uuid)
        if self._char is None:
            raise RuntimeError(t("Characteristic %s fehlt", "characteristic %s missing") % self.driver.write_uuid[4:8])
        if self.driver.notify:
            await client.start_notify(self._char, self._notified)
        # Ein frisch eingeschalteter Hub nimmt Fahrbefehle erst nach einem Stopp-Paket an
        for _ in range(self.driver.arm_frames):
            await self._write(self.driver.stop())
        self.state, self.error = "ready", ""
        log.info(t("%s verbunden", "%s connected"), self.address)
        heartbeat = self.driver.heartbeat_ms / 1000
        while client.is_connected:
            self._wake.clear()
            await self._write(self.frame)
            try:
                await asyncio.wait_for(self._wake.wait(), heartbeat)
            except asyncio.TimeoutError:
                pass
        raise ConnectionError(t("Verbindung verloren", "connection lost"))

    async def _drop(self, send_stop: bool) -> None:
        client, self._client = self._client, None
        if client is None:
            return
        try:
            if send_stop and client.is_connected and self._char is not None:
                self._client = client
                await self._write(self.driver.stop())
                self._client = None
            await asyncio.wait_for(client.disconnect(), 3.0)
        except Exception:  # noqa: BLE001 – beim Aufräumen zählt nur, dass es weitergeht
            pass
        self._char = None

    async def _run(self) -> None:
        backoff = 0.0
        try:
            while True:
                try:
                    await self._session()
                except asyncio.CancelledError:
                    raise
                except Exception as e:  # noqa: BLE001
                    if self.state == "ready":
                        self.reconnects += 1
                    if type(e).__name__ == "BleakDeviceNotFoundError":
                        # Ein verbundener JMC-Hub wirbt nicht mehr – dann ist er für alle anderen unsichtbar
                        self.error = t("Hub nicht gefunden – eingeschaltet? Noch mit ESP oder Handy verbunden?",
                                       "hub not found – switched on? Still connected to the ESP or a phone?")
                    else:
                        self.error = str(e) or type(e).__name__
                    log.warning("%s: %s", self.address, self.error)
                    await self._drop(send_stop=False)
                    self.state = "backoff"
                    backoff = min(backoff * 2, BACKOFF_MAX_S) if backoff else 1.0
                    await asyncio.sleep(backoff)
        finally:
            # Hub hat keinen Watchdog: vor dem Trennen immer Stopp senden
            await self._drop(send_stop=True)
            self.state = "off"

    async def close(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
