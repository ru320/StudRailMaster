#include "HubLink.h"

static constexpr uint32_t CONNECT_TIMEOUT_MS = 5000;
static constexpr uint32_t BACKOFF_MIN_MS = 1000;
static constexpr uint32_t BACKOFF_MAX_MS = 10000;
static constexpr uint32_t RSSI_INTERVAL_MS = 2000;

SemaphoreHandle_t HubLink::radioMutex = nullptr;

static uint8_t JMC_STOP[hub::PACKET_LEN];
static uint8_t LEGO_STOP[lego::FRAME_LEN];

// drivers/jmc.json: Heartbeat 100 ms wie die Original-App, 3 Stopp-Pakete schalten frei
const HubLink::Protocol HubLink::JMC = {"0000fff0-0000-1000-8000-00805f9b34fb",
                                        "0000fff2-0000-1000-8000-00805f9b34fb",
                                        true, false, false, 3, 100, hub::PACKET_LEN, JMC_STOP};
// drivers/lego.json: LWP3, eine Nachricht je Port
const HubLink::Protocol HubLink::LEGO = {"00001623-1212-efde-1623-785feabcd123",
                                         "00001624-1212-efde-1623-785feabcd123",
                                         true, true, true, 0, 500, lego::FRAME_LEN, LEGO_STOP};

void HubLink::beginAll() {
    radioMutex = xSemaphoreCreateMutex();
    hub::buildRaw(0, 0, 0, 0, JMC_STOP);
    const int zero[lego::PORT_COUNT] = {};
    lego::encodePercent(zero, LEGO_STOP);
}

void HubLink::start(int index) {
    index_ = index;
    lock_ = xSemaphoreCreateMutex();
    memcpy(packet_, JMC_STOP, hub::PACKET_LEN);
    char name[12];
    snprintf(name, sizeof(name), "hub%d", index);
    xTaskCreatePinnedToCore(taskEntry, name, 4096, this, 2, nullptr, 1);
}

void HubLink::configure(const char* mac, bool enabled, const Protocol& proto) {
    xSemaphoreTake(lock_, portMAX_DELAY);
    if (strcmp(mac, mac_) != 0 || enabled != enabled_ || &proto != proto_) {
        strlcpy(mac_, mac, sizeof(mac_));
        enabled_ = enabled && mac[0] != '\0';
        if (&proto != proto_) memcpy(packet_, proto.stop, proto.frameLen);
        proto_ = &proto;
        cfgGen_++;
    }
    xSemaphoreGive(lock_);
}

void HubLink::setPacket(const uint8_t* pkt) {
    xSemaphoreTake(lock_, portMAX_DELAY);
    if (memcmp(pkt, packet_, proto_->frameLen) != 0) {
        memcpy(packet_, pkt, proto_->frameLen);
        packetDirty_ = true;
    }
    xSemaphoreGive(lock_);
}

const char* HubLink::stateName(State s) {
    switch (s) {
        case State::Off: return "aus";
        case State::Connecting: return "verbindet";
        case State::Ready: return "verbunden";
        case State::Backoff: return "getrennt";
    }
    return "?";
}

void HubLink::taskEntry(void* arg) { static_cast<HubLink*>(arg)->run(); }

bool HubLink::write(const uint8_t* pkt) {
    if (!writeChar_) return false;
    const Protocol& p = *taskProto_;
    if (!p.splitByLength) return writeChar_->writeValue(pkt, p.frameLen, p.withResponse);
    for (size_t i = 0; i < p.frameLen;) {  // LEGO: eine Nachricht je Port
        uint8_t n = pkt[i];
        if (n < 2 || i + n > p.frameLen) return false;
        if (!writeChar_->writeValue(pkt + i, n, p.withResponse)) return false;
        i += n;
    }
    return true;
}

void HubLink::onNotify(NimBLERemoteCharacteristic*, uint8_t* data, size_t len, bool) {
    // LEGO: 0x05 = Fehlermeldung (z. B. Befehl an einen leeren Port)
    if (len >= 5 && data[2] == 0x05) Serial.printf("[hub] meldet Fehler zu Befehl 0x%02X: %u\n", data[3], data[4]);
}

void HubLink::dropConnection(bool sendStop) {
    if (client_ && client_->isConnected()) {
        if (sendStop) write(taskProto_->stop);
        client_->disconnect();
    }
    writeChar_ = nullptr;
}

