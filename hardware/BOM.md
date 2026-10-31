# Stückliste (BOM) Handgerät „Stud Rail Master Quadro“

> **Entwurf, ungetestet.** Automatisch erzeugt aus den Schaltplänen in [platinen/](platinen/README.md) und dem Gehäusemodell in [gehaeuse/](gehaeuse/README.md). Bezugsquellen stehen bewusst nicht dabei, alle Teile sind gängige Bastlerware.

## Platinen

| Menge | Platine | Größe | Fertigung |
|---|---|---|---|
| 1 | Fader-Platine | 91 × 91 mm, 2 Lagen, 1,6 mm FR4 | `platinen/fader/fertigung/Fader-Platine_gerber.zip` |
| 1 | Hauptplatine | 100 × 52 mm, 2 Lagen, 1,6 mm FR4 | `platinen/hauptplatine/fertigung/Hauptplatine_gerber.zip` |

## Bestückung Fader-Platine

| Menge | Teil | Wert / Typ | Bauform | Referenz | Hinweis |
|---|---|---|---|---|---|
| 4 | Kondensator | 100 nF | Keramik-Scheibe, RM 2,5 | C1, C2, C3, C4 |  |
| 1 | Stecker | 6-polig | JST XH B6B-XH-A, stehend | J1 |  |
| 4 | Widerstand | 1 kΩ | axial 0207, liegend, RM 7,62 | R1, R2, R3, R4 |  |
| 4 | Schiebepoti | B103 (10 kΩ linear), 75 mm, 60 mm Weg | THT, 6 Pins + 2 Laschen | RV1, RV2, RV3, RV4 |  |

## Bestückung Hauptplatine

| Menge | Teil | Wert / Typ | Bauform | Referenz | Hinweis |
|---|---|---|---|---|---|
| 1 | Elko | 470 µF / 10 V | radial Ø 8 mm, RM 3,5 | C1 | max. 12 mm hoch |
| 5 | Kondensator | 100 nF | Keramik-Scheibe, RM 2,5 | C2, C5, C7, C8, C10 |  |
| 1 | Kondensator | 10 µF | Keramik-Scheibe, RM 2,5 | C9 | Vielschicht-Keramik (MLCC), radial |
| 1 | Schottky-Diode | 1N5819 | DO-41, liegend, RM 10,16 | D1 | hinter dem MT3608 |
| 2 | Stecker | 2-polig | JST XH B2B-XH-A, stehend | J3, J9 |  |
| 1 | Stecker | 6-polig | JST XH B6B-XH-A, stehend | J4 |  |
| 5 | Stecker | 3-polig | JST XH B3B-XH-A, stehend | J5, J6, J7, J8, J10 |  |
| 1 | Stecker | 5-polig | JST XH B5B-XH-A, stehend | J11 |  |
| 1 | Stiftleiste | 2,4 GHz (nRF24L01+) | axial 0207, stehend, RM 2,54 | J12 |  |
| 1 | NPN-Transistor | BC337 (800 mA) | TO-92 | Q1 |  |
| 1 | Widerstand | 100 kΩ | axial 0207, liegend, RM 7,62 | R3 |  |
| 1 | Widerstand | 68 kΩ | axial 0207, liegend, RM 7,62 | R4 |  |
| 5 | Widerstand | 330 Ω | axial 0207, liegend, RM 7,62 | R11, R12, R13, R14, R20 |  |
| 1 | Widerstand | 10 kΩ | axial 0207, liegend, RM 7,62 | R21 |  |
| 4 | Widerstand | 47 Ω, 0,6 W (Metallschicht) | axial 0207, liegend, RM 10,16 | R22, R23, R24, R25 | übersteht einen hängenden IR-Ausgang (0,47 W) |
| 2 | Widerstand | 330 Ω | axial 0207, stehend, RM 2,54 | R30, R31 |  |
| 1 | Aufwärtswandler | MT3608, **vor dem Einbau auf 5,0 V** | Modul ca. 37 × 17 mm | U1 | an Drahtbeinchen unter der Platine |

Die Stiftleisten J1/J2 der Hauptplatine sind die des ESP32-DevKits (siehe unten), die Befestigungslöcher H1–H4 sind keine Bauteile.

## Teile am Gehäuse (über Kabel angeschlossen)

