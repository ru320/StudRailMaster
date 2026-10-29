#include "WebUi.h"
#include <ArduinoJson.h>
#include <NimBLEDevice.h>
#include <WebServer.h>
#include "Control.h"
#include "MkLink.h"
#include "Inputs.h"
#include "Net.h"
#include "web_index.h"

namespace webui {

static constexpr uint32_t SCAN_MS = 5000;
static constexpr uint32_t RESTART_DELAY_MS = 500;  // Zeit für die Stopp-Pakete

static WebServer server(80);

static bool scanRequested = false;
static bool scanRunning = false;
static JsonDocument scanResults;
static uint32_t restartAt = 0;

// Live-Link: angemeldeter PC (Stud Rail Master); gilt als da, solange er /api/state abfragt
static constexpr uint32_t PC_TIMEOUT_MS = 3000;
static String pcName;
static IPAddress pcIp;
static uint32_t pcSeen = 0;
static bool pcPresent = false;

static void sendJson(int code, const JsonDocument& doc) {
    String out;
    serializeJson(doc, out);
    server.send(code, "application/json", out);
}

static void sendError(int code, const String& msg) {
    JsonDocument doc;
    doc["error"] = msg;
    sendJson(code, doc);
}

static void handleState() {
    control::webAlive();
    if (pcName.length() && !control::radioReleased() && server.client().remoteIP() == pcIp) {
        pcSeen = millis();
        if (!pcPresent) Serial.printf("Live-Link: %s (%s) ist da\n", pcName.c_str(), pcIp.toString().c_str());
        pcPresent = true;
    }
    JsonDocument doc;
    doc["estop"] = control::estopActive();
    doc["radio"] = control::radioReleased() ? "pc" : "esp";
    if (pcName.length()) {
        JsonObject pc = doc["pc"].to<JsonObject>();
        pc["name"] = pcName;
        pc["ip"] = pcIp.toString();
        pc["online"] = pcPresent;
    }
    doc["input"] = inputs::source() == inputs::Source::Hardware ? "hw" : "web";
    JsonArray channels = doc["channels"].to<JsonArray>();
    for (int i = 0; i < pins::CHANNELS; i++) {
        JsonObject ch = channels.add<JsonObject>();
        ch["speed"] = inputs::speed(i);
        ch["reversed"] = inputs::reversed(i);
        ch["raw"] = inputs::potiRaw(i);
        ch["value"] = control::channelValue(i);
    }
    JsonArray hubs = doc["hubs"].to<JsonArray>();
    for (int h = 0; h < cfg::MAX_HUBS; h++) {
        HubLink& l = control::link(h);
        const cfg::Hub& hc = cfg::get().hubs[h];
        JsonObject o = hubs.add<JsonObject>();
        if (hc.enabled && control::radioReleased()) {
            o["state"] = "beim PC";  // Live-Link beendet, der PC fährt diesen Hub
            o["ready"] = false;
            o["rssi"] = 0;
            o["reconnects"] = l.reconnects();
        } else if (hc.type == cfg::HubType::Mk4) {
            // Nur Werbung, keine Rückmeldung vom Hub
            o["state"] = !hc.enabled ? "aus" : mklink::pairing() ? "lernt ein" : mklink::active() ? "sendet" : "Fehler";
            o["ready"] = hc.enabled && mklink::active() && !mklink::pairing();
            o["rssi"] = 0;
            o["reconnects"] = 0;
        } else {
            o["state"] = HubLink::stateName(l.state());
            o["ready"] = l.state() == HubLink::State::Ready;
            o["rssi"] = l.rssi();
            o["reconnects"] = l.reconnects();
        }
        JsonArray ports = o["ports"].to<JsonArray>();
        for (int p = 0; p < (int)hub::PORT_COUNT; p++) ports.add(control::portValue(h, p));
        JsonArray conflicts = o["pairConflict"].to<JsonArray>();
        conflicts.add(control::pairConflict(h, 0));
        conflicts.add(control::pairConflict(h, 1));
    }
    JsonObject n = doc["net"].to<JsonObject>();
    n["mode"] = net::modeName();
    n["ip"] = net::ip();
    doc["heap"] = ESP.getFreeHeap();
    doc["uptime"] = millis() / 1000;
    sendJson(200, doc);
}

static void handleGetConfig() {
    JsonDocument doc;
    cfg::toJson(doc.to<JsonObject>());
    sendJson(200, doc);
}

static void handlePostConfig() {
    JsonDocument doc;
    if (deserializeJson(doc, server.arg("plain")) != DeserializationError::Ok) {
        sendError(400, "ungültiges JSON");
        return;
    }
    String err;
    if (!cfg::update(doc.as<JsonVariantConst>(), err)) {
        sendError(400, err);
        return;
    }
    handleGetConfig();
}

static void handleStartScan() {
    if (!scanRunning) scanRequested = true;
    server.send(202, "application/json", "{}");
}

static void handleGetScan() {
    JsonDocument doc;
    doc["running"] = scanRunning || scanRequested;
    doc["devices"] = scanResults.as<JsonArrayConst>();
    sendJson(200, doc);
}

static void handleInput() {
    control::webAlive();
    JsonDocument doc;
    if (deserializeJson(doc, server.arg("plain")) != DeserializationError::Ok) {
        sendError(400, "ungültiges JSON");
        return;
    }
    if (inputs::source() != inputs::Source::Web) {
        sendError(409, "Eingabe steht auf Hardware");
        return;
    }
    int ch = doc["ch"] | -1;
    if (ch < 0 || ch >= pins::CHANNELS) {
        sendError(400, "ungültiger Kanal");
        return;
    }
    inputs::setWeb(ch, doc["speed"] | inputs::speed(ch), doc["reversed"] | inputs::reversed(ch));
    server.send(200, "application/json", "{}");
}

static void handleEstop() {
    control::triggerEstop();
    server.send(200, "application/json", "{}");
}

static void handleMkPair() {
    mklink::pair();
    server.send(200, "application/json", "{}");
}

static void handleLive() {
    JsonDocument doc;
    if (deserializeJson(doc, server.arg("plain")) != DeserializationError::Ok) {
        sendError(400, "ungültiges JSON");
        return;
    }
    if (doc["release"] | false) {
        control::releaseRadio();
        // PC bleibt eingetragen, damit die GUI zeigt, an wen der Funk ging
        pcIp = server.client().remoteIP();
        if (!pcName.length()) pcName = "PC";
        pcPresent = false;
    } else {
        control::takeRadio();
        const char* name = doc["name"] | "";
        if (name[0]) {
            pcName = String(name).substring(0, 40);
            pcIp = server.client().remoteIP();
            pcSeen = millis();
            pcPresent = true;
            Serial.printf("Live-Link gestartet von %s (%s)\n", pcName.c_str(), pcIp.toString().c_str());
        } else {
            pcName = "";  // am ESP zurückgeholt
            pcPresent = false;
        }
    }
    server.send(200, "application/json", "{}");
}

static void handleRestart() {
    control::triggerEstop();
    restartAt = millis() + RESTART_DELAY_MS;
    server.send(200, "application/json", "{}");
}

static void tickScan() {
    NimBLEScan* scan = NimBLEDevice::getScan();
    if (scanRequested) {
        // Kein Blockieren von loop(): läuft gerade ein Verbindungsaufbau, später nochmal versuchen
        if (xSemaphoreTake(HubLink::radioMutex, 0) != pdTRUE) return;
        scanRequested = false;
        scan->setActiveScan(true);
        scan->setInterval(100);
        scan->setWindow(60);
        scan->clearResults();
        if (scan->start(SCAN_MS, false, true)) {
            scanRunning = true;
        } else {
            xSemaphoreGive(HubLink::radioMutex);
        }
        return;
    }
    if (!scanRunning || scan->isScanning()) return;

    scanRunning = false;
    NimBLEScanResults res = scan->getResults();
    JsonArray list = scanResults.to<JsonArray>();
    for (int i = 0; i < res.getCount(); i++) {
        const NimBLEAdvertisedDevice* d = res.getDevice(i);
        if (!d->haveName()) continue;  // Hubs melden sich mit Namen (z. B. JG_JMC-C734)
        JsonObject o = list.add<JsonObject>();
        o["mac"] = d->getAddress().toString();
        o["name"] = d->getName();
        o["rssi"] = d->getRSSI();
        o["public"] = d->getAddress().getType() == BLE_ADDR_PUBLIC;
        // LEGO wirbt mit Service 1623 (Name frei wählbar), JMC nur mit Namen
        static const NimBLEUUID LEGO_SERVICE(HubLink::LEGO.service);
        o["type"] = d->isAdvertisingService(LEGO_SERVICE) ? "lego"
                    : d->getName().rfind("JG_JMC", 0) == 0 ? "jmc" : "";
    }
    scan->clearResults();
    xSemaphoreGive(HubLink::radioMutex);
}

void begin() {
    server.on("/", HTTP_GET, [] {
        server.sendHeader("Content-Encoding", "gzip");
        server.send_P(200, "text/html; charset=utf-8", (PGM_P)WEB_INDEX_GZ, WEB_INDEX_GZ_LEN);
    });
    server.on("/api/state", HTTP_GET, handleState);
    server.on("/api/config", HTTP_GET, handleGetConfig);
    server.on("/api/config", HTTP_POST, handlePostConfig);
    server.on("/api/scan", HTTP_POST, handleStartScan);
    server.on("/api/scan", HTTP_GET, handleGetScan);
    server.on("/api/input", HTTP_POST, handleInput);
    server.on("/api/estop", HTTP_POST, handleEstop);
    server.on("/api/restart", HTTP_POST, handleRestart);
    server.on("/api/mkpair", HTTP_POST, handleMkPair);
    server.on("/api/live", HTTP_POST, handleLive);
    server.onNotFound([] { server.send(404, "text/plain", "nicht gefunden"); });
    scanResults.to<JsonArray>();
    server.begin();
}

void tick() {
    server.handleClient();
    tickScan();
    if (pcPresent && !control::radioReleased() && millis() - pcSeen > PC_TIMEOUT_MS) {
        pcPresent = false;
        Serial.printf("Live-Link: %s meldet sich nicht mehr\n", pcName.c_str());
    }
    if (restartAt && (int32_t)(millis() - restartAt) >= 0) ESP.restart();
}

}  // namespace webui
