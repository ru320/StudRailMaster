#include "HubProtocol.h"

namespace hub {

uint8_t checksum(const uint8_t* data, size_t len) {
    uint16_t sum = 0;
    for (size_t i = 0; i < len; i++) sum += data[i];
    return (uint8_t)(sum & 0xFF);
}

uint8_t dirBits(Port port, int8_t dir) {
    if (dir == 0) return 0;
    bool fwd = dir > 0;
    switch (port) {
        case PORT_A:
        case PORT_C: return fwd ? 0x01 : 0x02;
        case PORT_B:
        case PORT_D: return fwd ? 0x08 : 0x04;
    }
    return 0;
}

void buildRaw(uint8_t dirAB, uint8_t spdAB, uint8_t dirCD, uint8_t spdCD, uint8_t out[PACKET_LEN]) {
    out[0] = 0x5A;
    out[1] = 0x6B;
    out[2] = 0x02;
    out[3] = 0x00;
    out[4] = 0x05;
    out[5] = dirAB;
    out[6] = spdAB;
    out[7] = dirCD;
    out[8] = spdCD;
    out[9] = 0x01;
    out[10] = checksum(out, PACKET_LEN - 1);
}

// Fasst ein Port-Paar zu Richtungsbits + gemeinsamem Speed zusammen.
static void mergePair(const PortCmd& lo, Port loPort, const PortCmd& hi, Port hiPort,
                      uint8_t& dir, uint8_t& spd) {
    dir = 0;
    spd = 0;
    if (lo.dir != 0 && lo.speed > 0) {
        dir |= dirBits(loPort, lo.dir);
        spd = lo.speed;
    }
    if (hi.dir != 0 && hi.speed > 0) {
        dir |= dirBits(hiPort, hi.dir);
        if (hi.speed > spd) spd = hi.speed;
    }
}

void buildPacket(const PortCmd cmds[PORT_COUNT], uint8_t out[PACKET_LEN]) {
    uint8_t dirAB, spdAB, dirCD, spdCD;
    mergePair(cmds[PORT_A], PORT_A, cmds[PORT_B], PORT_B, dirAB, spdAB);
    mergePair(cmds[PORT_C], PORT_C, cmds[PORT_D], PORT_D, dirCD, spdCD);
    buildRaw(dirAB, spdAB, dirCD, spdCD, out);
}

uint8_t speedFromPercent(int percent) {
    int mag = percent < 0 ? -percent : percent;
    if (mag > 100) mag = 100;
    if (mag == 0) return 0;
    return (uint8_t)(MIN_SPEED + (mag - 1) * (255 - MIN_SPEED) / 99);
}

void encodePercent(const int percent[PORT_COUNT], uint8_t out[PACKET_LEN]) {
    PortCmd cmds[PORT_COUNT];
    for (size_t p = 0; p < PORT_COUNT; p++) {
        int v = percent[p];
        cmds[p] = {(int8_t)(v > 0 ? 1 : v < 0 ? -1 : 0), speedFromPercent(v)};
    }
    buildPacket(cmds, out);
}

}  // namespace hub
