#pragma once

// Web-GUI und REST-API auf Port 80.
//   GET  /             Seite (web_index.h)
//   GET  /api/state    Live-Werte: Fahrregler, Hubs, Not-Stopp, WLAN (zählt als Lebenszeichen der GUI)
//   POST /api/input    Fahrregler setzen: {"ch":0-3, "speed":0-100, "reversed":bool} (nur Eingabe "web")
//   GET  /api/config   Einstellungen (ohne Passwörter)
//   POST /api/config   Einstellungen übernehmen und speichern
//   POST /api/scan     BLE-Scan (5 s) starten
//   GET  /api/scan     Scan-Status und gefundene Geräte
//   POST /api/estop    Not-Stopp auslösen
//   POST /api/restart  Neustart (für geänderte WLAN-Einstellungen)
//   POST /api/mkpair   Mould King: Connect-Telegramm 2 s senden (Einlernen)
//   POST /api/live     Live-Link mit Stud Rail Master (PC):
//                        {"name":"…"}      PC meldet sich an, ESP funkt (holt den Funk ggf. zurück)
//                        {"release":true}  Live-Link endet, ESP gibt den Funk an den PC ab
//                        {}                Funk zurückholen (Knopf in der ESP-GUI)
namespace webui {

void begin();
void tick();

}  // namespace webui