| Menge | Teil | Wert / Typ | Anschluss | Hinweis |
|---|---|---|---|---|
| 1 | ESP32-DevKit V1 | ESP32-WROOM-32, 30 Pins, Micro-USB | Stiftleisten durch die Hauptplatine gelötet | kopfüber, Micro-USB nach vorn; Pinfolge prüfen |
| 4 | Kippschalter | Ein-Aus (SPST/SPDT), Gewinde M6, Körper ca. 13 × 8 mm | J5–J8 | Fahrtrichtung |
| 4 | LED | 5 mm, rot | J5–J8 | Richtungsanzeige |
| 2 | LED | 3 mm | J10 | Status / Batterie |
| 1 | Taster | Cherry MX oder kompatibel, Plattenmontage | J9 | Not-Stopp |
| 1 | IR-LED | TSAL6100, 940 nm, 5 mm | J11 (IR1) | Mitte, geradeaus |
| 3 | IR-LED | TSAL6200, 940 nm, 5 mm | J11 (IR2–IR4) | ±30° seitlich, 45° nach oben |
| 1 | Schalter Ein/Aus | Schiebeschalter, Wandöffnung 9 × 4,4 mm | zwischen Batterie und J3 | trennt nur die Batterie |
| 1 | Batteriehalter | 4 × AA, max. 69 × 65 × 23 mm | J3 | Alkali oder NiMH, **kein Lithium** |
| 1 | Funkmodul 2,4 GHz | nRF24L01+ mit Leiterbahn-Antenne, ohne Verstärker, 15 × 29 mm | J12 (8 Dupont-Kabel) | steht im Funk-Halter unter dem Not-Stopp; für BlueBrixx-Hubs, Firmware fehlt noch |

## Stecker und Kabel

| Menge | Teil | Wofür |
|---|---|---|
| 2 | JST-XH-Buchsengehäuse 2-polig (XHP-2) | Gegenstück zu B2B-XH-A |
| 5 | JST-XH-Buchsengehäuse 3-polig (XHP-3) | Gegenstück zu B3B-XH-A |
| 1 | JST-XH-Buchsengehäuse 5-polig (XHP-5) | Gegenstück zu B5B-XH-A |
| 2 | JST-XH-Buchsengehäuse 6-polig (XHP-6) | Gegenstück zu B6B-XH-A |
| 36 (+10) | JST-XH-Crimpkontakte (SXH-001T-P0.6) | für AWG 22–28 |
| 0,7 m | Litze 0,14 mm² (AWG 26), blau | 5 Kabel, im Modell 0,46 m, dazu 50 % Reserve |
| 0,8 m | Litze 0,14 mm² (AWG 26), gelb | 8 Kabel, im Modell 0,47 m, dazu 50 % Reserve |
| 0,9 m | Litze 0,14 mm² (AWG 26), grün | 6 Kabel, im Modell 0,54 m, dazu 50 % Reserve |
| 0,1 m | Litze 0,14 mm² (AWG 26), rot | 1 Kabel, im Modell 0,07 m, dazu 50 % Reserve |
| 1,6 m | Litze 0,14 mm² (AWG 26), schwarz | 15 Kabel, im Modell 1,05 m, dazu 50 % Reserve |
| 0,5 m | Litze 0,25 mm² (AWG 24), rot | 2 Kabel, im Modell 0,31 m, dazu 50 % Reserve |
| 0,4 m | Litze 0,25 mm² (AWG 24), schwarz | 2 Kabel, im Modell 0,23 m, dazu 50 % Reserve |
| 8 | Dupont-Kabel Buchse–Buchse, 30 cm (Flachkabel, einzeln abziehbar; Weg im Gehäuse ca. 20 cm) | J12 ↔ Funkmodul; Farben wie oben (schwarz GND, rot 3,3 V, gelb CE/CSN, grün SCK/MOSI, blau MISO/IRQ) |
| — | Schrumpfschlauch 1,6 / 2,4 mm | Lötstellen an Schaltern und LEDs |
| — | Kapton-Band | Rückseite des DevKits unter den gekürzten Beinchen von J5 und D1 |

## Gehäuse: Kaufteile

| Menge | Teil | Wofür |
|---|---|---|
| 16 | Gewindeeinsatz M3, Bohrung Ø 4,0 mm, Länge 4–5 mm | 4 Oberschale, 4 Säulen Fader-Platine, 4 Säulen Hauptplatine, 2 Batteriedeckel, 2 Funk-Halter |
| 4 | Schraube M3 × 10, Zylinder- oder Linsenkopf | Gehäuse von unten |
| 8 | Schraube M3 × 6 | Fader-Platine und Hauptplatine auf die Säulen |
| 2 | Schraube M3 × 6, Linsenkopf | Batteriedeckel |
| 2 | Schraube M3 × 8, Senkkopf | Funk-Halter von unten |
| 4 | Klebefuß Ø 8–10 mm | Boden |
| 1 | IR-durchlässiges Acryl, 1,5 mm, 62 × 15 mm | Fenster vor den IR-LEDs |

## Gehäuse: Druckteile

Siehe [gehaeuse/README.md](gehaeuse/README.md#druckteile): Unterschale, Oberschale, Frontplatte, Batteriedeckel, Zierring, 4 Faderknöpfe, Not-Stopp-Kappe, Funk-Halter.

*In Herbrechtingen ist es immer am schönsten!*
