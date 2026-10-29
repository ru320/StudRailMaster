#include "Net.h"
#include <ArduinoOTA.h>
#include <ESPmDNS.h>
#include <WiFi.h>
#include "Config.h"
#include "Control.h"
#if __has_include("secrets.h")
#include "secrets.h"
#endif

namespace net {

static constexpr uint32_t STA_TIMEOUT_MS = 10000;
// Gerätename aus der Config: mDNS (<name>.local), DHCP, OTA und Name des Access Points
static const char* hostname() { return cfg::get().hostname; }

enum class Mode { CONNECTING, STA, AP };
static Mode mode = Mode::CONNECTING;
static uint32_t startedAt = 0;
static bool otaStarted = false;

// Kein Watchdog im JMC-Hub: vor dem Update Not-Stopp und Stopp-Pakete abwarten,
// denn während der Übertragung läuft loop() nicht.
static void otaBegin() {
    control::triggerEstop();
    Serial.println("OTA-Update: Not-Stopp, warte auf Stopp-Pakete");
    uint32_t t = millis();
    while (millis() - t < 500) {
        control::tick();
        delay(5);
    }
}

static void startOta() {
    if (otaStarted) return;
    ArduinoOTA.setHostname(hostname());
    ArduinoOTA.setMdnsEnabled(false);  // mDNS macht startMdns()
#ifdef SECRET_OTA_PASS
    ArduinoOTA.setPassword(SECRET_OTA_PASS);
#else
    ArduinoOTA.setPassword(cfg::get().apPass);
#endif
    ArduinoOTA.onStart(otaBegin);
    ArduinoOTA.onEnd([] { Serial.println("OTA-Update fertig, Neustart"); });
    ArduinoOTA.onError([](ota_error_t e) { Serial.printf("OTA-Update fehlgeschlagen (%u)\n", e); });
    ArduinoOTA.begin();
    otaStarted = true;
}

static void startMdns() {
    MDNS.end();
    if (MDNS.begin(hostname())) {
        MDNS.addService("http", "tcp", 80);
        MDNS.addService("arduino", "tcp", 3232);
    }
    startOta();
}

static void startAp() {
    const cfg::Config& c = cfg::get();
    if (WiFi.getMode() & WIFI_STA) WiFi.disconnect(true);
    WiFi.mode(WIFI_AP);
    WiFi.softAP(c.hostname, c.apPass);
    mode = Mode::AP;
    startMdns();
    Serial.printf("Access Point \"%s\" aktiv, http://%s\n", c.hostname, WiFi.softAPIP().toString().c_str());
}

void begin() {
    const cfg::Config& c = cfg::get();
    WiFi.setHostname(c.hostname);
    if (c.wifiSsid[0] == '\0') {
        startAp();
        return;
    }
    WiFi.mode(WIFI_STA);
    WiFi.begin(c.wifiSsid, c.wifiPass);
    startedAt = millis();
    mode = Mode::CONNECTING;
    Serial.printf("Verbinde mit WLAN \"%s\" ...\n", c.wifiSsid);
}

void tick() {
    if (otaStarted) ArduinoOTA.handle();
    if (mode != Mode::CONNECTING) return;
    if (WiFi.status() == WL_CONNECTED) {
        mode = Mode::STA;
        startMdns();
        Serial.printf("WLAN verbunden, http://%s bzw. http://%s.local\n", WiFi.localIP().toString().c_str(),
                      hostname());
    } else if (millis() - startedAt > STA_TIMEOUT_MS) {
        Serial.println("WLAN nicht erreichbar");
        startAp();
    }
}

const char* modeName() {
    switch (mode) {
        case Mode::CONNECTING: return "verbindet";
        case Mode::STA: return "WLAN";
        case Mode::AP: return "Access Point";
    }
    return "?";
}

String ip() {
    if (mode == Mode::AP) return WiFi.softAPIP().toString();
    if (mode == Mode::STA) return WiFi.localIP().toString();
    return "";
}

}  // namespace net