bool HubLink::connectOnce(const char* mac) {
    if (!client_) {
        client_ = NimBLEDevice::createClient();
        client_->setConnectTimeout(CONNECT_TIMEOUT_MS);
        // 15–30 ms Intervall: Write mit Response braucht 1–2 Intervalle.
        // Supervision-Timeout 2 s, damit ein abgeschalteter Hub schnell auffällt.
        client_->setConnectionParams(12, 24, 0, 200);
    }

    // Mit Timeout, damit ein laufender GUI-Scan diesen Task nicht ewig blockiert
    if (xSemaphoreTake(radioMutex, pdMS_TO_TICKS(CONNECT_TIMEOUT_MS)) != pdTRUE) return false;
    bool ok = client_->connect(NimBLEAddress(std::string(mac), BLE_ADDR_PUBLIC));
    if (ok) {
        NimBLERemoteService* svc = client_->getService(NimBLEUUID(taskProto_->service));
        writeChar_ = svc ? svc->getCharacteristic(NimBLEUUID(taskProto_->write)) : nullptr;
        ok = writeChar_ != nullptr;
        if (!ok) Serial.printf("[hub%d] Service %s nicht gefunden\n", index_, taskProto_->service);
        if (ok && taskProto_->notify && writeChar_->canNotify()) writeChar_->subscribe(true, onNotify);
    }
    xSemaphoreGive(radioMutex);

    if (!ok) {
        dropConnection(false);
        return false;
    }

    // JMC: Ein frisch eingeschalteter Hub nimmt Fahrbefehle erst nach einem Stopp-Paket an.
    for (int i = 0; i < taskProto_->armStops && ok; i++) ok = write(taskProto_->stop);
    if (!ok) dropConnection(false);
    return ok;
}

void HubLink::run() {
    uint32_t lastSend = 0;
    uint32_t lastRssi = 0;
    char mac[18];

    for (;;) {
        bool enabled;
        uint32_t gen;
        const Protocol* proto;
        xSemaphoreTake(lock_, portMAX_DELAY);
        strlcpy(mac, mac_, sizeof(mac));
        enabled = enabled_;
        gen = cfgGen_;
        proto = proto_;
        xSemaphoreGive(lock_);

        if (gen != seenGen_) {
            seenGen_ = gen;
            dropConnection(true);  // Stopp noch im alten Protokoll
            taskProto_ = proto;
            backoffMs_ = 0;
            state_ = enabled ? State::Connecting : State::Off;
        }

        uint32_t now = millis();
        switch (state_) {
            case State::Off:
                vTaskDelay(pdMS_TO_TICKS(200));
                break;

            case State::Connecting:
                Serial.printf("[hub%d] verbinde mit %s ...\n", index_, mac);
                if (connectOnce(mac)) {
                    Serial.printf("[hub%d] verbunden\n", index_);
                    state_ = State::Ready;
                    backoffMs_ = 0;
                    xSemaphoreTake(lock_, portMAX_DELAY);
                    packetDirty_ = true;
                    xSemaphoreGive(lock_);
                } else {
                    backoffMs_ = backoffMs_ ? min(backoffMs_ * 2, BACKOFF_MAX_MS) : BACKOFF_MIN_MS;
                    backoffUntil_ = millis() + backoffMs_;
                    state_ = State::Backoff;
                    Serial.printf("[hub%d] fehlgeschlagen, neuer Versuch in %u ms\n", index_,
                                  (unsigned)backoffMs_);
                }
                break;

            case State::Backoff:
                if ((int32_t)(now - backoffUntil_) >= 0) state_ = State::Connecting;
                vTaskDelay(pdMS_TO_TICKS(50));
                break;

            case State::Ready: {
                if (!client_->isConnected()) {
                    Serial.printf("[hub%d] Verbindung verloren\n", index_);
                    reconnects_ = reconnects_ + 1;
                    writeChar_ = nullptr;
                    backoffMs_ = BACKOFF_MIN_MS;
                    backoffUntil_ = now + backoffMs_;
                    state_ = State::Backoff;
                    break;
                }
                uint8_t pkt[MAX_FRAME];
                bool dirty;
                xSemaphoreTake(lock_, portMAX_DELAY);
                bool sameProto = proto_ == taskProto_;  // sonst kommt gleich der Neuaufbau
                memcpy(pkt, sameProto ? packet_ : taskProto_->stop, taskProto_->frameLen);
                dirty = packetDirty_;
                packetDirty_ = false;
                xSemaphoreGive(lock_);

                if (dirty || now - lastSend >= taskProto_->heartbeatMs) {
                    lastSend = now;
                    if (!write(pkt)) {
                        Serial.printf("[hub%d] Schreiben fehlgeschlagen\n", index_);
                        dropConnection(false);
                    }
                }
                if (now - lastRssi >= RSSI_INTERVAL_MS) {
                    lastRssi = now;
                    rssi_ = client_->getRssi();
                }
                vTaskDelay(pdMS_TO_TICKS(5));
                break;
            }
        }
    }
}
