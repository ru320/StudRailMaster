# Gehäuse Handgerät „Stud Rail Master Quadro“

> **Vorschau, ungetestet.** Das Gehäuse ist am Rechner fertig konstruiert und auf Kollisionen geprüft, aber noch nicht gedruckt und zusammengebaut. Maße von Zukaufteilen (Cherry-MX-Stößel, Kippschalter, Ein/Aus-Schalter) vor dem Druck am eigenen Teil prüfen.

![Vorschau](vorschau.png)

Ein Pult-Gehäuse (180 × 180 mm, 22 → 46 mm hoch) für die ESP32-Fernsteuerung: 4 Schiebepotis, 4 Kippschalter mit LED, Not-Stopp (Cherry MX), IR-Sender nach vorn, 4 × AA. Gedacht für FDM-Drucker ab 185 × 185 mm Bauraum (entwickelt für einen Elegoo Neptune 4 Pro). **Jedes Teil lässt sich einfarbig drucken.**

## Dateien

| Datei | Inhalt |
|---|---|
| `quadro_oeffentlich.sc` | parametrisches Modell für [SolidCraft](https://docs.solidcraft.io/) (Zeitleiste + Parametertabelle) |
| `quadro_oeffentlich.step` | alle Teile im Zusammenbau, für jedes andere CAD |
| `druck/*.stl` | Druckteile, schon richtig aufs Bett gelegt |
| `vorschau.png`, `vorschau_ir.png` | Ansichten (Oberschale halbdurchsichtig; die Elektronik darin ist nur angedeutet) |
| `schrift/` | Barlow Condensed Bold (SIL Open Font License) für die Beschriftung |
| [`../BOM.md`](../BOM.md) | Stückliste: Elektronik, Kaufteile, Schrauben |

## Ändern

`quadro_oeffentlich.sc` in SolidCraft öffnen. Unter **Parameter** stehen alle Maße mit Kommentar, zum Beispiel:

| Parameter | Bedeutung |
|---|---|
| `Breite`, `Tiefe`, `H_Nutzer`, `H_IR` | Außenmaße und Pultneigung |
| `Wand`, `Spiel` | Wandstärke, Luft zwischen gesteckten Teilen |
| `Fader_Weg`, `Hebel_D`, `Hebel_B`, `Lasche_A` | Schiebepoti (Weg, Hebel, Klemmlaschen) |
| `MX_Kreuz`, `Kappe_Unten` | Höhe der Not-Stopp-Kappe über dem Cherry MX |
| `Fach_B`, `Fach_T`, `Fach_H` | Batteriefach (innen) |
| `USB_Z` | Höhe des Micro-USB-Langlochs |
| `Ring_H`, `Ring_Ueber` | Zierring |
| `Rund_Aussen`, `Rund_Fuge` | Kantenverrundungen |

Nach einer Änderung baut sich die Zeitleiste neu auf. Danach die Körper einzeln als STL exportieren und im Slicer aufs Bett legen (Oberschale: Pultseite nach unten; Frontplatte, Fader-Rahmen, Knöpfe und Kappe liegen im Modell schräg).

## Druckteile

| Datei | Anzahl | Farbe (Vorschlag) | Lage | Hinweis |
|---|---|---|---|---|
| `unterschale.stl` | 1 | Anthrazit | Boden unten | Fach-Auflagerahmen 3 mm überhängend, geht ohne Stützen |
| `oberschale.stl` | 1 | Anthrazit | Pultseite unten | keine Stützen nötig |
| `frontplatte.stl` | 1 | Anthrazit | flach, Schrift oben | einfarbig, oder Farbwechsel nach Höhe (siehe unten) |
| `frontplatte_platte.stl` + `_weiss` + `_gelb` | je 1 | Anthrazit / Weiß / Gelb | flach | dieselbe Frontplatte in drei Teilen für den Mehrfarbdruck |
| `batteriedeckel.stl` | 1 | Anthrazit | Außenseite unten | |
| `zierring.stl` | 1 | Orange/Gelb | flach | die farbige Kante in der Fuge |
| `faderknopf_1.stl` | **4** | Orange/Gelb | Oberseite unten | |
| `notstopp_kappe.stl` | 1 | Rot | Oberseite unten | |
| `esp_halter.stl` | 1 | beliebig | Boden unten | ESP32-DevKit liegt kopfüber darin |
| `mt3608_halter.stl` | 1 | beliebig | Boden unten | mit Tasche für die Diode SS14 |
| `fader_rahmen.stl` | 1 | beliebig | flach | hält die 4 Schiebepotis |

PLA oder PETG, Düse 0,4 mm, Schicht 0,2 mm, mindestens 3 Wände, Füllung 15–20 %.

### Beschriftung farbig (optional)

Die Schrift steht erhaben auf der Frontplatte (Platte 2,4 mm; gelb +0,4 mm: Logo-Noppen, „QUADRO“, Striche unter den Nummern; weiß +0,8 mm: übrige Schrift und Skalen). Einfarbig gedruckt ist sie als Prägung lesbar.

- **Einfach:** In OrcaSlicer zwei Pausen bzw. Farbwechsel setzen: bei 2,4 mm auf Gelb, bei 2,8 mm auf Weiß. Die weißen Buchstaben haben dann unten 0,4 mm Gelb, das man nur an der Kante sieht.
- **Sauber, auch mit einem Einzelextruder:** `frontplatte_platte.stl`, `frontplatte_weiss.stl` und `frontplatte_gelb.stl` gleichzeitig in OrcaSlicer ziehen und als *ein Objekt mit mehreren Teilen* laden (die Teile passen genau aufeinander). Jedem Teil ein Filament zuweisen und im Druckerprofil „Single Extruder Multi Material“ einschalten. Der Slicer setzt dann nur in den obersten 4 Schichten Filamentwechsel (rund 4–5 Wechsel von Hand).

## Aufbau

- **Frontplatte von unten eingesetzt:** Sie liegt unter dem Rahmen der Oberschale, der sie 6,5 mm überdeckt.
- **4 Klemmsäulen** der Unterschale drücken die Frontplatte gegen den Rahmen. Die Dome der Oberschale greifen durch Aussparungen am Plattenrand in die Säulen. **4 × M3 × 10 von unten** halten Unterschale, Zierring, Frontplatte und Oberschale zusammen. Von außen ist oben keine Schraube zu sehen.
- **Zierring:** Er liegt in der Fuge über die ganze Wandbreite und wird eingeklemmt. Innen führt ihn der Zentrierrand der Unterschale. Er steht 0,4 mm über die Wand und ist nirgends unterbrochen.
- **Schiebepotis (B103, 75 mm, 60 mm Weg)** sitzen im **Fader-Rahmen**:
  - Ihre zwei Klemmlaschen stecken durch Schlitze und werden darunter verdreht, wie auf einer Platine. Dort ist der Rahmen auf 1,6 mm ausgedünnt.
  - Die Lötpins ragen durch Fenster, angeschlossen wird mit Litze.
  - Der Rahmen ist auf 4 Säulen geschraubt und drückt die Fader gegen die Frontplatte.
- **Not-Stopp:** Cherry MX rastet in die Frontplatte ein (14 × 14 mm bei 1,5 mm Plattenstärke). Die rote Kappe läuft in einer Führungsbuchse und kann nicht kippen.
- **ESP32-DevKit** liegt kopfüber (Pins oben) im ESP-Halter links. Die **Micro-USB-Buchse** zeigt nach vorn auf ein Langloch 12 × 8 mm unter dem Zierring. Darüber laufen Strom und Programmieren.
- **Stromversorgung:** 4 × AA → Ein/Aus → MT3608 (auf **5,0 V** einstellen, *bevor* der ESP angeschlossen wird) → Diode SS14 → 5-V-Pin des DevKits. Die SS14 sitzt in einer Tasche am MT3608-Halter.
- **Batteriefach** rechts, innen 65,5 × 70 × 23,5 mm, für einen Halter 4 × AA bis 69 × 65 × 23 mm. Den Halter unter den Auflagerahmen kleben. Der Deckel wird von unten verschraubt.
- **IR-Sender:** Ein Block innen an der Stirnwand nimmt 4 IR-LEDs (5 mm) auf: eine geradeaus, zwei je 30° seitlich, eine 45° nach oben. Außen gibt es eine Mulde für 1,5 mm IR-Acryl (62 × 15 mm).

## Zusammenbau

1. Gewindeeinsätze M3 setzen:
   - Oberschale: 4 Dome, von unten
   - Unterschale: 4 Säulen für den Fader-Rahmen, 2 am Batteriedeckel
   - ESP-Halter: 2
   - MT3608-Halter: 1
2. Fader in den Rahmen stecken, Laschen verdrehen, Litzen anlöten. Den Rahmen auf die Säulen schrauben (4 × M3 × 6).
3. ESP-Halter und MT3608-Halter von unten anschrauben (Senkkopf M3 × 8). ESP und MT3608 einrasten, die SS14 in die Tasche legen. Den Batteriehalter unter den Auflagerahmen kleben. Verdrahten.
4. In der Frontplatte Kippschalter (Mutter oben), LEDs und den MX-Schalter montieren. Die IR-LEDs in den Block der Oberschale stecken, das IR-Acryl außen einkleben.
5. Frontplatte von unten in die Oberschale legen, die Aussparungen kommen um die Dome.
6. Zierring auf die Unterschale legen. Oberschale aufsetzen und dabei die Fader-Hebel durch die Schlitze führen. Mit 4 × M3 × 10 von unten verschrauben.
7. Faderknöpfe aufstecken, Not-Stopp-Kappe aufdrücken, Batteriedeckel anschrauben, Klebefüße in die Mulden.

## Vor dem Druck prüfen

- **Not-Stopp-Kappe** zuerst allein drucken und auf den MX-Schalter stecken. `MX_Kreuz` (10,5 mm) ist die angenommene Höhe der Kappenaufnahme über der Platte.
- **Faderknopf** auf einen Fader stecken. Die Aufnahme misst 1,5 × 4,3 mm, der Hebel 1,2 × 4 mm.
- **Fader-Rahmen:** Passen die Klemmlaschen in die Schlitze (`Lasche_A` = 25 mm von der Mitte)?
- **Kippschalter:** Das Modell geht von 13 × 8 × 10 mm Körper und M6-Gewinde aus.
- Tipp: Erst einen Streifen der Frontplatte mit einem Kanal und dem Not-Stopp drucken. Dafür in OrcaSlicer schneiden.
