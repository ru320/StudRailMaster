"""Werbung unter Linux direkt per HCI-Socket, ohne hcitool.

Der Hub verlangt exakt „02 01 02 1B FF F0 FF …“; BlueZ würde die Flags selbst setzen bzw.
im Broadcast-Modus weglassen. Darum gehen die Kommandos am bluetoothd vorbei an den Controller.
Braucht CAP_NET_RAW (siehe docs: setcap), sonst ok = False mit Hinweis in der GUI.

Ältere Controller (BT 4.x) kennen nur Legacy-Advertising. Hat BlueZ den Controller schon mit
Extended Advertising benutzt, lehnt er Legacy-Kommandos ab (0x0C) – dann Extended mit
Legacy-PDU, wie es auch die App „MK Tech“ macht.
"""
import logging
import select
import socket
import struct
import time

from ..i18n import t
from . import Advertiser

log = logging.getLogger("srm.adv")

OGF_LE = 0x08
INTERVAL = 160  # × 0,625 ms = 100 ms, wie die App
ADV_HANDLE = 0x0E  # eigener Handle, BlueZ nimmt die kleinen
EVT_CMD_COMPLETE = 0x0E
EVT_CMD_STATUS = 0x0F
ERR_DISALLOWED = 0x0C
ERR_UNKNOWN_CMD = 0x01


class HciError(OSError):
    pass


class HciAdvertiser(Advertiser):
    def __init__(self, dev: int = 0):
        self.dev = dev
        self.sock = None
        self.extended = False
        self.on = False
        self.current = b""
        self.permission = False  # nur das Recht fehlt

    def _cmd(self, ocf: int, params: bytes) -> int:
        opcode = (OGF_LE << 10) | ocf
        self.sock.send(struct.pack("<BHB", 0x01, opcode, len(params)) + params)
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            r, _, _ = select.select([self.sock], [], [], max(0.0, deadline - time.monotonic()))
            if not r:
                break
            ev = self.sock.recv(260)
            if len(ev) < 7 or ev[0] != 0x04:
                continue
            if ev[1] == EVT_CMD_COMPLETE and struct.unpack_from("<H", ev, 4)[0] == opcode:
                return ev[6]
            if ev[1] == EVT_CMD_STATUS and struct.unpack_from("<H", ev, 5)[0] == opcode:
                return ev[3]
        raise HciError(t("Controller antwortet nicht", "controller does not answer"))

    def _check(self, ocf: int, params: bytes) -> None:
        status = self._cmd(ocf, params)
        if status:
            raise HciError(f"HCI 0x{ocf:04X}: Status 0x{status:02X}")

    async def start(self) -> bool:
        try:
            self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_RAW, socket.BTPROTO_HCI)
            self.sock.bind((self.dev,))
            # nur Command Complete / Command Status empfangen
            # struct hci_ufilter: 16 Byte inkl. Auffüllung, sonst EINVAL
            flt = struct.pack("<IIIH2x", 1 << 4, (1 << EVT_CMD_COMPLETE) | (1 << EVT_CMD_STATUS), 0, 0)
            self.sock.setsockopt(socket.SOL_HCI, socket.HCI_FILTER, flt)
            iv = struct.pack("<H", INTERVAL)
            # Legacy: Intervall, ADV_NONCONN_IND (nicht verbindbar, wie der ESP), öffentliche Adresse, alle Kanäle
            status = self._cmd(0x0006, iv + iv + bytes([0x03, 0x00, 0x00]) + bytes(6) + bytes([0x07, 0x00]))
            if status in (ERR_DISALLOWED, ERR_UNKNOWN_CMD):
                self.extended = True
                iv3 = INTERVAL.to_bytes(3, "little")
                # Extended-Parameter mit Legacy-PDU 0x0010 = ADV_NONCONN_IND
                self._check(
                    0x0036,
                    bytes([ADV_HANDLE]) + struct.pack("<H", 0x0010) + iv3 + iv3
                    + bytes([0x07, 0x00, 0x00]) + bytes(6) + bytes([0x00, 0x7F, 0x01, 0x00, 0x01, 0x00, 0x00]),
                )
            elif status:
                raise HciError(f"HCI 0x0006: Status 0x{status:02X}")
            self.ok, self.reason = True, ""
            log.info(t("Werbung über hci%d bereit (%s)", "advertising via hci%d ready (%s)"), self.dev,
                     "extended" if self.extended else "legacy")
        except PermissionError:
            self.ok, self.permission = False, True
            self.reason = t(
                "Mould King ist auf diesem Computer noch nicht freigeschaltet (Linux braucht dafür einmal dein Passwort).",
                "Mould King is not unlocked on this computer yet (Linux needs your password once).",
            )
        except (OSError, AttributeError) as e:
            self.ok = False
            self.reason = t("Bluetooth-Werbung nicht möglich: ", "Bluetooth advertising not possible: ") + str(e)
        if not self.ok and self.sock:
            self.sock.close()
            self.sock = None
        return self.ok

    def _enable(self, on: bool) -> None:
        if self.extended:
            self._check(0x0039, bytes([1 if on else 0, 1, ADV_HANDLE, 0, 0, 0]))
        else:
            self._check(0x000A, bytes([1 if on else 0]))
        self.on = on

    def set(self, payload: bytes) -> None:
        if not self.ok or payload == self.current:
            return
        try:
            if self.extended:
                self._check(0x0037, bytes([ADV_HANDLE, 0x03, 0x01, len(payload)]) + payload)
            else:
                self._check(0x0008, bytes([len(payload)]) + payload + bytes(31 - len(payload)))
            self.current = payload
            if not self.on:
                self._enable(True)
        except OSError as e:
            log.warning(t("Werbung: %s", "advertising: %s"), e)
            self.reason = str(e)

    async def close(self) -> None:
        if self.sock:
            try:
                if self.on:
                    self._enable(False)
            except OSError:
                pass
            self.sock.close()
            self.sock = None
        self.ok = False
        self.current = b""
