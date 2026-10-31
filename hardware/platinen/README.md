# Platinen Handgerät „Stud Rail Master Quadro“

> **Entwurf, ungetestet.** Beide Platinen sind platziert und gegen das Gehäuse geprüft, aber noch nicht gefertigt. Vor der Bestellung die Punkte unter [Vor der Bestellung prüfen](#vor-der-bestellung-prüfen) abhaken.

Zwei Platinen, 2 Lagen, 1,6 mm FR4, Masse auf beiden Seiten als Fläche:

| Platine | Größe | Inhalt |
|---|---|---|
| [Fader-Platine](fader/) | 91 × 91 mm | 4 Schiebepotis B103 75 mm, je 1 k + 100 nF am Schleifer, Stecker zur Hauptplatine |
| [Hauptplatine](hauptplatine/) | 100 × 52 mm | ESP32-DevKit V1 (30 Pin, kopfüber darunter), MT3608-Modul (unten), 1N5819, Batteriemessung, IR-Treiber, LED-Widerstände, Stecker für alles am Gehäuse, Anschluss für ein 2,4-GHz-Funkmodul |

Je Platine liegen Schaltplan (`.kicad_sch`), Platine (`.kicad_pcb`) und Projekt (`.kicad_pro`) im Ordner. Eigene Footprints (Fader, MT3608-Modul) stehen in [`ZugFern.pretty/`](ZugFern.pretty/).

## Im Gehäuse

- **Fader-Platine:** Sie sitzt auf den 4 Säulen unter der Frontplatte (4 × M3 × 6 in Gewindeeinsätze). Die Fader drücken mit ihrer Oberseite gegen die Frontplatte. Der Stecker J1 sitzt **unten** auf der Platine.
- **Hauptplatine:** Sie liegt waagrecht im linken hinteren Teil der Unterschale, 12,4 mm über dem Boden, auf 4 eigenen Säulen (4 × M3 × 6 von oben).
  - Das ESP32-DevKit hängt kopfüber darunter: Seine Stiftleisten stecken von unten durch die Platine und werden oben verlötet. Die Platine liegt dabei auf dem Kunststoff der Stiftleisten auf.
  - Die Micro-USB-Buchse zeigt nach vorn auf das Langloch in der Stirnwand.
  - Über der WLAN/BLE-Antenne des ESP32 ist die Platine ausgespart.
  - Das MT3608-Modul hängt an 4 Drahtbeinchen (abgeschnittene Bauteilbeine) etwa 2 mm unter der Platine, Bauteilseite nach unten.

## Stecker (JST XH, 2,5 mm)

| Stecker | Pins | Wohin |
|---|---|---|
| J1 (Fader-Platine) ↔ J4 (Hauptplatine) | 1 +3V3, 2 GND, 3–6 Regler 1–4 | Kabel 1:1, 6-polig |
| J3 | 1 VSYS, 2 GND | 4 × AA über den Ein/Aus-Schalter an der linken Wand |
| J5–J8 | 1 Schalter, 2 LED-Anode, 3 GND | Regler 1–4: Kippschalter (Mitte → Pin 1, ein Außenanschluss → GND) und Richtungs-LED |
| J9 | 1 Not-Stopp, 2 GND | Cherry-MX-Schalter |
| J10 | 1 Status-LED, 2 Batterie-LED, 3 GND | die beiden 3-mm-LEDs neben dem Not-Stopp (Anoden an 1/2) |
| J11 | 1–4 Anoden IR1–IR4, 5 gemeinsame Kathode | IR-LEDs im IR-Block (IR1 = TSAL6100 Mitte, IR2/IR3 = TSAL6200 ±30°, IR4 = TSAL6200 45° nach oben) |
| J12 | wie nRF24L01+ (1 GND, 2 3V3, 3 CE, 4 CSN, 5 SCK, 6 MOSI, 7 MISO, 8 IRQ) | Funkmodul nRF24L01+ im Funk-Halter unter dem Not-Stopp, 8 Dupont-Kabel Buchse–Buchse |

## Kabel

Vorschlag für Farben und Querschnitte (so sind die Kabel auch im CAD-Modell gezogen):

| Farbe | Wofür | Querschnitt |
|---|---|---|
| rot | Plus: Batterie, VSYS, +3V3 zur Fader-Platine | 0,25 mm² (AWG 24) für Batterie/VSYS, sonst 0,14 mm² |
| schwarz | GND, gemeinsame Kathode der IR-LEDs | 0,25 mm² für Batterie und IR-Kathode, sonst 0,14 mm² |
| gelb | Regler (Fader-Kabel) und Kippschalter | 0,14 mm² (AWG 26) |
| grün | LED-Anoden (Richtung, Status, Batterie) | 0,14 mm² |
| blau | Not-Stopp, IR-Anoden | 0,14 mm² |

- Die Kathoden der Richtungs-LEDs bekommen eine kurze schwarze Brücke zum GND-Anschluss des Kippschalters.
- Die IR-Kathoden sind als Kette verbunden, ebenso die Kathoden der Status- und der Batterie-LED.
- JST-XH-Crimpkontakte nehmen AWG 22–28.

## Pinbelegung ESP32

Wie in `src/Pins.h`, dazu neu:

| Funktion | GPIO |
|---|---|
| Batterie-LED | 12 (LED mit 330 Ω gegen GND hält den Strapping-Pin beim Booten auf LOW, wie er sein muss) |
| 2,4-GHz-Modul: SCK, MOSI, MISO, CSN, CE, IRQ | 14, 13, 39, 5, 4, 15 |
| Batteriespannung (VSYS × 0,405) | 36 |
| IR-Sender | 26 |

Für die Batterie-LED, die Batteriemessung, den IR-Sender und das Funkmodul fehlt die Firmware noch.

## Bestückung

Nur Durchsteckmontage, keine SMD-Teile: Widerstände 0207 liegend, Keramik-Scheibenkondensatoren RM 2,5, Elko radial, 1N5819 (DO-41), BC337 (TO-92) als IR-Treiber.

1. **MT3608 vorher einstellen:** an 5 V Labornetzteil oder 4 × AA, Poti drehen bis 5,0 V am Ausgang.
2. Hauptplatine: zuerst die flachen Teile (Widerstände, Diode, Kondensatoren, BC337), dann Elko C1 (Ø 8 mm, max. 12 mm hoch), JST-Stecker und J12. Die Beinchen von J5 und D1 liegen über dem DevKit: auf 1 mm kürzen.
3. MT3608 mit 4 Drahtbeinchen unten anlöten (Bauteilseite nach unten, ca. 2 mm Abstand).
4. ESP32-DevKit von unten einstecken, Platine plan auf die Stiftleisten drücken, oben verlöten. Danach lässt sich das DevKit nur noch mit Entlötlitze tauschen.
5. Fader-Platine: R und C, dann die Fader. Die Haltelaschen durch die Löcher stecken, verdrehen und verlöten. J1 auf die Unterseite.

## Vor der Bestellung prüfen

- [ ] **Fader:** Die Platine auf 1:1 ausdrucken (KiCad: Drucken, Maßstab 1) und einen Fader auflegen. Das Pinbild stammt aus dem Datenblatt (Raster 2,5 mm, Enden 70 mm auseinander). Das 3D-Modell eines anderen Herstellers hatte 2,7 mm und 73,2 mm. Liegen die Pins anders, `Fader_B103_75mm_Dual` in `tools/gen_platinen.py` anpassen.
- [ ] **0 % am richtigen Ende:** Pin 3 (GND) liegt am Nutzer-Ende. Zeigt der Regler verkehrt herum an, Pin 1 und 3 tauschen.
- [ ] **ESP32-DevKit:** Die Pinfolge mit dem eigenen Board vergleichen. Es gibt 30-Pin-Varianten mit anderer Reihenfolge. Die Reihen liegen 25,4 mm auseinander.
- [ ] **MT3608-Modul:** Die Lage der 4 Anschlüsse am eigenen Modul messen. Die Langlöcher gleichen ± 1 mm aus.
- [ ] **Säulen und Langloch:** Erst die Unterschale drucken und die bestückte Hauptplatine mit ESP probehalber einsetzen.

## Bearbeiten

Die Dateien lassen sich direkt in KiCad 10 öffnen (`.kicad_pro`). Werden Lage oder Umriss der Platinen geändert, müssen Säulen und Aussparungen im Gehäuse mitziehen ([gehaeuse/](../gehaeuse/README.md)).

*In Herbrechtingen ist es immer am schönsten!*
