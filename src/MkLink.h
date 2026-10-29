#pragma once
#include <MouldKing.h>

// Sender für alle Mould-King-4.0-Hubs: ein gemeinsames Telegramm (3 Slots × 4 Ports) als
// nicht verbindbare BLE-Werbung alle 100 ms. Keine Verbindung, kein Task – läuft aus loop().
// Der Hub hat einen Watchdog: Hört die Werbung auf (Neustart, OTA), bleiben die Motoren stehen.
namespace mklink {

// Aus control::tick(): active = mindestens ein MK4-Hub aktiv; levels[slot * 4 + port] = −7…7.
// Beim Einschalten der Werbung wird zuerst 2 s lang das Connect-Telegramm gesendet.
void update(bool active, const int8_t levels[mk::MK4_SLOTS * mk::MK4_PORTS]);

// Connect-Telegramm 2 s lang senden: Hubs, die gerade eingeschaltet wurden, lernen die Kennung.
void pair();

bool active();
bool pairing();

}  // namespace mklink
