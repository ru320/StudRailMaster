#pragma once
#include <stddef.h>
#include <stdint.h>

// Mould-King-Hubs (MK 4.0) werden ohne Verbindung über BLE-Werbung gesteuert:
// Flags 02 01 02 + Herstellerdaten (Company-ID 0xFFF0) mit 24 verschlüsselten Bytes.
// Abgeleitet aus dem HCI-Mitschnitt der App „MK Tech“ und
// https://github.com/J0EK3R/mkconnect-python (MouldKingCrypt).
//
// Klartext MK 4.0:
//   Connect  AD id0 id1 80 80 80 chk 52
//   Fahren   7D id0 id1 [6 Byte, ein Nibble pro Kanal] 82
// Ein Telegramm steuert 3 Slots × 4 Ports (Slot per Taste am Hub, nach dem Einschalten 0).
// Nibble: 8 = Stopp, 9…F = vorwärts Stufe 1…7, 1…7 = rückwärts Stufe 1…7 (7 = voll rückwärts,
// am Hub geprüft 28.10.2026; wie mkconnect-python, moldqueen hat es falsch).
namespace mk {

constexpr uint16_t COMPANY_ID = 0xFFF0;
constexpr size_t CRYPT_LEN = 24;  // verschlüsselte Herstellerdaten
constexpr size_t ADV_LEN = 31;    // komplette Werbedaten (Flags + Herstellerdaten)

constexpr int MK4_SLOTS = 3;
constexpr int MK4_PORTS = 4;
constexpr int MK4_LEVELS = 7;  // Stufen je Richtung
constexpr size_t MK4_CONNECT_LEN = 8;
constexpr size_t MK4_DATA_LEN = 10;

// Kennung in Byte 1–2; der Hub lernt sie per Connect. chk ist Byte 6 im Connect und gehört
// fest zur Kennung (Regel unbekannt), darum nur Paare aus Mitschnitten verwenden.
struct Id {
    uint8_t id0, id1, chk;
};
constexpr Id ID_MKTECH_A = {0x25, 0x95, 0xE7};  // eigener Mitschnitt MK Tech
constexpr Id ID_MOLDQUEEN = {0xAE, 0x18, 0xF3};  // github.com/jrichter24/moldqueen

// Verschlüsselt len Bytes Klartext (len ≤ 14) zu 24 Bytes Herstellerdaten.
void crypt(const uint8_t* raw, size_t len, uint8_t out[CRYPT_LEN]);

// Komplette Werbedaten: 02 01 02 1B FF F0 FF + crypt(raw).
void advData(const uint8_t* raw, size_t len, uint8_t out[ADV_LEN]);

void mk4Connect(const Id& id, uint8_t out[MK4_CONNECT_LEN]);

// levels[slot * 4 + port] = −7…7
void mk4Data(const Id& id, const int8_t levels[MK4_SLOTS * MK4_PORTS], uint8_t out[MK4_DATA_LEN]);

// Prozent −100…100 → Stufe −7…7; jeder Wert ≠ 0 ergibt mindestens Stufe 1.
int8_t mk4Level(int percent);

}  // namespace mk
