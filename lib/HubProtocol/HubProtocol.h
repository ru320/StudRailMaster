#pragma once
#include <stddef.h>
#include <stdint.h>

// Paketformat des BLE-Motor-Hubs (Service fff0, Characteristic fff2).
// Abgeleitet aus einem Mitschnitt der Original-App:
//
//   Index:  0  1  2  3  4  5    6      7    8      9  10
//           5A 6B 02 00 05 dirAB spdAB dirCD spdCD 01 CS
//
// Richtungsbits: A/C vor 0x01, zurück 0x02; B/D vor 0x08, zurück 0x04.
// A+B bzw. C+D teilen sich je ein Speed-Byte.
// CS = Summe der Bytes 0..9, untere 8 Bit.
namespace hub {

constexpr size_t PACKET_LEN = 11;
constexpr size_t PORT_COUNT = 4;

enum Port : uint8_t { PORT_A = 0, PORT_B = 1, PORT_C = 2, PORT_D = 3 };

// Sollwert für einen Port: dir -1 = zurück, 0 = Stopp, +1 = vor.
struct PortCmd {
    int8_t  dir;
    uint8_t speed;
};

// Prüfsumme über len Bytes (Summe, untere 8 Bit).
uint8_t checksum(const uint8_t* data, size_t len);

// Baut ein komplettes Paket für alle vier Ports.
// Laufen beide Ports eines Paares (A/B oder C/D), gilt der größere Speed für beide.
void buildPacket(const PortCmd cmds[PORT_COUNT], uint8_t out[PACKET_LEN]);

// Baut ein Paket aus den rohen Nutzbytes 5..8 (für Tests/Probe).
void buildRaw(uint8_t dirAB, uint8_t spdAB, uint8_t dirCD, uint8_t spdCD, uint8_t out[PACKET_LEN]);

// Richtungsbit eines Ports, 0 bei dir == 0.
uint8_t dirBits(Port port, int8_t dir);

constexpr uint8_t MIN_SPEED = 0x10;  // Motor läuft laut Hardwaretest ab 0x10 an

// Betrag 1…100 % → MIN_SPEED…255, 0 → 0.
uint8_t speedFromPercent(int percent);

// Sollwerte −100…100 für A–D → Paket. Gleiche Funktion wie encode() im Python-Treiber
// (app/studrailmaster/drivers/jmc.py), beide geprüft gegen drivers/jmc.json.
void encodePercent(const int percent[PORT_COUNT], uint8_t out[PACKET_LEN]);

}  // namespace hub
