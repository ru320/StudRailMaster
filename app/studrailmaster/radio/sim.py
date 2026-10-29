"""Demo-Modus: simulierte Hubs, kein Funk. Zum Ausprobieren und für Tests."""
import asyncio
import random

from . import Advertiser, Link


class SimRadio:
    demo = True
    ble_ok = True
    ble_error = ""

    def __init__(self):
        self.links: list[SimLink] = []
        self.adv = SimAdvertiser()

    async def check(self) -> bool:
        await asyncio.sleep(0.3)
        return True

    def gatt_link(self, address: str, driver) -> "SimLink":
        link = SimLink(address, driver)
        self.links.append(link)
        return link

    def advertiser(self) -> "SimAdvertiser":
        return self.adv

    async def scan(self, seconds: float) -> list[dict]:
        await asyncio.sleep(min(seconds, 2.0))
        return [
            {"mac": "a9:22:28:bc:3a:c7", "name": "JG_JMC-C734", "rssi": -58},
            {"mac": "13:12:05:04:ae:f2", "name": "JG_JMC-0AF2", "rssi": -71},
            {"mac": "90:84:2b:4c:aa:01", "name": "HUB NO.4", "rssi": -64, "services": ["00001623-1212-efde-1623-785feabcd123"]},
            {"mac": "5c:f3:70:11:22:33", "name": "Kaffeemaschine", "rssi": -88},
        ]


class SimLink(Link):
    def __init__(self, address: str, driver):
        super().__init__(address, driver)
        self.sent: list[bytes] = []
        self._task = None

    def start(self) -> None:
        self._task = asyncio.get_running_loop().create_task(self._run())

    async def _run(self) -> None:
        try:
            await asyncio.sleep(random.uniform(0.4, 1.2))
            self.state = "ready"
            self.rssi = random.randint(-75, -50)
            while True:
                self.sent.append(self.frame)
                del self.sent[:-50]
                await asyncio.sleep(self.driver.heartbeat_ms / 1000)
        finally:
            self.sent.append(self.driver.stop())
            self.state = "off"

    def set_frame(self, frame: bytes) -> None:
        self.frame = frame

    async def close(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


class SimAdvertiser(Advertiser):
    def __init__(self):
        self.current = b""

    async def start(self) -> bool:
        self.ok = True
        return True

    def set(self, payload: bytes) -> None:
        self.current = payload

    async def close(self) -> None:
        self.current = b""
