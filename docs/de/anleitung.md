# Anleitung

🇬🇧 [English](../en/user-guide.md) · [Installation](installation.md) · [README](../../README.de.md)

Mit Stud Rail Master fährst du deine Klemmbaustein-Züge vom Computer aus. Du brauchst nur einen Computer mit Bluetooth und einen oder mehrere Motor-Hubs.

## Erste Schritte

1. **Programm installieren** – siehe [Installation](installation.md).
2. **Programm starten.** Kurz erscheint ein Ladebildschirm, dann die Fahrseite. Sie ist am Anfang leer, weil noch kein Hub eingerichtet ist.
3. **Hub einschalten** (Batteriekasten an).
4. Oben rechts auf das **Einstellungen-Symbol** klicken (die drei Schieberegler).
5. Unter **Hubs suchen** auf **Scan starten** klicken. Nach 5 Sekunden erscheint dein Hub in der Liste (zum Beispiel „JG_JMC-C734“). Auf **übernehmen** klicken.
6. Auf der neuen Hub-Karte bei **Port A** den **Regler 1** auswählen. Der Port ist die Buchse, in der der Motor steckt.
7. Unten auf **Speichern** klicken.
8. Oben rechts auf das **Lok-Symbol** klicken – zurück zur Fahrseite. Dort ist jetzt ein Hebel. Hochziehen, und der Zug fährt!

