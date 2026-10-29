# Stückliste (BOM) Handgerät „Stud Rail Master Quadro“

> **Vorschau, ungetestet.** Die Stückliste passt zum Gehäuse in [gehaeuse/](gehaeuse/README.md). Das Gerät ist noch nicht komplett nachgebaut. Bezugsquellen stehen bewusst nicht dabei, alle Teile sind gängige Bastlerware.

## Elektronik

| Menge | Teil | Wert / Typ | Bauform | Anschluss / Bemerkung |
|---|---|---|---|---|
| 1 | ESP32-DevKit V1 | ESP32-WROOM-32, 30 Pins | Modul mit Micro-USB | liegt kopfüber im ESP-Halter, Micro-USB nach vorn |
| 4 | Schiebepoti | B103 (10 kΩ linear), 75 mm, 60 mm Weg, Hebel 15 mm | THT, 8 Pins + 2 Klemmlaschen | Schleifer an GPIO 34, 35, 32, 33 (nur ADC1); Enden an 3,3 V / GND |
| 4 | Kippschalter | Ein-Aus (SPST/SPDT), Gewinde M6 | Frontplattenmontage | Fahrtrichtung, gegen GND an GPIO 16–19 |
| 4 | LED | 5 mm | THT | Richtungsanzeige an GPIO 21, 22, 23, 25 |
| 4 | Widerstand | 330 Ω | THT 0,25 W | Vorwiderstand der Richtungs-LEDs |
| 2 | LED | 3 mm | THT | Status / Batterie |
| 1 | Taster | Cherry MX oder kompatibel, Plattenmontage | — | Not-Stopp, gegen GND an GPIO 27 |
| 5 | Kondensator | 100 nF | Keramik | je einer an den Potis (4) und am Not-Stopp (1) |
| 1 | Aufwärtswandler | MT3608-Modul | ca. 37 × 17 mm | Batterie → 5,0 V an den 5-V-Pin des DevKits. **Vor dem Anschließen auf 5,0 V einstellen.** |
| 1 | Schottky-Diode | SS14 | SMA (DO-214AC) | hinter dem MT3608 |
| 1 | Schalter Ein/Aus | Schiebeschalter | Wandöffnung 9 × 4,4 mm | trennt nur die Batterie |
| 1 | Batteriehalter | 4 × AA, max. 69 × 65 × 23 mm | — | Alkali oder NiMH, **kein Lithium** |
| 1 | Widerstand | 100 kΩ | THT | Batteriemessung (Teiler an GPIO 36) |
| 1 | Widerstand | 68 kΩ | THT | Batteriemessung |
| 1 | Kondensator | 100 nF | Keramik | am Messeingang |

### IR-Sender (für IR-Hubs, GPIO 26)

| Menge | Teil | Wert / Typ | Bauform | Bemerkung |
|---|---|---|---|---|
| 1 | MOSFET | AO3400A (Logic Level) | SOT-23 | Low-Side-Schalter |
| 1 | Widerstand | 100 Ω | | Gate |
| 1 | Widerstand | 100 kΩ | | Pull-down am Gate (LEDs beim Booten aus) |
| 4 | IR-LED | 940 nm, 5 mm (1 × TSAL6100, 3 × TSAL6200) | THT | im IR-Block hinter der Stirnwand |
| 4 | Widerstand | 47 Ω, 1 W | 2512 oder THT | je LED einer, direkt an der Batteriespannung |
| 1 | Elko | 470 µF / 16 V | | an der LED-Versorgung |
| 1 | Kondensator | 100 nF | Keramik | an der LED-Versorgung |

## Gehäuse: Kaufteile

| Menge | Teil | Wofür |
|---|---|---|
| 13 | Gewindeeinsatz M3, Bohrung Ø 4,0 mm, Länge 4–5 mm | 4 Oberschale, 4 Säulen Fader-Rahmen, 2 Batteriedeckel, 2 ESP-Halter, 1 MT3608-Halter |
| 4 | Schraube M3 × 10, Zylinder- oder Linsenkopf | Gehäuse von unten |
| 4 | Schraube M3 × 6 | Fader-Rahmen auf die Säulen |
| 2 | Schraube M3 × 6, Linsenkopf | Batteriedeckel |
| 3 | Schraube M3 × 8, Senkkopf | ESP- und MT3608-Halter von unten |
| 4 | Klebefuß Ø 8–10 mm | Boden |
| 1 | IR-durchlässiges Acryl, 1,5 mm, 62 × 15 mm | Fenster vor den IR-LEDs |
| — | Litze, Schrumpfschlauch | Verdrahtung, eine Platine gibt es nicht |

## Gehäuse: Druckteile

Siehe [gehaeuse/README.md](gehaeuse/README.md#druckteile): Unterschale, Oberschale, Frontplatte, Batteriedeckel, Zierring, 4 Faderknöpfe, Not-Stopp-Kappe, ESP-Halter, MT3608-Halter, Fader-Rahmen.
