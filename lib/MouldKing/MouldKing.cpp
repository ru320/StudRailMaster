#include "MouldKing.h"
#include <string.h>

namespace mk {

static const uint8_t C1C5[5] = {0xC1, 0xC2, 0xC3, 0xC4, 0xC5};

static uint8_t rev8(uint8_t v) {
    uint8_t r = 0;
    for (int i = 0; i < 8; i++)
        if (v & (1 << i)) r |= 1 << (7 - i);
    return r;
}

static uint16_t rev16(uint16_t v) {
    uint16_t r = 0;
    for (int i = 0; i < 16; i++)
        if (v & (1 << i)) r |= 1 << (15 - i);
    return r;
}

// 7-Bit-LFSR für das Whitening
struct Lfsr {
    uint8_t a[7];
    explicit Lfsr(uint8_t seed) {
        a[0] = 1;
        for (int i = 1; i < 7; i++) a[i] = (seed >> (6 - i)) & 1;
    }
    uint8_t next() {
        uint8_t r1 = a[3] ^ a[6];
        a[3] = a[2];
        a[2] = a[1];
        a[1] = a[0];
        a[0] = a[6];
        a[6] = a[5];
        a[5] = a[4];
        a[4] = r1;
        return a[0];
    }
};

static void whiten(uint8_t* buf, size_t len, uint8_t seed) {
    Lfsr l(seed);
    for (size_t i = 0; i < len; i++) {
        uint8_t r = 0;
        for (int bit = 0; bit < 8; bit++) r |= (((buf[i] >> bit) & 1) ^ l.next()) << bit;
        buf[i] = r;
    }
}

static uint16_t crcStep(uint16_t r) {
    for (int i = 0; i < 8; i++) r = (r & 0x8000) ? (uint16_t)((r << 1) ^ 0x1021) : (uint16_t)(r << 1);
    return r;
}

static uint16_t crc(const uint8_t* raw, size_t len) {
    uint16_t r = 0xFFFF;
    for (int i = 4; i >= 0; i--) r = crcStep(r ^ (C1C5[i] << 8));
    for (size_t i = 0; i < len; i++) r = crcStep(r ^ (rev8(raw[i]) << 8));
    return rev16(r) ^ 0xFFFF;
}

void crypt(const uint8_t* raw, size_t len, uint8_t out[CRYPT_LEN]) {
    // Aufbau wie MouldKingCrypt.Crypt(): ab Index 15 Präambel, ab 18 C5…C1, ab 23 Klartext, dann CRC
    const size_t n = len + 25;
    uint8_t t[25 + 14] = {};
    t[15] = 0x71;
    t[16] = 0x0F;
    t[17] = 0x55;
    for (int i = 0; i < 5; i++) t[18 + i] = C1C5[4 - i];
    memcpy(t + 23, raw, len);
    for (int i = 15; i < 23; i++) t[i] = rev8(t[i]);
    uint16_t cs = crc(raw, len);
    t[23 + len] = cs & 0xFF;
    t[24 + len] = cs >> 8;
    whiten(t + 18, n - 18, 63);
    whiten(t, n, 37);

    const size_t used = len + 10;
    memcpy(out, t + 15, used);
    for (size_t i = used; i < CRYPT_LEN; i++) out[i] = (uint8_t)(i + 1);
}

void advData(const uint8_t* raw, size_t len, uint8_t out[ADV_LEN]) {
    const uint8_t head[7] = {0x02, 0x01, 0x02, CRYPT_LEN + 3, 0xFF, COMPANY_ID & 0xFF, COMPANY_ID >> 8};
    memcpy(out, head, sizeof(head));
    crypt(raw, len, out + sizeof(head));
}

void mk4Connect(const Id& id, uint8_t out[MK4_CONNECT_LEN]) {
    const uint8_t t[MK4_CONNECT_LEN] = {0xAD, id.id0, id.id1, 0x80, 0x80, 0x80, id.chk, 0x52};
    memcpy(out, t, sizeof(t));
}

static uint8_t nibble(int8_t level) {
    if (level > MK4_LEVELS) level = MK4_LEVELS;
    if (level < -MK4_LEVELS) level = -MK4_LEVELS;
    return (uint8_t)(level >= 0 ? 0x08 + level : -level);
}

void mk4Data(const Id& id, const int8_t levels[MK4_SLOTS * MK4_PORTS], uint8_t out[MK4_DATA_LEN]) {
    out[0] = 0x7D;
    out[1] = id.id0;
    out[2] = id.id1;
    for (int i = 0; i < 6; i++) out[3 + i] = (nibble(levels[2 * i]) << 4) | nibble(levels[2 * i + 1]);
    out[9] = 0x82;
}

int8_t mk4Level(int percent) {
    if (percent > 100) percent = 100;
    if (percent < -100) percent = -100;
    int mag = (percent < 0 ? -percent : percent);
    int lvl = (mag * MK4_LEVELS + 99) / 100;
    return (int8_t)(percent < 0 ? -lvl : lvl);
}

}  // namespace mk
