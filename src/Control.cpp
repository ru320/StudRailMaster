#include "Control.h"
#include "Inputs.h"
#include "MkLink.h"
#include "Pins.h"

namespace control {

static constexpr uint32_t TICK_MS = 20;
static constexpr uint32_t WEB_TIMEOUT_MS = 2000;

static HubLink links[cfg::MAX_HUBS];
static int values[cfg::MAX_HUBS][hub::PORT_COUNT];
static bool estop = true;  // Anfahrsperre nach dem Einschalten
static uint32_t lastTick = 0;
static uint32_t seenRev = 0;
static uint32_t lastWebSeen = 0;
static bool released = false;    // Funk an den PC abgegeben
static uint32_t releaseAt = 0;   // Abgabe nach den Stopp-Paketen
static bool seenReleased = false;

// Weicher Richtungswechsel je Fahrregler: wirksamer Wert −100…100 und ob gerade gewechselt wird
static float rampVal[pins::CHANNELS] = {};
static bool ramping[pins::CHANNELS] = {};
static int chOut[pins::CHANNELS] = {};

// Folgt dem Sollwert direkt, außer bei Richtungswechsel während der Fahrt: dann läuft der Wert
// mit fester Rate (200 % in reverseMs) über 0 auf den Sollwert in der neuen Richtung.
static int rampTo(int ch, int target, uint32_t dtMs, uint16_t reverseMs) {
    float& v = rampVal[ch];
    if (reverseMs == 0) {
        ramping[ch] = false;
        return (int)(v = target);
    }
    if (!ramping[ch] && v * target < 0) ramping[ch] = true;
    if (ramping[ch]) {
        float step = 200.0f * dtMs / reverseMs;
        // Nach dem Nulldurchgang: Sollwert in gleicher Richtung, aber kleiner → sofort übernehmen
        if (v * target > 0 && fabsf((float)target) <= fabsf(v)) {
            v = target;
        } else if (fabsf(target - v) <= step) {
            v = target;
        } else {
            v += target > v ? step : -step;
        }
        if (v == target) ramping[ch] = false;
    } else {
        v = target;
    }
    return (int)lroundf(v);
}

// Stehen alle Fahrregler, die irgendwo benutzt werden, auf 0?
static bool usedChannelsAtZero(const cfg::Config& c) {
    for (const cfg::Hub& h : c.hubs) {
        if (!h.enabled) continue;
        for (const cfg::Route& r : h.routes) {
            if (r.source && inputs::speed(r.source - 1) != 0) return false;
        }
    }
    return true;
}

void begin() {
    HubLink::beginAll();
    for (int i = 0; i < cfg::MAX_HUBS; i++) links[i].start(i);
}

void triggerEstop() {
    if (!estop) Serial.println("NOT-STOPP");
    estop = true;
    inputs::zeroWeb();
    // Rampe sofort auf 0: Bei Eingabe Web ist die Sperre im nächsten Takt schon wieder frei
    // (Regler stehen auf 0), ein laufender Richtungswechsel würde sonst langsam auslaufen.
    for (int ch = 0; ch < pins::CHANNELS; ch++) {
        rampVal[ch] = 0;
        ramping[ch] = false;
    }
}

void releaseRadio() {
    if (released || releaseAt) return;
    triggerEstop();
    releaseAt = millis() + 500;  // kein Watchdog im JMC-Hub: erst Stopp-Pakete, dann trennen
    if (!releaseAt) releaseAt = 1;
    Serial.println("Live-Link beendet: Funk wird an den PC abgegeben");
}

void takeRadio() {
    if (!released && !releaseAt) return;
    triggerEstop();
    released = false;
    releaseAt = 0;
    Serial.println("Funk zurück am ESP");
}

bool radioReleased() { return released || releaseAt; }

void webAlive() { lastWebSeen = millis(); }

bool estopActive() { return estop; }

HubLink& link(int index) { return links[index]; }

int portValue(int hubIndex, int port) { return values[hubIndex][port]; }

int channelValue(int ch) { return chOut[ch]; }

bool pairConflict(int hubIndex, int pair) {
    const cfg::Hub& h = cfg::get().hubs[hubIndex];
    if (h.type != cfg::HubType::Jmc) return false;  // nur der JMC-Hub hat gemeinsame Speed-Bytes
    const cfg::Route* r = h.routes;
    uint8_t a = r[pair * 2].source, b = r[pair * 2 + 1].source;
    return a && b && a != b;
}

void tick() {
    if (inputs::estopPressed()) triggerEstop();

    uint32_t now = millis();
    if (now - lastTick < TICK_MS) return;
    uint32_t dt = lastTick ? now - lastTick : TICK_MS;
    lastTick = now;

    if (releaseAt && (int32_t)(now - releaseAt) >= 0) {
        releaseAt = 0;
        released = true;
        Serial.println("Funk abgegeben, die Hubs fährt jetzt der PC");
    }

    const cfg::Config& c = cfg::get();
    if (cfg::revision() != seenRev || released != seenReleased) {
        seenRev = cfg::revision();
        seenReleased = released;
        inputs::setSource(c.hardwareInput ? inputs::Source::Hardware : inputs::Source::Web);
        for (int i = 0; i < cfg::MAX_HUBS; i++)
            links[i].configure(c.hubs[i].mac, c.hubs[i].enabled && cfg::isGatt(c.hubs[i].type) && !released,
                               c.hubs[i].type == cfg::HubType::Lego ? HubLink::LEGO : HubLink::JMC);
    }

    // Kein Watchdog im Hub: verschwindet die GUI (Handy weg, WLAN weg), stoppen wir selbst
    if (inputs::source() == inputs::Source::Web && !usedChannelsAtZero(c) && now - lastWebSeen > WEB_TIMEOUT_MS) {
        Serial.println("GUI antwortet nicht mehr");
        triggerEstop();
    }

    // Solange der Funk abgegeben ist, bleibt die Sperre: Die Hubs gehören dem PC
    if (estop && usedChannelsAtZero(c) && !radioReleased()) {
        estop = false;
        Serial.println("Freigabe: alle Fahrregler auf 0");
    }

    int chVal[pins::CHANNELS];
    for (int ch = 0; ch < pins::CHANNELS; ch++) {
        if (estop) {  // Not-Stopp wirkt sofort, ohne Rampe
            rampVal[ch] = 0;
            ramping[ch] = false;
        }
        chVal[ch] = chOut[ch] = rampTo(ch, estop ? 0 : inputs::value(ch), dt, c.reverseMs);
    }

    bool mkActive = false;
    int8_t mkLevels[mk::MK4_SLOTS * mk::MK4_PORTS] = {};
    for (int h = 0; h < cfg::MAX_HUBS; h++) {
        const cfg::Hub& hubCfg = c.hubs[h];
        const bool mk4 = hubCfg.type == cfg::HubType::Mk4;
        if (mk4 && hubCfg.enabled) mkActive = true;
        for (int p = 0; p < (int)hub::PORT_COUNT; p++) {
            const cfg::Route& r = hubCfg.routes[p];
            int v = (!estop && hubCfg.enabled && r.source) ? chVal[r.source - 1] : 0;
            if (r.invert) v = -v;
            values[h][p] = v;
            if (mk4 && hubCfg.enabled) mkLevels[hubCfg.slot * mk::MK4_PORTS + p] = mk::mk4Level(v);
        }
        if (mk4) continue;
        if (hubCfg.type == cfg::HubType::Lego) {
            uint8_t frame[lego::FRAME_LEN];
            lego::encodePercent(values[h], frame);  // nur A/B
            links[h].setPacket(frame);
        } else {
            uint8_t pkt[hub::PACKET_LEN];
            hub::encodePercent(values[h], pkt);
            links[h].setPacket(pkt);
        }
    }
    mklink::update(mkActive && !released, mkLevels);
}

}  // namespace control
