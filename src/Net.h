#pragma once
#include <Arduino.h>

// WLAN: erst Heim-WLAN (falls eingetragen), nach 10 s ohne Verbindung eigener
// Access Point mit dem Gerätenamen (192.168.4.1). mDNS: http://<Gerätename>.local,
// Standard StudRailMasterQuadro (in der GUI einstellbar, Groß/Klein egal).
// OTA (ArduinoOTA, Port 3232): pio run -e ota -t upload; Passwort SECRET_OTA_PASS aus
// secrets.h, sonst das AP-Passwort.
namespace net {

void begin();
void tick();

const char* modeName();  // "verbindet", "WLAN", "Access Point"
String ip();

}  // namespace net
