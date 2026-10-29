#include "Inputs.h"
#include <Arduino.h>

namespace inputs {

static constexpr uint32_t SAMPLE_MS = 10;
static constexpr uint32_t DEBOUNCE_MS = 30;
static constexpr int HYSTERESIS = 2;

struct Debounce {
    bool stable = false;  // true = gegen GND geschaltet
    bool lastRaw = false;
    uint32_t changedAt = 0;

    // Gibt true zurück, wenn sich der entprellte Zustand geändert hat.
    bool update(bool raw, uint32_t now) {
        if (raw != lastRaw) {
            lastRaw = raw;
            changedAt = now;
        } else if (raw != stable && now - changedAt >= DEBOUNCE_MS) {
            stable = raw;
            return true;
        }
        return false;
    }
};

static Source src = Source::Web;
static bool hwStarted = false;

static int speeds[pins::CHANNELS];
static bool revs[pins::CHANNELS];
static float filtered[pins::CHANNELS];
static Debounce switches[pins::CHANNELS];

static Debounce estopButton;
static bool estopEdge = false;
static uint32_t lastSample = 0;

// Rohwert → 0…100 mit Totzone am unteren Anschlag.
static int toPercent(float raw) {
    float pct = raw / 4095.0f * 100.0f;
    if (pct < DEADBAND) return 0;
    int scaled = (int)lroundf((pct - DEADBAND) * 100.0f / (100.0f - DEADBAND));
    return constrain(scaled, 1, 100);
}

static void startHardware() {
    analogReadResolution(12);
    for (int i = 0; i < pins::CHANNELS; i++) {
        analogRead(pins::POTI[i]);  // konfiguriert den Pin als ADC-Kanal
        analogSetPinAttenuation(pins::POTI[i], ADC_11db);
        filtered[i] = analogRead(pins::POTI[i]);
        pinMode(pins::SWITCH[i], INPUT_PULLUP);
    }
    hwStarted = true;
}

void begin() {
    for (int i = 0; i < pins::CHANNELS; i++) {
        pinMode(pins::DIR_LED[i], OUTPUT);
        digitalWrite(pins::DIR_LED[i], LOW);
    }
    pinMode(pins::ESTOP, INPUT_PULLUP);
}

void setSource(Source s) {
    if (s == src) return;
    src = s;
    // Beim Umschalten nie mit einem alten Wert weiterfahren
    for (int i = 0; i < pins::CHANNELS; i++) {
        speeds[i] = 0;
        revs[i] = false;
    }
    if (s == Source::Hardware && !hwStarted) startHardware();
}

Source source() { return src; }

void tick() {
    uint32_t now = millis();

    if (estopButton.update(digitalRead(pins::ESTOP) == LOW, now) && estopButton.stable) estopEdge = true;

    if (src == Source::Hardware && now - lastSample >= SAMPLE_MS) {
        lastSample = now;
        for (int i = 0; i < pins::CHANNELS; i++) {
            int sum = 0;
            for (int s = 0; s < 4; s++) sum += analogRead(pins::POTI[i]);
            filtered[i] += (sum / 4.0f - filtered[i]) * 0.25f;
            int v = toPercent(filtered[i]);
            // Hysterese gegen Zappeln; 0 und 100 immer sofort übernehmen
            if (v == 0 || v == 100 || abs(v - speeds[i]) >= HYSTERESIS) speeds[i] = v;

            switches[i].update(digitalRead(pins::SWITCH[i]) == LOW, now);
            revs[i] = switches[i].stable;
        }
    }

    for (int i = 0; i < pins::CHANNELS; i++) digitalWrite(pins::DIR_LED[i], revs[i]);
}

int speed(int ch) { return speeds[ch]; }

bool reversed(int ch) { return revs[ch]; }

int value(int ch) { return revs[ch] ? -speeds[ch] : speeds[ch]; }

int potiRaw(int ch) { return hwStarted ? (int)filtered[ch] : 0; }

void setWeb(int ch, int spd, bool rev) {
    if (src != Source::Web || ch < 0 || ch >= pins::CHANNELS) return;
    speeds[ch] = constrain(spd, 0, 100);
    revs[ch] = rev;
}

void zeroWeb() {
    if (src != Source::Web) return;
    for (int i = 0; i < pins::CHANNELS; i++) speeds[i] = 0;
}

bool estopPressed() {
    bool e = estopEdge;
    estopEdge = false;
    return e;
}

}  // namespace inputs
