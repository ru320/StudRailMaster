#include <unity.h>
#include <MouldKing.h>

using namespace mk;

// Verschlüsselte Herstellerdaten aus dem HCI-Mitschnitt der App „MK Tech“ (28.10.2026)
static const uint8_t CAP_CONNECT[CRYPT_LEN] = {0x6d, 0xb6, 0x43, 0xcf, 0x7e, 0x8f, 0x47, 0x11, 0x48, 0x38, 0x6b, 0x38,
                                               0xd1, 0x7a, 0xcd, 0xe6, 0x63, 0x25, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18};
// Fahren, alles Stopp: 7D 25 95 88 88 88 88 88 88 82
static const uint8_t CAP_STOP[CRYPT_LEN] = {0x6d, 0xb6, 0x43, 0xcf, 0x7e, 0x8f, 0x47, 0x11, 0x98, 0x38, 0x6b, 0x30,
                                            0xd9, 0x72, 0xa2, 0x3c, 0x6f, 0x56, 0xd4, 0x02, 0x15, 0x16, 0x17, 0x18};
// Fahren, Port A rückwärts Stufe 1: 7D 25 95 18 88 88 88 88 88 82
static const uint8_t CAP_A_BACK[CRYPT_LEN] = {0x6d, 0xb6, 0x43, 0xcf, 0x7e, 0x8f, 0x47, 0x11, 0x98, 0x38, 0x6b, 0xa0,
                                              0xd9, 0x72, 0xa2, 0x3c, 0x6f, 0x56, 0x00, 0x31, 0x15, 0x16, 0x17, 0x18};

void test_connect_matches_capture() {
    uint8_t raw[MK4_CONNECT_LEN], out[CRYPT_LEN];
    mk4Connect(ID_MKTECH_A, raw);
    crypt(raw, sizeof(raw), out);
    TEST_ASSERT_EQUAL_HEX8_ARRAY(CAP_CONNECT, out, CRYPT_LEN);
}

void test_data_matches_capture() {
    int8_t levels[MK4_SLOTS * MK4_PORTS] = {};
    uint8_t raw[MK4_DATA_LEN], out[CRYPT_LEN];
    mk4Data(ID_MKTECH_A, levels, raw);
    crypt(raw, sizeof(raw), out);
    TEST_ASSERT_EQUAL_HEX8_ARRAY(CAP_STOP, out, CRYPT_LEN);

    levels[0] = -1;
    mk4Data(ID_MKTECH_A, levels, raw);
    TEST_ASSERT_EQUAL_HEX8(0x18, raw[3]);
    crypt(raw, sizeof(raw), out);
    TEST_ASSERT_EQUAL_HEX8_ARRAY(CAP_A_BACK, out, CRYPT_LEN);
}

void test_nibbles() {
    int8_t levels[MK4_SLOTS * MK4_PORTS] = {};
    levels[1] = 7;    // Slot 0 Port B
    levels[2] = 1;    // Slot 0 Port C
    levels[4] = -1;   // Slot 1 Port A
    levels[11] = 3;   // Slot 2 Port D
    uint8_t raw[MK4_DATA_LEN];
    mk4Data(ID_MOLDQUEEN, levels, raw);
    const uint8_t expected[MK4_DATA_LEN] = {0x7D, 0xAE, 0x18, 0x8F, 0x98, 0x18, 0x88, 0x88, 0x8B, 0x82};
    TEST_ASSERT_EQUAL_HEX8_ARRAY(expected, raw, MK4_DATA_LEN);
}

void test_adv_header() {
    uint8_t raw[MK4_CONNECT_LEN], adv[ADV_LEN];
    mk4Connect(ID_MKTECH_A, raw);
    advData(raw, sizeof(raw), adv);
    const uint8_t head[7] = {0x02, 0x01, 0x02, 0x1B, 0xFF, 0xF0, 0xFF};
    TEST_ASSERT_EQUAL_HEX8_ARRAY(head, adv, 7);
    TEST_ASSERT_EQUAL_HEX8_ARRAY(CAP_CONNECT, adv + 7, CRYPT_LEN);
}

void test_levels() {
    TEST_ASSERT_EQUAL_INT8(0, mk4Level(0));
    TEST_ASSERT_EQUAL_INT8(1, mk4Level(1));
    TEST_ASSERT_EQUAL_INT8(-1, mk4Level(-1));
    TEST_ASSERT_EQUAL_INT8(4, mk4Level(50));
    TEST_ASSERT_EQUAL_INT8(7, mk4Level(100));
    TEST_ASSERT_EQUAL_INT8(-7, mk4Level(-100));
    TEST_ASSERT_EQUAL_INT8(7, mk4Level(150));
}

int main() {
    UNITY_BEGIN();
    RUN_TEST(test_connect_matches_capture);
    RUN_TEST(test_data_matches_capture);
    RUN_TEST(test_nibbles);
    RUN_TEST(test_adv_header);
    RUN_TEST(test_levels);
    return UNITY_END();
}
