#include <unity.h>
#include <HubProtocol.h>
#include <LegoHub.h>
#include <MouldKing.h>
#include "vectors.h"

// Dieselben Testvektoren wie app/tests/test_drivers.py (Quelle: drivers/*.json).
// Stimmen beide Seiten, lässt sich ein Treiber zwischen ESP und PC-App verschieben.

#define COUNT(a) (sizeof(a) / sizeof((a)[0]))

void test_jmc_build() {
    for (size_t i = 0; i < COUNT(JMC_BUILD); i++) {
        const JmcBuild& v = JMC_BUILD[i];
        hub::PortCmd cmds[hub::PORT_COUNT];
        for (int p = 0; p < 4; p++) cmds[p] = {v.dir[p], v.speed[p]};
        uint8_t pkt[hub::PACKET_LEN];
        hub::buildPacket(cmds, pkt);
        TEST_ASSERT_EQUAL_HEX8_ARRAY(v.frame, pkt, hub::PACKET_LEN);
    }
}

void test_jmc_speed() {
    for (size_t i = 0; i < COUNT(JMC_SPEED); i++)
        TEST_ASSERT_EQUAL_UINT8(JMC_SPEED[i].speed, hub::speedFromPercent(JMC_SPEED[i].percent));
}

void test_jmc_percent() {
    for (size_t i = 0; i < COUNT(JMC_PERCENT); i++) {
        uint8_t pkt[hub::PACKET_LEN];
        hub::encodePercent(JMC_PERCENT[i].percent, pkt);
        TEST_ASSERT_EQUAL_HEX8_ARRAY(JMC_PERCENT[i].frame, pkt, hub::PACKET_LEN);
    }
}

void test_mk4_crypt() {
    for (size_t i = 0; i < COUNT(MK4_CRYPT); i++) {
        uint8_t out[mk::CRYPT_LEN];
        mk::crypt(MK4_CRYPT[i].plain, MK4_CRYPT[i].len, out);
        TEST_ASSERT_EQUAL_HEX8_ARRAY(MK4_CRYPT[i].crypt, out, mk::CRYPT_LEN);
    }
}

static mk::Id ident(const uint8_t b[3]) { return {b[0], b[1], b[2]}; }

void test_mk4_connect() {
    for (size_t i = 0; i < COUNT(MK4_CONNECT); i++) {
        uint8_t out[mk::MK4_CONNECT_LEN];
        mk::mk4Connect(ident(MK4_CONNECT[i].ident), out);
        TEST_ASSERT_EQUAL_HEX8_ARRAY(MK4_CONNECT[i].plain, out, mk::MK4_CONNECT_LEN);
    }
}

void test_mk4_data() {
    for (size_t i = 0; i < COUNT(MK4_DATA); i++) {
        uint8_t out[mk::MK4_DATA_LEN];
        mk::mk4Data(ident(MK4_DATA[i].ident), MK4_DATA[i].levels, out);
        TEST_ASSERT_EQUAL_HEX8_ARRAY(MK4_DATA[i].plain, out, mk::MK4_DATA_LEN);
    }
}

void test_mk4_level() {
    for (size_t i = 0; i < COUNT(MK4_LEVEL); i++)
        TEST_ASSERT_EQUAL_INT8(MK4_LEVEL[i].level, mk::mk4Level(MK4_LEVEL[i].percent));
}

void test_mk4_adv() {
    for (size_t i = 0; i < COUNT(MK4_ADV); i++) {
        uint8_t out[mk::ADV_LEN];
        mk::advData(MK4_ADV[i].plain, MK4_ADV[i].len, out);
        TEST_ASSERT_EQUAL_HEX8_ARRAY(MK4_ADV[i].adv, out, mk::ADV_LEN);
    }
}

void test_lego_power() {
    for (size_t i = 0; i < COUNT(LEGO_POWER); i++)
        TEST_ASSERT_EQUAL_INT8(LEGO_POWER[i].power, lego::power(LEGO_POWER[i].percent));
}

void test_lego_percent() {
    for (size_t i = 0; i < COUNT(LEGO_PERCENT); i++) {
        uint8_t frame[lego::FRAME_LEN];
        lego::encodePercent(LEGO_PERCENT[i].percent, frame);
        TEST_ASSERT_EQUAL_HEX8_ARRAY(LEGO_PERCENT[i].frame, frame, lego::FRAME_LEN);
    }
}

int main() {
    UNITY_BEGIN();
    RUN_TEST(test_jmc_build);
    RUN_TEST(test_jmc_speed);
    RUN_TEST(test_jmc_percent);
    RUN_TEST(test_mk4_crypt);
    RUN_TEST(test_mk4_connect);
    RUN_TEST(test_mk4_data);
    RUN_TEST(test_mk4_level);
    RUN_TEST(test_mk4_adv);
    RUN_TEST(test_lego_power);
    RUN_TEST(test_lego_percent);
    return UNITY_END();
}
