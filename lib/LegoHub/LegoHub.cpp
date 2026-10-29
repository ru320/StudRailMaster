#include "LegoHub.h"

namespace lego {

static const uint8_t PORT_IDS[PORT_COUNT] = {0x00, 0x01};  // City Hub: A, B

int8_t power(int percent) {
    if (percent > 100) return 100;
    if (percent < -100) return -100;
    return (int8_t)percent;
}

void encodePercent(const int percent[PORT_COUNT], uint8_t out[FRAME_LEN]) {
    for (size_t p = 0; p < PORT_COUNT; p++) {
        uint8_t* m = out + p * MSG_LEN;
        m[0] = MSG_LEN;
        m[1] = 0x00;  // Hub-ID
        m[2] = 0x81;  // Port Output Command
        m[3] = PORT_IDS[p];
        m[4] = 0x11;  // sofort ausführen, mit Rückmeldung
        m[5] = 0x51;  // WriteDirectModeData
        m[6] = 0x00;  // Modus 0 = Leistung
        m[7] = (uint8_t)power(percent[p]);
    }
}

}  // namespace lego
