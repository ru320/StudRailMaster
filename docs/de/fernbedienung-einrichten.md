# Fernbedienung einrichten

🇬🇧 [English](../en/remote-setup.md) · [Anleitung](anleitung.md) · [Zusammen mit dem PC](esp-abgleich.md) · [README](../../README.de.md)

Die Fernbedienung **Stud Rail Master Quadro** ist ein ESP32 mit eigener Firmware. Sie fährt bis zu vier Hubs ganz ohne Computer. Eingestellt wird sie über eine Webseite, die du im Browser am Handy oder am PC öffnest.

Für den Anfang reicht ein **nacktes ESP32-DevKit**. Die Fahrhebel sind dann Schieberegler auf der Webseite. Potis, Schalter und Gehäuse kannst du später dazubauen, siehe [Hardware anschließen](#hardware-anschließen).

## Was du brauchst

- Ein **ESP32-DevKit** mit ESP32-WROOM-32 und 4 MB Flash (zum Beispiel „ESP32 DevKit V1“, 30 oder 38 Pins).
- Ein **USB-Kabel mit Datenleitungen**. Reine Ladekabel gehen nicht.
- Einen Computer mit Windows, macOS oder Linux. Auf ihm wird die Firmware einmal gebaut und aufgespielt.
- Ein **WLAN mit 2,4 GHz**. Der ESP32 kann kein 5 GHz. Ohne WLAN geht es auch, dann macht die Fernbedienung ein eigenes auf.

## 1. Firmware aufspielen

### Quellcode holen

Auf der GitHub-Seite des Projekts **Code → Download ZIP** anklicken und die ZIP-Datei entpacken. Alternativ mit git:

```bash
git clone https://github.com/ru320/StudRailMaster.git
```

### Mit VS Code (empfohlen)

1. [Visual Studio Code](https://code.visualstudio.com/) installieren. Dann unter *Erweiterungen* nach **PlatformIO IDE** suchen und installieren.
2. In VS Code **Datei → Ordner öffnen** und den entpackten Projektordner wählen, also den Ordner, in dem `platformio.ini` liegt.
3. Den ESP32 per USB anstecken.
4. Unten in der blauen Leiste die Umgebung **env:esp32dev** wählen und auf den Pfeil **→ (Upload)** klicken.

Beim ersten Mal lädt PlatformIO den Compiler und die Bibliotheken herunter, einige hundert MB. Das dauert ein paar Minuten. Am Ende steht `SUCCESS`.

### Mit der Kommandozeile

Mit installiertem [PlatformIO Core](https://docs.platformio.org/en/latest/core/installation/index.html):

```bash
cd StudRailMaster
pio run -e esp32dev -t upload
pio device monitor          # optional: Ausgaben ansehen (115200 Baud), Ende mit Strg+C
```

### WLAN schon vorher eintragen (optional)

Normalerweise trägst du das WLAN später auf der Webseite ein. Du kannst es aber auch fest in die Firmware schreiben: `src/secrets.h.example` nach `src/secrets.h` kopieren und ausfüllen.

```c
#define SECRET_WIFI_SSID "MeinWLAN"
#define SECRET_WIFI_PASS "MeinPasswort"
#define SECRET_OTA_PASS  "einPasswortFürUpdates"
```

Ohne diese Datei geht es genauso. Was du auf der Webseite einträgst, gilt immer vorrangig.

## 2. Erste Verbindung

1. Nach dem Aufspielen startet der ESP32 neu und öffnet ein eigenes WLAN namens **StudRailMasterQuadro**.
2. Mit dem Handy oder PC in dieses WLAN gehen. Das Passwort ist **`zugfern123`**.
3. Im Browser **http://192.168.4.1** öffnen. Du siehst die Fahrseite der Fernbedienung.
4. Oben rechts auf das **Einstellungen-Symbol** tippen. Unter **WLAN** eintragen:
   - **Heim-WLAN** und **Passwort**.
   - **Gerätename**, wenn du willst. Standard ist `StudRailMasterQuadro`. Hast du mehrere Fernbedienungen, gib jeder einen eigenen Namen.
   - **AP-Passwort**: Bitte ein eigenes vergeben, mindestens 8 Zeichen. Es schützt das eigene WLAN der Fernbedienung und, solange du kein eigenes Update-Passwort festlegst, auch die Updates über WLAN.
5. **WLAN speichern** und dann **Neustart** klicken.
6. Wieder ins Heim-WLAN wechseln und **http://StudRailMasterQuadro.local** öffnen, bzw. `Gerätename.local`. Groß- und Kleinschreibung ist egal.

Findet die Fernbedienung das Heim-WLAN nach 10 Sekunden nicht, öffnet sie wieder ihr eigenes WLAN unter 192.168.4.1. Ein falsches Passwort sperrt dich also nicht aus.

## 3. Hubs einrichten

Das geht genauso wie im PC-Programm, nur auf der Webseite der Fernbedienung (*Einstellungen*):

1. Hub einschalten. Unter **Hubs suchen** auf **Scan starten (5 s)** klicken und beim Hub **übernehmen** klicken.
2. Auf der Hub-Karte jedem **Port** einen **Regler** (1–4) zuordnen. Bei Bedarf **umpolen** und **aktiv** anhaken.
3. **Speichern** klicken. Die Fernbedienung verbindet sich jetzt mit dem Hub.

**Mould King 4.0:** Dieser Hub taucht in der Suche nicht auf. Auf einer freien Hub-Karte „Mould King 4.0“ wählen, den Hub einschalten und **Einlernen** klicken. Den **Slot** wählst du mit der Taste am Hub (nach dem Einschalten ist es Slot 0).

Hast du die Hubs schon im PC-Programm eingerichtet, kannst du sie dort auch einfach an die Fernbedienung übergeben, siehe [Zusammen mit dem PC](esp-abgleich.md).

Gleichzeitig aktiv sind höchstens **4 Hubs**. Weitere bis zu 16 parkst du im **Archiv** und holst sie bei Bedarf auf einen Platz.

## 4. Fahren

Auf der Startseite erscheint für jeden zugeordneten Regler ein großer Hebel. Hochziehen heißt schneller. Ein Tipp auf die Richtung schaltet um. Der rote Knopf ist der **Not-Stopp**.

Nach dem Einschalten und nach jedem Not-Stopp fährt erst etwas, wenn **alle benutzten Regler einmal auf 0** standen. Fährst du über die Webseite, löst die Fernbedienung Not-Stopp aus, sobald die Seite 2 Sekunden lang nichts mehr von sich hören lässt, zum Beispiel weil das Handy-Display ausgeht.

### Status-LED auf dem Board

| LED | Bedeutung |
|---|---|
| aus | kein Hub aktiviert |
| schnelles Blinken | verbindet, noch kein Hub da |
| langsames Blinken | nur ein Teil der Hubs verbunden |
| an | alle aktivierten Hubs verbunden |
| Doppelblitz | Not-Stopp bzw. Anfahrsperre: alle Regler einmal auf 0 |

## Hardware anschließen

Mit Potis und Schaltern stellst du unter *Einstellungen → Fahrregler → Eingabe* auf **Potis + Schalter am ESP** um. Die Belegung der Pins:

| Funktion | GPIO | Anschluss |
|---|---|---|
| Schiebepoti 1–4 (10 kΩ linear) | 34, 35, 32, 33 | Schleifer; Enden an 3,3 V und GND |
| Richtungsschalter 1–4 | 16, 17, 18, 19 | gegen GND |
| Richtungs-LED 1–4 | 21, 22, 23, 25 | über 330 Ω gegen GND |
| Not-Stopp-Taster | 27 | gegen GND |

Teile, Stromversorgung und das druckbare Gehäuse: [Stückliste](../../hardware/BOM.md) und [Gehäuse](../../hardware/gehaeuse/README.md). Beides ist eine **Vorschau und noch nicht nachgebaut**.

## Updates über WLAN

Ist die Fernbedienung einmal eingerichtet, brauchst du kein USB-Kabel mehr:

- **VS Code:** Umgebung **env:ota** wählen, dann **Upload**.
- **Kommandozeile:** `pio run -e ota -t upload`. Bei einem anderen Gerätenamen hängst du `--upload-port Gerätename.local` an.

Das Passwort für Updates ist `SECRET_OTA_PASS` aus `src/secrets.h`. Gibt es diese Zeile nicht, ist es das **AP-Passwort** der Fernbedienung (Standard `zugfern123`). In diesem Fall trägst du es in `src/secrets.h` als `SECRET_OTA_PASS` ein.

Vor dem Update hält die Fernbedienung alle Züge an. Deine Einstellungen bleiben erhalten.

## Probleme?

- **Upload: „Failed to connect to ESP32“:** Die Taste **BOOT** am Board gedrückt halten, bis das Hochladen beginnt.
- **Kein Port gefunden:** Ein anderes USB-Kabel versuchen (Datenkabel!). Unter Windows und macOS braucht der USB-Chip des Boards eventuell einen Treiber, meist CP210x oder CH340. Unter Linux muss dein Benutzer in der Gruppe `dialout` sein (`sudo usermod -aG dialout $USER`, danach neu anmelden).
- **`StudRailMasterQuadro.local` geht nicht:** Manche Android-Handys und ältere Windows-Rechner kennen keine `.local`-Namen. Dann die IP-Adresse nehmen. Du findest sie in deinem Router oder im Serial-Monitor (`WLAN verbunden, http://…`).
- **Hub verbindet nicht:** Ein Hub kann nur mit einem Gerät gleichzeitig verbunden sein. Handy-App und PC-Programm also vorher schließen bzw. den Funk an die Fernbedienung abgeben, siehe [Zusammen mit dem PC](esp-abgleich.md).

---

*In Herbrechtingen ist es immer am schönsten!*
