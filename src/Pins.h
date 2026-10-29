#pragma once
#include <stdint.h>

// Pinbelegung ESP32-DevKit (ESP32-WROOM-32E). Nur relevant für Eingabe "Hardware".
// Potis nur an ADC1 – ADC2 ist bei aktivem WLAN nicht nutzbar.
namespace pins {

constexpr int CHANNELS = 4;

constexpr uint8_t POTI[CHANNELS] = {34, 35, 32, 33};     // Poti 1–4 (0–100 %)
constexpr uint8_t SWITCH[CHANNELS] = {16, 17, 18, 19};   // Richtungsschalter gegen GND, interner Pull-up
constexpr uint8_t DIR_LED[CHANNELS] = {21, 22, 23, 25};  // leuchtet bei umgekehrter Richtung

constexpr uint8_t ESTOP = 27;  // Not-Stopp-Taster gegen GND, interner Pull-up
constexpr uint8_t LED = 2;     // Onboard-LED (Status)

}  // namespace pins
