#include <unity.h>
#include <HubProtocol.h>

using namespace hub;

// Referenzpakete aus dem Mitschnitt der Original-App (jeweils erstes Paket pro Fall)
struct Case {
    Port    port;
    int8_t  dir;
    uint8_t speed;
    uint8_t expected[PACKET_LEN];
};

static const Case CASES[] = {
    {PORT_A, +1, 0x93, {0x5A, 0x6B, 0x02, 0x00, 0x05, 0x01, 0x93, 0x00, 0x00, 0x01, 0x61}},
    {PORT_A, -1, 0xDF, {0x5A, 0x6B, 0x02, 0x00, 0x05, 0x02, 0xDF, 0x00, 0x00, 0x01, 0xAE}},
    {PORT_B, +1, 0xA0, {0x5A, 0x6B, 0x02, 0x00, 0x05, 0x08, 0xA0, 0x00, 0x00, 0x01, 0x75}},
    {PORT_B, -1, 0xBD, {0x5A, 0x6B, 0x02, 0x00, 0x05, 0x04, 0xBD, 0x00, 0x00, 0x01, 0x8E}},
    {PORT_C, +1, 0xFF, {0x5A, 0x6B, 0x02, 0x00, 0x05, 0x00, 0x00, 0x01, 0xFF, 0x01, 0xCD}},
    {PORT_C, -1, 0x9A, {0x5A, 0x6B, 0x02, 0x00, 0x05, 0x00, 0x00, 0x02, 0x9A, 0x01, 0x69}},
    {PORT_D, +1, 0xBF, {0x5A, 0x6B, 0x02, 0x00, 0x05, 0x00, 0x00, 0x08, 0xBF, 0x01, 0x94}},
    {PORT_D, -1, 0xD5, {0x5A, 0x6B, 0x02, 0x00, 0x05, 0x00, 0x00, 0x04, 0xD5, 0x01, 0xA6}},
};

static const uint8_t STOP[PACKET_LEN] = {0x5A, 0x6B, 0x02, 0x00, 0x05, 0x00, 0x00, 0x00, 0x00, 0x01, 0xCD};

void test_capture_cases() {
    for (const Case& c : CASES) {
        PortCmd cmds[PORT_COUNT] = {};
        cmds[c.port] = {c.dir, c.speed};
        uint8_t pkt[PACKET_LEN];
        buildPacket(cmds, pkt);
        TEST_ASSERT_EQUAL_HEX8_ARRAY(c.expected, pkt, PACKET_LEN);
    }
}

void test_stop() {
    PortCmd cmds[PORT_COUNT] = {};
    uint8_t pkt[PACKET_LEN];
    buildPacket(cmds, pkt);
    TEST_ASSERT_EQUAL_HEX8_ARRAY(STOP, pkt, PACKET_LEN);
}

void test_speed_zero_is_stop() {
    PortCmd cmds[PORT_COUNT] = {{+1, 0}, {-1, 0}, {+1, 0}, {-1, 0}};
    uint8_t pkt[PACKET_LEN];
    buildPacket(cmds, pkt);
    TEST_ASSERT_EQUAL_HEX8_ARRAY(STOP, pkt, PACKET_LEN);
}

void test_pair_uses_max_speed() {
    PortCmd cmds[PORT_COUNT] = {{+1, 0x90}, {-1, 0xC0}, {}, {}};
    uint8_t pkt[PACKET_LEN];
    buildPacket(cmds, pkt);
    TEST_ASSERT_EQUAL_HEX8(0x01 | 0x04, pkt[5]);
    TEST_ASSERT_EQUAL_HEX8(0xC0, pkt[6]);
    TEST_ASSERT_EQUAL_HEX8(checksum(pkt, PACKET_LEN - 1), pkt[10]);
}

void test_both_pairs_independent() {
    PortCmd cmds[PORT_COUNT] = {{+1, 0x90}, {}, {}, {-1, 0xE0}};
    uint8_t pkt[PACKET_LEN];
    buildPacket(cmds, pkt);
    TEST_ASSERT_EQUAL_HEX8(0x01, pkt[5]);
    TEST_ASSERT_EQUAL_HEX8(0x90, pkt[6]);
    TEST_ASSERT_EQUAL_HEX8(0x04, pkt[7]);
    TEST_ASSERT_EQUAL_HEX8(0xE0, pkt[8]);
}

void setUp() {}
void tearDown() {}

int main() {
    UNITY_BEGIN();
    RUN_TEST(test_capture_cases);
    RUN_TEST(test_stop);
    RUN_TEST(test_speed_zero_is_stop);
    RUN_TEST(test_pair_uses_max_speed);
    RUN_TEST(test_both_pairs_independent);
    return UNITY_END();
}
