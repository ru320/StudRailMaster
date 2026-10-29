"""LEGO Powered Up City Hub (88009): BLE-Verbindung, LEGO Wireless Protocol 3.0 (LWP3).

Noch kein Gegenstück auf dem ESP (runsOn: pc). Testvektoren in drivers/lego.json.

Eine Nachricht je Port (Port Output Command, WriteDirectModeData, Modus 0 = Leistung):

    Index:  0    1    2    3     4    5    6    7
            08   00   81   port  11   51   00   power (int8 −100…100, 0 = auslaufen)

Ein Frame sind alle Nachrichten hintereinander; Byte 0 jeder Nachricht ist ihre Länge.
Der Funk schreibt sie einzeln (messages()).
"""
from .base import GattDriver

PORT_IDS = (0x00, 0x01)  # City Hub: A, B


def power(percent: int) -> int:
    """Sollwert −100…100 → LWP3-Leistung (gleich, nur begrenzt)."""
    return max(-100, min(100, int(percent)))


def start_power(port_id: int, percent: int) -> bytes:
    return bytes([0x08, 0x00, 0x81, port_id, 0x11, 0x51, 0x00, power(percent) & 0xFF])


def encode(percent) -> bytes:
    """2 Sollwerte −100…100 (A, B) → Frame aus zwei Nachrichten."""
    return b"".join(start_power(pid, p) for pid, p in zip(PORT_IDS, percent))


def messages(frame: bytes) -> list[bytes]:
    """Frame → einzelne LWP3-Nachrichten (Byte 0 = Länge)."""
    out, i = [], 0
    while i < len(frame):
        n = frame[i]
        if n < 2 or i + n > len(frame):
            raise ValueError("kaputter LWP3-Frame")
        out.append(frame[i:i + n])
        i += n
    return out


STOP = encode([0] * len(PORT_IDS))


class LegoDriver(GattDriver):
    def encode(self, percent) -> bytes:
        return encode(percent)

    def stop(self) -> bytes:
        return STOP

    def messages(self, frame: bytes) -> list[bytes]:
        return messages(frame)
