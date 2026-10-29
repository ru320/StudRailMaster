"""JMC-Hub (Name „JG_JMC-…“): BLE-Verbindung, 11-Byte-Paket auf Characteristic fff2.

Gegenstück auf dem ESP: lib/HubProtocol (hub::buildRaw, hub::buildPacket, hub::speedFromPercent,
hub::encodePercent). Beide müssen die Testvektoren in drivers/jmc.json erfüllen.

    Index:  0  1  2  3  4  5     6     7     8     9  10
            5A 6B 02 00 05 dirAB spdAB dirCD spdCD 01 CS

Richtungsbits: A/C vor 0x01, zurück 0x02; B/D vor 0x08, zurück 0x04.
A+B bzw. C+D teilen sich ein Speed-Byte (es gilt der größere Wert).
CS = Summe der Bytes 0..9, untere 8 Bit.
"""
from .base import GattDriver

PACKET_LEN = 11
PORT_COUNT = 4
MIN_SPEED = 0x10  # Motor läuft laut Hardwaretest ab 0x10 an


def checksum(data) -> int:
    return sum(data) & 0xFF


def dir_bits(port: int, direction: int) -> int:
    if direction == 0:
        return 0
    fwd = direction > 0
    if port in (0, 2):  # A, C
        return 0x01 if fwd else 0x02
    return 0x08 if fwd else 0x04  # B, D


def build_raw(dir_ab: int, spd_ab: int, dir_cd: int, spd_cd: int) -> bytes:
    pkt = bytearray([0x5A, 0x6B, 0x02, 0x00, 0x05, dir_ab, spd_ab, dir_cd, spd_cd, 0x01, 0])
    pkt[10] = checksum(pkt[:10])
    return bytes(pkt)


def _merge_pair(lo, lo_port, hi, hi_port):
    direction = speed = 0
    if lo[0] != 0 and lo[1] > 0:
        direction |= dir_bits(lo_port, lo[0])
        speed = lo[1]
    if hi[0] != 0 and hi[1] > 0:
        direction |= dir_bits(hi_port, hi[0])
        speed = max(speed, hi[1])
    return direction, speed


def build(cmds) -> bytes:
    """cmds: 4 × (Richtung −1/0/+1, Speed 0…255) für A–D."""
    dir_ab, spd_ab = _merge_pair(cmds[0], 0, cmds[1], 1)
    dir_cd, spd_cd = _merge_pair(cmds[2], 2, cmds[3], 3)
    return build_raw(dir_ab, spd_ab, dir_cd, spd_cd)


def speed_from_percent(percent: int) -> int:
    """Betrag 1…100 % → MIN_SPEED…255, 0 → 0 (wie hub::speedFromPercent)."""
    mag = min(abs(int(percent)), 100)
    if mag == 0:
        return 0
    return MIN_SPEED + (mag - 1) * (255 - MIN_SPEED) // 99


def encode(percent) -> bytes:
    """4 Sollwerte −100…100 (A–D) → Paket."""
    cmds = [((p > 0) - (p < 0), speed_from_percent(p)) for p in percent]
    return build(cmds)


STOP = build_raw(0, 0, 0, 0)


class JmcDriver(GattDriver):
    def encode(self, percent) -> bytes:
        return encode(percent)

    def stop(self) -> bytes:
        return STOP
