#include "MkLink.h"
#include <Arduino.h>
#include <NimBLEDevice.h>
#include <string.h>

namespace mklink {

static constexpr uint32_t PAIR_MS = 2000;
static constexpr uint16_t INTERVAL = 160;  // × 0,625 ms = 100 ms, wie die App
// Kennung, die der Hub per Connect lernt (am Hub getestet)
static constexpr mk::Id ID = mk::ID_MOLDQUEEN;

static bool running = false;
static bool enabled = false;  // letzter Wert von active aus update()
static uint32_t pairUntil = 0;
static uint8_t current[mk::ADV_LEN];

static bool isPairing() { return pairUntil && (int32_t)(millis() - pairUntil) < 0; }

static void send(const uint8_t* raw, size_t len) {
    uint8_t adv[mk::ADV_LEN];
    mk::advData(raw, len, adv);
    if (running && memcmp(adv, current, sizeof(adv)) == 0) return;
    memcpy(current, adv, sizeof(adv));

    NimBLEAdvertising* a = NimBLEDevice::getAdvertising();
    NimBLEAdvertisementData d;
    d.addData(adv, sizeof(adv));
    a->setAdvertisementData(d);
    if (!running) {
        a->setConnectableMode(BLE_GAP_CONN_MODE_NON);
        a->enableScanResponse(false);
        a->setMinInterval(INTERVAL);
        a->setMaxInterval(INTERVAL);
        running = a->start();
        if (!running) Serial.println("[mk] Werbung lässt sich nicht starten");
    }
}

void update(bool active, const int8_t levels[mk::MK4_SLOTS * mk::MK4_PORTS]) {
    if (!active) {
        if (running) {
            NimBLEDevice::getAdvertising()->stop();
            running = false;
            Serial.println("[mk] Sender aus");
        }
        enabled = false;
        return;
    }
    if (!enabled) pair();  // gerade aktiviert (Start oder neue Einstellungen)
    enabled = true;

    if (isPairing()) {
        uint8_t raw[mk::MK4_CONNECT_LEN];
        mk::mk4Connect(ID, raw);
        send(raw, sizeof(raw));
    } else {
        pairUntil = 0;
        uint8_t raw[mk::MK4_DATA_LEN];
        mk::mk4Data(ID, levels, raw);
        send(raw, sizeof(raw));
    }
}

void pair() {
    pairUntil = millis() + PAIR_MS;
    if (!pairUntil) pairUntil = 1;
    Serial.println("[mk] sende Connect (Einlernen)");
}

bool active() { return running; }

bool pairing() { return isPairing(); }

}  // namespace mklink
