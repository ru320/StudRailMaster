"""Werbung über das freigeschaltete Hilfsprogramm srm-hci-helper (Linux, ohne Rechte fürs Hauptprogramm)."""
import logging
import select
import subprocess

from ..i18n import t
from . import Advertiser

log = logging.getLogger("srm.adv")


class HelperAdvertiser(Advertiser):
    def __init__(self, helper, dev: int = 0):
        self.helper = str(helper)
        self.dev = dev
        self.proc = None
        self.current = b""

    def _reply(self, timeout: float = 3.0) -> str:
        r, _, _ = select.select([self.proc.stdout], [], [], timeout)
        return self.proc.stdout.readline().strip() if r else "ERR timeout"

    async def start(self) -> bool:
        try:
            self.proc = subprocess.Popen([self.helper, str(self.dev)], stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, text=True, bufsize=1)
            first = self._reply()
        except OSError as e:
            first = f"ERR {e}"
        self.ok = first.startswith("READY")
        if self.ok:
            self.reason = ""
            log.info(t("Werbung über Hilfsprogramm bereit (%s)", "advertising via helper ready (%s)"), first[6:])
        else:
            self.reason = t("Hilfsprogramm: ", "helper: ") + first[4:]
            await self.close()
        return self.ok

    def set(self, payload: bytes) -> None:
        if not self.ok or payload == self.current:
            return
        try:
            self.proc.stdin.write(f"D {payload.hex()}\n")
            reply = self._reply()
        except OSError as e:
            reply = f"ERR {e}"
        if reply == "OK":
            self.current = payload
        else:
            self.reason = reply
            log.warning(t("Werbung: %s", "advertising: %s"), reply)

    async def close(self) -> None:
        if self.proc:
            try:
                self.proc.stdin.close()  # EOF: Hilfsprogramm schaltet die Werbung ab
                self.proc.wait(2)
            except (OSError, subprocess.TimeoutExpired):
                self.proc.kill()
            self.proc = None
        self.current = b""
