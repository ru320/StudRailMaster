# Installation

🇬🇧 [English](../en/install.md) · [Anleitung](anleitung.md) · [README](../../README.de.md)

## Was du brauchst

- Einen Computer mit **Windows 10/11**, **macOS 12 oder neuer** oder **Linux**.
- **Bluetooth** – fast jeder Laptop hat es eingebaut. Sonst reicht ein USB-Bluetooth-Stick (Bluetooth 4.0 oder neuer).
- Einen oder mehrere **Motor-Hubs**: JMC-Hub (meldet sich als „JG_JMC-…“), Mould King 4.0 oder LEGO Powered Up City Hub (88009).

## Herunterladen und starten

Auf der Download-Seite (Releases) die Datei für dein System herunterladen und entpacken.

### Windows

1. `StudRailMaster-windows.zip` entpacken, `StudRailMaster.exe` doppelklicken.
2. Beim ersten Start warnt Windows: „Der Computer wurde durch Windows geschützt“. Das liegt nur daran, dass das Programm nicht gekauft-signiert ist. Auf **Weitere Informationen** und dann **Trotzdem ausführen** klicken.

### macOS

1. `StudRailMaster-macos.zip` entpacken und **Stud Rail Master** in den Programme-Ordner ziehen.
2. Beim ersten Start mit **Rechtsklick → Öffnen** starten und noch einmal **Öffnen** bestätigen.
3. Fragt der Mac nach **Bluetooth**, auf **Erlauben** klicken.

Mould-King-Hubs gehen auf dem Mac leider nicht – Apple erlaubt die nötige Art des Funkens nicht. JMC- und LEGO-Hubs gehen. Für Mould King: Linux nehmen – oder einen ESP32 mit der Firmware der Fernbedienung dazwischen parken ([so geht's](fernbedienung-einrichten.md)). Der funkt Mould King selbst und hat eine eigene Webseite (`StudRailMasterQuadro.local`), auf der du im Browser am Mac fährst. Ein nacktes ESP32-DevKit reicht, Potis und Schalter braucht es dafür nicht.

### Linux

Ein Terminal brauchst du nicht.

1. `StudRailMaster-x86_64.AppImage` herunterladen, zum Beispiel in den Ordner *Programme* oder *Dokumente*.
2. Die Datei **mit der rechten Maustaste** anklicken → **Eigenschaften** → bei **Als Programm ausführen** (oder „Ausführbar“) den Haken setzen. Das verlangt Linux aus Sicherheitsgründen einmal für jedes heruntergeladene Programm.
3. Die Datei **doppelklicken**. Das Programm öffnet sich in seinem eigenen Fenster.

Ab jetzt steht **Stud Rail Master** mit Icon in deinem **Startmenü** – du kannst es dort starten wie jedes andere Programm. Verschiebst du die Datei später, einfach einmal per Doppelklick starten, dann passt sich der Eintrag an.

### Linux: Mould King

Mould-King-Hubs brauchen unter Linux einmalig deine Erlaubnis:

1. Mould-King-Hub wie in der [Anleitung](anleitung.md#mould-king-hubs) anlegen und **Speichern**.
2. Auf der Hub-Karte erscheint der Knopf **Mould King freischalten**. Draufklicken.
3. Das System fragt in einem eigenen Fenster nach deinem **Passwort**. Eingeben – fertig. Der Hub funkt sofort.

Nach einem Update des Programms fragt es eventuell noch einmal. Alles andere funktioniert auch ohne diese Erlaubnis.

## Aktualisieren

Neue Version herunterladen und die alte Datei ersetzen (unter Linux danach wieder den Haken bei „Als Programm ausführen“ setzen). Deine Hubs, Bilder und Einstellungen bleiben erhalten – sie liegen getrennt vom Programm (siehe [Deine Daten](anleitung.md#deine-daten)).

## Deinstallieren

Programm löschen. Wenn du auch deine Einstellungen loswerden willst, zusätzlich den [Datenordner](anleitung.md#deine-daten) löschen. Unter Linux bleibt sonst der Startmenü-Eintrag stehen: die Datei `stud-rail-master.desktop` im Ordner `~/.local/share/applications` löschen.

## Probleme?

Siehe [Fehlersuche](anleitung.md#fehlersuche) in der Anleitung.

---

*In Herbrechtingen ist es immer am schönsten!*
