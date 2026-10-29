"""Werbung unter Windows über WinRT (BluetoothLEAdvertisementPublisher).

Die winrt-Pakete kommen mit bleak. Windows setzt die Flags selbst; ob der Mould-King-Hub
das annimmt, ist noch nicht am Hub geprüft (siehe docs, „Mould King unter Windows“).
Der Publisher übernimmt neue Daten nur nach Stopp/Start; das passiert nur bei Änderungen.
"""
import logging

from ..drivers import mk4
from ..i18n import t
from . import Advertiser

log = logging.getLogger("srm.adv")


class WinAdvertiser(Advertiser):
    def __init__(self):
        self.pub = None
        self.current = b""

    async def start(self) -> bool:
        try:
            from winrt.windows.devices.bluetooth.advertisement import BluetoothLEAdvertisementPublisher  # noqa: F401

            self.ok, self.reason = True, ""
        except ImportError as e:
            self.ok, self.reason = False, t("WinRT fehlt: ", "WinRT missing: ") + str(e)
        return self.ok

    def set(self, payload: bytes) -> None:
        if not self.ok or payload == self.current:
            return
        from winrt.windows.devices.bluetooth.advertisement import (
            BluetoothLEAdvertisementPublisher,
            BluetoothLEManufacturerData,
        )
        from winrt.windows.storage.streams import DataWriter

        # Nur die Herstellerdaten übergeben (ab Byte 7), Flags erzeugt Windows
        body = payload[7:]
        try:
            if self.pub:
                self.pub.stop()
            pub = BluetoothLEAdvertisementPublisher()
            md = BluetoothLEManufacturerData()
            md.company_id = mk4.COMPANY_ID
            w = DataWriter()
            w.write_bytes(list(body))
            md.data = w.detach_buffer()
            pub.advertisement.manufacturer_data.append(md)
            pub.start()
            self.pub = pub
            self.current = payload
        except Exception as e:  # noqa: BLE001
            self.ok = False
            self.reason = t("Windows-Werbung fehlgeschlagen: ", "Windows advertising failed: ") + str(e)
            log.warning(self.reason)

    async def close(self) -> None:
        if self.pub:
            try:
                self.pub.stop()
            except Exception:  # noqa: BLE001
                pass
            self.pub = None
        self.current = b""
