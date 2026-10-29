# Zusammen mit der Fernbedienung

🇬🇧 [English](../en/esp-sync.md) · [Anleitung](anleitung.md) · [README](../../README.de.md)

Hast du die selbst gebaute **ZugFern-Fernbedienung** (Stud Rail Master Quadro), arbeitet das Programm mit ihr zusammen. Beide müssen dafür im selben WLAN sein – oder der Computer ist mit dem WLAN „ZugFern“ der Fernbedienung verbunden.

Alles findest du unter **Einstellungen → Fernbedienung (ESP)**. Im Feld **Adresse** steht normalerweise `StudRailMasterQuadro.local` – Groß- und Kleinschreibung ist egal. Hast du der Fernbedienung einen anderen Gerätenamen gegeben (auf ihrer Webseite unter *Einstellungen → WLAN*, zum Beispiel bei mehreren Fernbedienungen), trage `Gerätename.local` ein. Klappt das nicht, nimm die IP-Adresse der Fernbedienung (in ihrem eigenen WLAN, das genauso heißt wie der Gerätename, ist das `192.168.4.1`).

## Hubs von der Fernbedienung holen

Du hast deine Hubs schon in der Fernbedienung eingerichtet? Dann musst du sie nicht noch einmal anlegen:

1. **Hubs vom ESP holen** klicken. Die Liste zeigt alle Hubs der Fernbedienung.
2. Bei jedem gewünschten Hub auf **übernehmen** klicken.
3. **Speichern**. Jetzt noch ein Bild dazu – fertig.

Die übernommenen Hubs landen zuerst im **Depot**. Setz den Haken bei **aktiv**, wenn du sie vom Computer aus fahren willst – und schalte dann die Fernbedienung aus, denn ein Hub kann nur mit einem Gerät gleichzeitig verbunden sein.

## Hubs an die Fernbedienung schicken

Andersherum geht es auch:

1. In der Liste die Hubs ankreuzen, die die Fernbedienung bekommen soll.
2. **An ESP übergeben** klicken.
3. An der Fernbedienung (auf dem Handy) unter **Archiv** den Hub mit **Holen** auf einen Platz setzen.

Gut zu wissen:

- Die Fernbedienung hat nur **4 Fahrregler**. Hängt ein Port an Regler 5 oder höher, bleibt er dort leer – du bekommst einen Hinweis.
- Die Fernbedienung kann sich höchstens **16 Hubs** merken.
- **Bilder** bleiben auf dem Computer, dafür hat die Fernbedienung keinen Platz.
- Hubs, die gerade an der Fernbedienung fahren, werden nicht überschrieben.
- **LEGO City Hubs** gehen in beide Richtungen, mit ihren Buchsen A und B. Die Fernbedienung findet sie auch selbst in der Suche.
- Hubs, die du am **Mac** gefunden hast, lassen sich nicht übergeben – der Mac verrät die echte Adresse des Hubs nicht. Such sie in dem Fall direkt an der Fernbedienung.

## Live-Link: der Computer als Anzeige der Fernbedienung

Mit **Live-Link starten** übernimmt die Fernbedienung das Kommando:

- Die **Fernbedienung fährt** die Züge. Der Computer gibt dafür seine Hubs frei.
- Auf der Fahrseite siehst du die **Regler der Fernbedienung** – mit den Bildern deiner Hubs.
- Ist die Fernbedienung auf **Schieberegler (GUI)** eingestellt, kannst du auch am Computer mitfahren. Bei **Potis + Schalter** schaust du nur zu.
- Der **Not-Stopp** am Computer hält auch die Fernbedienung an.
- Geht der Computer weg (Fenster zu, WLAN weg), während ein Zug fährt, hält die Fernbedienung nach 2 Sekunden selbst alle Züge an.

- Auf der Fernbedienung (Handy) steht oben, welcher Computer gerade zuschaut.

**Live-Link beenden** gibt die Hubs an den Computer zurück: Die Fernbedienung hält alle Züge an und trennt sich von den Hubs. Danach erst alle Hebel einmal auf 0 stellen. Auf dem Handy steht dann **Funk beim PC**. Mit **Funk zurückholen** fährt wieder die Fernbedienung – der Computer verliert dann seine Hubs. Nach einem Neustart funkt die Fernbedienung ohnehin wieder selbst.

---

*In Herbrechtingen ist es immer am schönsten!*
