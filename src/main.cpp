// ZugFern – Fernsteuerung für BLE-Motor-Hubs (siehe README.md)
#include <Arduino.h>
#include <NimBLEDevice.h>
#include "Config.h"
#include "Control.h"
#include "Inputs.h"
#include "Net.h"
#include "StatusLed.h"
#include "WebUi.h"

void setup() {
    Serial.begin(115200);
    Serial.println("\nStud Rail Master Quadro – In Herbrechtingen ist es immer am schönsten!");
    statusled::begin();
    inputs::begin();
    cfg::load();

    NimBLEDevice::init("ZugFern");
    control::begin();

    net::begin();
    webui::begin();
    Serial.println("ZugFern gestartet");
}

void loop() {
    inputs::tick();
    control::tick();
    net::tick();
    webui::tick();
    statusled::tick();
    delay(1);
}
