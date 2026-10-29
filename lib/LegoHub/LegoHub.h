#pragma once
#include <stddef.h>
#include <stdint.h>

// LEGO Powered Up City Hub (88009), LEGO Wireless Protocol 3.0 (LWP3) über GATT
// (Service 1623, Characteristic 1624). Eine Nachricht je Port:
//
//   Index:  0    1    2    3     4    5    6    7
//           08   00   81   port  11   51   00   power (int8 −100…100, 0 = auslaufen)
//
// Ein Frame sind beide Nachrichten hintereinander; Byte 0 jeder Nachricht ist ihre Länge,
// HubLink schreibt sie einzeln. Gleiche Funktionen wie app/studrailmaster/drivers/lego.py,
// beide geprüft gegen drivers/lego.json.
namespace lego {

constexpr size_t PORT_COUNT = 2;  // A, B
constexpr size_t MSG_LEN = 8;
constexpr size_t FRAME_LEN = PORT_COUNT * MSG_LEN;

// Sollwert −100…100 → LWP3-Leistung (gleich, nur begrenzt).
int8_t power(int percent);

// Sollwerte −100…100 für A, B → Frame aus zwei Nachrichten.
void encodePercent(const int percent[PORT_COUNT], uint8_t out[FRAME_LEN]);

}  // namespace lego
