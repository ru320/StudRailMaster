"""Mould King 4.0: keine Verbindung, gesteuert wird über BLE-Werbung.

Gegenstück auf dem ESP: lib/MouldKing (mk::crypt, mk::advData, mk::mk4Connect, mk::mk4Data,
mk::mk4Level). Beide müssen die Testvektoren in drivers/mk4.json erfüllen.

Werbedaten: Flags 02 01 02 + Herstellerdaten (Company-ID 0xFFF0) mit 24 verschlüsselten Bytes.
Klartext:
    Connect  AD id0 id1 80 80 80 chk 52
    Fahren   7D id0 id1 [6 Byte, ein Nibble pro Port] 82
Ein Telegramm steuert 3 Slots × 4 Ports. Nibble: 8 = Stopp, 9…F = vorwärts Stufe 1…7,
1…7 = rückwärts Stufe 1…7 (am Hub geprüft 28.10.2026).
Verschlüsselung nach MouldKingCrypt (github.com/J0EK3R/mkconnect-python).
"""
from .base import AdvertDriver

COMPANY_ID = 0xFFF0
CRYPT_LEN = 24
ADV_LEN = 31
SLOTS = 3
PORTS = 4
LEVELS = 7

# Kennung (id0, id1, chk): der Hub lernt sie per Connect. chk gehört fest zur Kennung, die
# Regel dafür ist unbekannt – darum nur Paare aus Mitschnitten verwenden.
ID_MKTECH_A = (0x25, 0x95, 0xE7)  # eigener Mitschnitt der App „MK Tech“
ID_MOLDQUEEN = (0xAE, 0x18, 0xF3)  # github.com/jrichter24/moldqueen, am Hub getestet

_C1C5 = bytes([0xC1, 0xC2, 0xC3, 0xC4, 0xC5])


def _rev8(v: int) -> int:
    return int(f"{v:08b}"[::-1], 2)


def _rev16(v: int) -> int:
    return int(f"{v:016b}"[::-1], 2)


def _whiten(buf: bytearray, start: int, seed: int) -> None:
    # 7-Bit-LFSR wie Lfsr in MouldKing.cpp
    a = [1] + [(seed >> (6 - i)) & 1 for i in range(1, 7)]
    for i in range(start, len(buf)):
        r = 0
        for bit in range(8):
            r1 = a[3] ^ a[6]
            a[3], a[2], a[1], a[0] = a[2], a[1], a[0], a[6]
            a[6], a[5], a[4] = a[5], a[4], r1
            r |= (((buf[i] >> bit) & 1) ^ a[0]) << bit
        buf[i] = r


def _crc_step(r: int) -> int:
    for _ in range(8):
        r = ((r << 1) ^ 0x1021) & 0xFFFF if r & 0x8000 else (r << 1) & 0xFFFF
    return r


def _crc(raw: bytes) -> int:
    r = 0xFFFF
    for b in reversed(_C1C5):
        r = _crc_step(r ^ (b << 8))
    for b in raw:
        r = _crc_step(r ^ (_rev8(b) << 8))
    return _rev16(r) ^ 0xFFFF


def crypt(raw: bytes) -> bytes:
    """Klartext (≤ 14 Byte) → 24 Byte Herstellerdaten."""
    if len(raw) > 14:
        raise ValueError("Klartext höchstens 14 Byte")
    n = len(raw) + 25
    t = bytearray(n)
    t[15:18] = b"\x71\x0f\x55"
    t[18:23] = bytes(reversed(_C1C5))
    t[23 : 23 + len(raw)] = raw
    for i in range(15, 23):
        t[i] = _rev8(t[i])
    cs = _crc(raw)
    t[23 + len(raw)] = cs & 0xFF
    t[24 + len(raw)] = cs >> 8
    _whiten(t, 18, 63)
    _whiten(t, 0, 37)
    used = len(raw) + 10
    return bytes(t[15 : 15 + used]) + bytes(i + 1 for i in range(used, CRYPT_LEN))


def adv_data(raw: bytes) -> bytes:
    """Komplette Werbedaten (31 Byte): 02 01 02 1B FF F0 FF + crypt(raw)."""
    head = bytes([0x02, 0x01, 0x02, CRYPT_LEN + 3, 0xFF, COMPANY_ID & 0xFF, COMPANY_ID >> 8])
    return head + crypt(raw)


def connect(ident=ID_MOLDQUEEN) -> bytes:
    id0, id1, chk = ident
    return bytes([0xAD, id0, id1, 0x80, 0x80, 0x80, chk, 0x52])


def _nibble(level: int) -> int:
    level = max(-LEVELS, min(LEVELS, level))
    return 0x08 + level if level >= 0 else -level


def data(levels, ident=ID_MOLDQUEEN) -> bytes:
    """levels: 12 Stufen −7…7, Index = slot * 4 + port."""
    id0, id1, _ = ident
    body = bytes((_nibble(levels[2 * i]) << 4) | _nibble(levels[2 * i + 1]) for i in range(6))
    return bytes([0x7D, id0, id1]) + body + b"\x82"


def level(percent: int) -> int:
    """−100…100 % → Stufe −7…7; jeder Wert ≠ 0 ergibt mindestens Stufe 1."""
    percent = max(-100, min(100, int(percent)))
    lvl = (abs(percent) * LEVELS + 99) // 100
    return -lvl if percent < 0 else lvl


class Mk4Driver(AdvertDriver):
    ident = ID_MOLDQUEEN

    def encode(self, slots) -> bytes:
        levels = [0] * (SLOTS * PORTS)
        for slot, percent in slots.items():
            for p, v in enumerate(percent[:PORTS]):
                levels[slot * PORTS + p] = level(v)
        return adv_data(data(levels, self.ident))

    def pair(self) -> bytes:
        return adv_data(connect(self.ident))

    def stop(self) -> bytes:
        return self.encode({})
