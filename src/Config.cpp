#include "Config.h"
#include <Preferences.h>
#if __has_include("secrets.h")
#include "secrets.h"
#endif
#ifndef SECRET_WIFI_SSID
#define SECRET_WIFI_SSID ""
#define SECRET_WIFI_PASS ""
#endif

namespace cfg {

const char* typeName(HubType t) {
    switch (t) {
        case HubType::Mk4: return "mk4";
        case HubType::Lego: return "lego";
        default: return "jmc";
    }
}


static Config config;
static uint32_t rev = 1;

static const char* NVS_NS = "zugfern";
static const char* NVS_KEY = "config";
static const char* NVS_ARCHIVE = "archive";  // getrennt, damit kein Eintrag zu groß wird
static const char* DEFAULT_AP_PASS = "zugfern123";
static const char* DEFAULT_HOSTNAME = "StudRailMasterQuadro";

// Ohne SSID aus der GUI gilt das WLAN aus secrets.h
static void useSecretWifi(Config& c) {
    if (c.wifiSsid[0] != '\0') return;
    strlcpy(c.wifiSsid, SECRET_WIFI_SSID, sizeof(c.wifiSsid));
    strlcpy(c.wifiPass, SECRET_WIFI_PASS, sizeof(c.wifiPass));
}

static void setDefaults(Config& c) {
    memset(&c, 0, sizeof(c));
    for (int i = 0; i < MAX_HUBS; i++) snprintf(c.hubs[i].name, sizeof(c.hubs[i].name), "Hub %d", i + 1);
    // Bekannte Hubs aus dem alten Code
    c.hubs[0].enabled = true;
    strlcpy(c.hubs[0].mac, "a9:22:28:bc:3a:c7", sizeof(c.hubs[0].mac));
    c.hubs[0].routes[hub::PORT_A] = {1, false};
    strlcpy(c.hubs[1].mac, "13:12:05:04:ae:f2", sizeof(c.hubs[1].mac));
    strlcpy(c.apPass, DEFAULT_AP_PASS, sizeof(c.apPass));
    strlcpy(c.hostname, DEFAULT_HOSTNAME, sizeof(c.hostname));
    c.reverseMs = 5000;
    useSecretWifi(c);
}

// Hostname nach RFC 1123: 1–32 Zeichen, Buchstaben, Ziffern, Bindestrich (nicht am Rand)
static bool validHostname(const char* s) {
    size_t n = strlen(s);
    if (n == 0 || n > 32 || s[0] == '-' || s[n - 1] == '-') return false;
    for (size_t i = 0; i < n; i++) {
        if (!isalnum((unsigned char)s[i]) && s[i] != '-') return false;
    }
    return true;
}

static bool validMac(const char* s) {
    if (strlen(s) != 17) return false;
    for (int i = 0; i < 17; i++) {
        if (i % 3 == 2) {
            if (s[i] != ':') return false;
        } else if (!isxdigit((unsigned char)s[i])) {
            return false;
        }
    }
    return true;
}

// Liest einen Hub (aktiver Platz oder Archiv). Fehlende Felder behalten ihren Wert.
static bool parseHub(JsonObjectConst h, Hub& dst, const String& label, String& err) {
    if (h["name"].is<const char*>()) strlcpy(dst.name, h["name"], sizeof(dst.name));
    if (h["mac"].is<const char*>()) {
        String mac = h["mac"].as<const char*>();
        mac.trim();
        mac.toLowerCase();
        if (!mac.isEmpty() && !validMac(mac.c_str())) {
            err = "ungültige MAC bei " + label + ": " + mac;
            return false;
        }
        strlcpy(dst.mac, mac.c_str(), sizeof(dst.mac));
    }
    if (h["type"].is<const char*>()) {
        String t = h["type"].as<const char*>();
        if (t != "jmc" && t != "mk4" && t != "lego") {
            err = "unbekannter Hub-Typ bei " + label;
            return false;
        }
        dst.type = t == "mk4" ? HubType::Mk4 : t == "lego" ? HubType::Lego : HubType::Jmc;
    }
    if (!h["slot"].isNull()) {
        int slot = h["slot"] | -1;
        if (slot < 0 || slot >= mk::MK4_SLOTS) {
            err = "ungültiger Slot bei " + label;
            return false;
        }
        dst.slot = slot;
    }
    if (h["enabled"].is<bool>()) dst.enabled = h["enabled"];
    JsonArrayConst routes = h["routes"];
    for (size_t p = 0; p < routes.size() && p < hub::PORT_COUNT; p++) {
        int src = routes[p]["source"] | 0;
        if (src < 0 || src > 4) {
            err = "ungültige Regler-Nummer";
            return false;
        }
        dst.routes[p].source = src;
        dst.routes[p].invert = routes[p]["invert"] | false;
    }
    if (dst.type == HubType::Lego)  // City Hub hat nur A/B: C/D nicht von einem früheren Hub erben
        for (size_t p = lego::PORT_COUNT; p < hub::PORT_COUNT; p++) dst.routes[p] = {0, false};
    if (isGatt(dst.type) && dst.mac[0] == '\0') dst.enabled = false;
    return true;
}

// Liest JSON in c. Fehlende Felder behalten ihren bisherigen Wert.
static bool parse(JsonVariantConst j, Config& c, String& err) {
    if (j["input"].is<const char*>()) {
        String in = j["input"].as<const char*>();
        if (in != "web" && in != "hw") {
            err = "ungültige Eingabequelle";
            return false;
        }
        c.hardwareInput = in == "hw";
    }
    if (!j["reverseMs"].isNull()) {
        long ms = j["reverseMs"] | -1L;
        if (ms < 0 || ms > MAX_REVERSE_MS) {
            err = "Richtungswechsel: 0 bis " + String(MAX_REVERSE_MS / 1000) + " s";
            return false;
        }
        c.reverseMs = ms;
    }
    JsonArrayConst hubs = j["hubs"];
    if (hubs) {
        if (hubs.size() > MAX_HUBS) {
            err = "zu viele Hubs";
            return false;
        }
        for (size_t i = 0; i < hubs.size(); i++) {
            if (!parseHub(hubs[i], c.hubs[i], "Hub " + String(i + 1), err)) return false;
        }
        // Zwei MK4-Hubs auf demselben Slot würden dieselben Befehle bekommen
        for (int a = 0; a < MAX_HUBS; a++)
            for (int b = a + 1; b < MAX_HUBS; b++) {
                const Hub &ha = c.hubs[a], &hb = c.hubs[b];
                if (ha.enabled && hb.enabled && ha.type == HubType::Mk4 && hb.type == HubType::Mk4 &&
                    ha.slot == hb.slot) {
                    err = "Hub " + String(a + 1) + " und Hub " + String(b + 1) + " haben denselben Slot";
                    return false;
                }
            }
    }

    // Archiv wird immer als Ganzes ersetzt
    JsonArrayConst archive = j["archive"];
    if (archive) {
        if (archive.size() > MAX_ARCHIVE) {
            err = "Archiv voll (höchstens " + String(MAX_ARCHIVE) + " Hubs)";
            return false;
        }
        memset(c.archive, 0, sizeof(c.archive));
        for (size_t i = 0; i < archive.size(); i++) {
            if (!parseHub(archive[i], c.archive[i], "Archiv " + String(i + 1), err)) return false;
        }
        c.archiveCount = archive.size();
    }

    JsonObjectConst wifi = j["wifi"];
    if (wifi) {
        if (wifi["ssid"].is<const char*>()) strlcpy(c.wifiSsid, wifi["ssid"], sizeof(c.wifiSsid));
        // Leeres Passwortfeld in der GUI = unverändert lassen
        const char* pass = wifi["pass"] | "";
        if (pass[0]) strlcpy(c.wifiPass, pass, sizeof(c.wifiPass));
        if (wifi["clearPass"] | false) c.wifiPass[0] = '\0';
        const char* ap = wifi["apPass"] | "";
        if (ap[0]) {
            if (strlen(ap) < 8) {
                err = "AP-Passwort braucht mindestens 8 Zeichen";
                return false;
            }
            strlcpy(c.apPass, ap, sizeof(c.apPass));
        }
        if (wifi["host"].is<const char*>()) {
            const char* host = wifi["host"];
            if (!validHostname(host)) {
                err = "Gerätename: 1–32 Zeichen, nur Buchstaben, Ziffern und Bindestrich";
                return false;
            }
            strlcpy(c.hostname, host, sizeof(c.hostname));
        }
    }
    return true;
}

static void writeHub(const Hub& h, JsonObject o) {
    o["name"] = h.name;
    o["type"] = typeName(h.type);
    o["mac"] = h.mac;
    o["slot"] = h.slot;
    o["enabled"] = h.enabled;
    JsonArray routes = o["routes"].to<JsonArray>();
    for (const Route& r : h.routes) {
        JsonObject ro = routes.add<JsonObject>();
        ro["source"] = r.source;
        ro["invert"] = r.invert;
    }
}

static void writeArchive(const Config& c, JsonObject out) {
    JsonArray a = out["archive"].to<JsonArray>();
    for (int i = 0; i < c.archiveCount; i++) writeHub(c.archive[i], a.add<JsonObject>());
}

// Ohne Archiv (das hat einen eigenen NVS-Eintrag)
static void writeJson(const Config& c, JsonObject out, bool withSecrets) {
    out["input"] = c.hardwareInput ? "hw" : "web";
    out["reverseMs"] = c.reverseMs;
    JsonArray hubs = out["hubs"].to<JsonArray>();
    for (const Hub& h : c.hubs) writeHub(h, hubs.add<JsonObject>());
    JsonObject wifi = out["wifi"].to<JsonObject>();
    wifi["ssid"] = c.wifiSsid;
    wifi["host"] = c.hostname;
    if (withSecrets) {
        wifi["pass"] = c.wifiPass;
        wifi["apPass"] = c.apPass;
    } else {
        wifi["passSet"] = c.wifiPass[0] != '\0';
    }
}

const Config& get() { return config; }

uint32_t revision() { return rev; }

// Liest einen NVS-Eintrag (JSON) in config; false, wenn er fehlt oder defekt ist.
static bool loadKey(Preferences& prefs, const char* key) {
    String stored = prefs.isKey(key) ? prefs.getString(key) : String();
    if (stored.isEmpty()) return false;
    JsonDocument doc;
    String err;
    Config c = config;
    if (deserializeJson(doc, stored) != DeserializationError::Ok || !parse(doc.as<JsonVariantConst>(), c, err)) {
        Serial.printf("NVS-Eintrag \"%s\" defekt – ignoriert\n", key);
        return false;
    }
    config = c;
    return true;
}

static bool storeKey(Preferences& prefs, const char* key, JsonDocument& doc) {
    String s;
    serializeJson(doc, s);
    return prefs.putString(key, s) == s.length();
}

void load() {
    setDefaults(config);
    Preferences prefs;
    prefs.begin(NVS_NS, false);  // nicht read-only: legt den Namespace beim ersten Start an
    loadKey(prefs, NVS_KEY);
    loadKey(prefs, NVS_ARCHIVE);
    prefs.end();
    useSecretWifi(config);
    rev++;
}

bool update(JsonVariantConst json, String& err) {
    Config c = config;
    if (!parse(json, c, err)) return false;

    JsonDocument doc, arch;
    writeJson(c, doc.to<JsonObject>(), true);
    writeArchive(c, arch.to<JsonObject>());
    Preferences prefs;
    prefs.begin(NVS_NS, false);
    bool ok = storeKey(prefs, NVS_KEY, doc) && storeKey(prefs, NVS_ARCHIVE, arch);
    prefs.end();
    if (!ok) {
        err = "Speichern in NVS fehlgeschlagen";
        return false;
    }
    config = c;
    rev++;
    return true;
}

void toJson(JsonObject out) {
    writeJson(config, out, false);
    writeArchive(config, out);
}

}  // namespace cfg
