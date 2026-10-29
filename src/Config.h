#pragma once
#include <ArduinoJson.h>
#include <HubProtocol.h>
#include <LegoHub.h>
#include <MouldKing.h>

// Persistente Einstellungen (NVS, als JSON).
namespace cfg {

constexpr uint16_t MAX_REVERSE_MS = 20000;

constexpr int MAX_HUBS = 4;      // gleichzeitig aktiv (je ein HubLink-Task bzw. MK-Slot)
constexpr int MAX_ARCHIVE = 16;  // gespeicherte, gerade nicht benutzte Hubs

struct Route {
    uint8_t source;  // 0 = keins, 1…4 = Fahrregler
    bool invert;     // Richtung umpolen
};

enum class HubType : uint8_t {
    Jmc,  // BLE-Verbindung, Paket per GATT (HubProtocol, HubLink)
    Mk4,  // Mould King 4.0, nur Werbung (MouldKing, MkLink)
    Lego, // LEGO Powered Up City Hub, BLE-Verbindung, LWP3 (LegoHub, HubLink), Ports A/B
};

// Typen mit BLE-Verbindung (MAC nötig, ein HubLink je Hub)
inline bool isGatt(HubType t) { return t == HubType::Jmc || t == HubType::Lego; }
const char* typeName(HubType t);

struct Hub {
    bool enabled;
    HubType type;  // fehlt im JSON = Jmc
    char name[24];
    char mac[18];  // nur Jmc/Lego: "aa:bb:cc:dd:ee:ff", leer = unbenutzt
    uint8_t slot;  // nur Mk4: 0…2, per Taste am Hub gewählt
    Route routes[hub::PORT_COUNT];
};

struct Config {
    bool hardwareInput;  // false = Schieberegler in der GUI, true = Potis/Schalter am ESP
    uint16_t reverseMs;  // Richtungswechsel während der Fahrt: Dauer voll vor → voll zurück, 0 = hart
    Hub hubs[MAX_HUBS];
    Hub archive[MAX_ARCHIVE];  // eigener NVS-Eintrag; enabled hat hier keine Bedeutung
    uint8_t archiveCount;
    char wifiSsid[33];
    char wifiPass[65];
    char apPass[65];
    char hostname[33];  // mDNS/WLAN/AP-Name, Groß/Klein egal (mDNS vergleicht ohne)
};

const Config& get();

// Erhöht sich bei jeder Änderung – damit erkennen Module neue Einstellungen.
uint32_t revision();

void load();

// Prüft und übernimmt JSON aus der GUI, speichert in NVS. err enthält ggf. den Grund.
bool update(JsonVariantConst json, String& err);

// Für die GUI (mit Archiv); Passwörter werden nicht ausgegeben.
void toJson(JsonObject out);

}  // namespace cfg
