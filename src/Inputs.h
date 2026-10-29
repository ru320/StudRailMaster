#pragma once
#include "Pins.h"

// Fahrregler: 4 Kanäle, je Geschwindigkeit 0–100 % und Richtungsschalter.
// Quelle ist entweder die Web-GUI (Schieberegler) oder Hardware (Poti + Schalter).
// Die Richtungs-LEDs werden in beiden Fällen angesteuert.
namespace inputs {

enum class Source : uint8_t { Web, Hardware };

constexpr int DEADBAND = 3;  // Hardware-Poti: unter 3 % gilt als 0

void begin();
void tick();

void setSource(Source s);
Source source();

// Geschwindigkeit 0…100.
int speed(int ch);
// Richtungsschalter umgelegt (= LED an).
bool reversed(int ch);
// Sollwert −100…100 (negativ = Schalter umgelegt).
int value(int ch);

// Rohwert 0…4095 des Hardware-Potis (für die GUI).
int potiRaw(int ch);

// Werte aus der GUI; wirkt nur bei Quelle Web.
void setWeb(int ch, int speed, bool reversed);
// Alle Web-Regler auf 0 (Not-Stopp).
void zeroWeb();

// true genau einmal pro Druck auf den Not-Stopp-Taster.
bool estopPressed();

}  // namespace inputs