Du willst das Programm erst einmal ohne Hub ausprobieren? Dann starte den **Demo-Modus** (siehe [Für Neugierige](#für-neugierige)).

## Fahren

![Fahrseite](../img/drive-de.png)

Für jeden Fahrregler, dem ein Hub zugeordnet ist, gibt es einen Hebel. Darauf steht, welche Züge er fährt – mit Bild, wenn du eins hinterlegt hast.

- **Schneller oder langsamer:** den Hebel nach oben oder unten ziehen. Einfach nur Antippen ändert nichts – so fährt ein Zug nie aus Versehen los.
- **Richtung:** die Taste unter dem Hebel (VOR / ZURÜCK). Wechselst du während der Fahrt, bremst der Zug erst ab und fährt dann in die andere Richtung los. Die Taste blinkt so lange.
- **Not-Stopp:** die große rote Taste oder die **Leertaste** auf der Tastatur. Alle Züge halten sofort an.

Oben siehst du, ob alle Hubs bereit sind. Wenn nicht, steht dort, woran es liegt.

### Anfahrsperre

Nach dem Start und nach jedem Not-Stopp fährt kein Zug, bis alle Hebel einmal ganz unten (auf 0) waren. Ein oranger Hinweis zeigt das an. So fährt nach einem Not-Stopp nichts von selbst wieder los.

## Einstellungen

Über das Einstellungen-Symbol oben rechts. Was du an Hubs und Reglern änderst, gilt erst, wenn du unten auf **Speichern** klickst. Mit **Verwerfen** machst du alles rückgängig.

### Fahrregler

- **Anzahl:** wie viele Hebel es gibt (1 bis 16).
- **Richtungswechsel während der Fahrt:** wie lange ein Zug zum Umkehren braucht, von voller Fahrt vorwärts bis volle Fahrt rückwärts. Standard sind 5 Sekunden. Bei 0 wechselt er sofort.
- Die Schieberegler auf dieser Seite fahren genauso wie die Hebel – praktisch zum Ausprobieren.

### Hubs

Jeder Hub hat eine Karte:

- **Bild:** auf den Bildrahmen klicken oder ein Foto darauf ziehen. Das Bild erscheint dann auf dem Hebel. Mit ✕ entfernst du es wieder.
- **Name:** zum Beispiel „ICE“ oder „Güterzug“. Er steht auf dem Hebel.
- **Typ:** *JMC*, *Mould King 4.0* oder *LEGO Powered Up City Hub* – je nachdem, welchen Hub du hast.
- **Adresse:** die Kennung des Hubs. Sie wird beim Suchen automatisch eingetragen.
- **aktiv:** Nur aktive Hubs werden gefahren. Nimmst du den Haken weg, kommt der Hub ins **Depot**. Dort bleibt er mit allen Einstellungen und Bild gespeichert, bis du ihn wieder brauchst.
- **Ports A bis D:** Für jede Buchse wählst du einen Fahrregler. Ein Regler kann mehrere Motoren fahren, auch auf verschiedenen Hubs – zum Beispiel zwei Loks in Doppeltraktion.
- **umpolen:** Fährt ein Motor falsch herum, setze hier den Haken.
- **Löschen:** entfernt den Hub ganz.

> **Gut zu wissen beim JMC-Hub:** Die Buchsen A und B fahren immer gleich schnell, ebenso C und D. Hängen A und B an verschiedenen Reglern, fahren beide mit dem schnelleren Wert. Die Karte weist darauf hin.

> **LEGO City Hub:** Er hat nur die Buchsen A und B. Die Suche erkennt ihn auch, wenn du ihn in der LEGO-App umbenannt hast. Er schaltet sich nach kurzer Zeit ab, wenn sich nichts mit ihm verbindet – also erst den Hub in der Liste haben, dann die grüne Taste drücken. An B kann auch das Licht (88005) hängen: Der Regler stellt dann die Helligkeit ein.

### Mould-King-Hubs

Mould-King-Hubs erscheinen nicht in der Suche. So richtest du einen ein:

1. **+ Neuer Hub** klicken, Typ **Mould King 4.0** wählen.
2. **Slot** wählen: Ein Mould-King-Hub kann auf Slot 0, 1 oder 2 hören. Mit der Taste am Hub wechselst du ihn; er blinkt dann 1-, 2- oder 3-mal. Nach dem Einschalten ist es immer Slot 0. So kannst du bis zu drei Mould-King-Hubs getrennt fahren.
3. Hub einschalten und auf **Einlernen** klicken. Der Hub merkt sich das Programm.
4. Ports zuordnen und **Speichern**.

Unter Linux klickst du beim ersten Mal auf **Mould King freischalten** und gibst dein Passwort ein, siehe [Installation](installation.md#linux-mould-king). Auf dem Mac geht Mould King leider nicht – dann Linux nehmen oder einen ESP32 dazwischen parken und über seine Webseite fahren, siehe [Installation](installation.md#macos).

### Hubs suchen

**Scan starten** sucht 5 Sekunden nach Bluetooth-Geräten in der Nähe. Erkannte Hubs sind markiert. Andere Geräte (Fernseher, Kopfhörer …) kannst du ignorieren.

### Fernbedienung (ESP)

Falls du die selbst gebaute ZugFern-Fernbedienung hast, kannst du Hubs zwischen ihr und dem Programm austauschen – siehe [Fernbedienung](esp-abgleich.md).

## Sicherheit

Der Computer passt auf, dass kein Zug unkontrolliert weiterfährt:

| Wenn … | dann … |
|---|---|
| du das Fenster schließt | halten alle Züge an, bevor das Programm endet |
| du den Not-Stopp drückst | halten alle Züge sofort an |
| die Verbindung zu einem Hub abreißt | verbindet sich das Programm von selbst neu |

**Achtung:** Reißt die Verbindung ab, fährt ein JMC-Hub mit dem letzten Befehl weiter, bis die Verbindung wieder steht. Halte den Computer deshalb in der Nähe der Strecke.

## Fehlersuche

| Problem | Was hilft |
|---|---|
| Ladebildschirm meldet „Bluetooth suchen“ in Orange | Ist Bluetooth am Computer eingeschaltet? |
| Hub bleibt bei „verbindet“ oder meldet „nicht gefunden“ | Ist der Hub an und sind die Batterien voll? Ist er noch mit einem Handy oder der Fernbedienung verbunden? Ein Hub kann immer nur mit einem Gerät verbunden sein – dort trennen oder den Hub aus- und einschalten. |
| Hub ist verbunden, aber der Zug fährt nicht | Ist ein Port einem Regler zugeordnet und gespeichert? Steht der orange Hinweis „Not-Stopp aktiv“? Dann alle Hebel einmal ganz nach unten. |
| Zug fährt falsch herum | Auf der Hub-Karte beim Port **umpolen** ankreuzen. |
| Mould-King-Hub reagiert nicht | Hub an, richtiger Slot? Noch einmal **Einlernen** klicken. Unter Linux: Knopf **Mould King freischalten** auf der Hub-Karte ([mehr](installation.md#linux-mould-king)). |
| Fenster bleibt leer oder schwarz | Programm schließen und erneut starten. |

## Deine Daten

Alles bleibt auf deinem Computer – das Programm geht nie ins Internet. Einstellungen und Bilder liegen hier:

| System | Ordner |
|---|---|
| Windows | `%APPDATA%\StudRailMaster` |
| macOS | `~/Library/Application Support/Stud Rail Master` |
| Linux | `~/.local/share/stud-rail-master` |

Zum Sichern oder für einen neuen Computer einfach den ganzen Ordner kopieren.

## Für Neugierige

Das Programm lässt sich mit Zusätzen starten (unter Windows in einer Verknüpfung, sonst im Terminal):

- `stud-rail-master --demo` – **Demo-Modus** mit drei simulierten Zügen, ganz ohne Hub. Deine echten Einstellungen bleiben unberührt.
- `stud-rail-master --lan` – auch vom **Handy** im Heimnetz aus bedienen. Die Adresse steht dann im Terminal. Achtung: Jeder in deinem WLAN kann dann mitfahren.

---

*In Herbrechtingen ist es immer am schönsten!*
