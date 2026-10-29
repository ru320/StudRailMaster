#pragma once
#include <Arduino.h>
#include <HubProtocol.h>
#include <LegoHub.h>
#include <NimBLEDevice.h>

// Eine BLE-Verbindung zu einem Hub, betrieben in einem eigenen FreeRTOS-Task.
// Der Hub kann nur Write mit Response – das blockiert pro Paket ein paar
// Verbindungsintervalle. Mit einem Task pro Hub hält ein langsamer Hub weder
// die anderen Hubs noch loop() (Potis, Web-GUI) auf.
class HubLink {
public:
    enum class State : uint8_t { Off, Connecting, Ready, Backoff };

    // Was je Hub-Typ verschieden ist (Werte wie in drivers/<id>.json).
    struct Protocol {
        const char* service;
        const char* write;
        bool withResponse;
        bool notify;        // Meldungen des Hubs abonnieren (LEGO: Fehler ins Log)
        bool splitByLength; // Frame = mehrere Nachrichten, Byte 0 = Länge (LEGO LWP3)
        uint8_t armStops;   // Stopp-Pakete direkt nach dem Verbinden (JMC: Freischalten)
        uint16_t heartbeatMs;
        uint8_t frameLen;
        const uint8_t* stop;
    };
    static const Protocol JMC;
    static const Protocol LEGO;
    static constexpr size_t MAX_FRAME = 16;

    // Muss einmal nach NimBLEDevice::init() aufgerufen werden.
    static void beginAll();

    void start(int index);

    // Ziel setzen; bei geänderter MAC oder anderem Protokoll wird neu verbunden. Aus loop() aufrufen.
    void configure(const char* mac, bool enabled, const Protocol& proto);

    // Gewünschtes Paket (proto.frameLen Bytes); der Task sendet es sofort bei Änderung,
    // sonst alle proto.heartbeatMs.
    void setPacket(const uint8_t* pkt);

    State state() const { return state_; }
    int rssi() const { return rssi_; }
    uint32_t reconnects() const { return reconnects_; }

    static const char* stateName(State s);

    // BLE erlaubt nur einen Verbindungsaufbau bzw. Scan gleichzeitig.
    static SemaphoreHandle_t radioMutex;

private:
    static void taskEntry(void* arg);
    void run();
    bool connectOnce(const char* mac);
    bool write(const uint8_t* pkt);
    static void onNotify(NimBLERemoteCharacteristic* c, uint8_t* data, size_t len, bool isNotify);
    void dropConnection(bool sendStop);

    int index_ = 0;
    SemaphoreHandle_t lock_ = nullptr;

    // geschützt durch lock_
    char mac_[18] = "";
    bool enabled_ = false;
    const Protocol* proto_ = &JMC;
    uint32_t cfgGen_ = 0;
    uint8_t packet_[MAX_FRAME] = {};
    bool packetDirty_ = false;

    // nur im Task
    const Protocol* taskProto_ = &JMC;
    NimBLEClient* client_ = nullptr;
    NimBLERemoteCharacteristic* writeChar_ = nullptr;
    uint32_t seenGen_ = 0;
    uint32_t backoffMs_ = 0;
    uint32_t backoffUntil_ = 0;

    volatile State state_ = State::Off;
    volatile int rssi_ = 0;
    volatile uint32_t reconnects_ = 0;
};
