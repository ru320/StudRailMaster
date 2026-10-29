#pragma once
#include "Config.h"
#include "HubLink.h"

// Verknüpft Potis, Konfiguration und Hub-Verbindungen.
namespace control {

void begin();
void tick();

// Not-Stopp auslösen (Taster, GUI oder GUI-Timeout). Setzt die Web-Regler auf 0.
// Aufgehoben wird er, sobald alle benutzten Fahrregler auf 0 stehen.
// Nach dem Einschalten ist die Sperre ebenfalls aktiv.
void triggerEstop();
bool estopActive();

// Die GUI meldet sich (bei jeder Abfrage). Bleibt das bei Eingabe "Web" länger als
// 2 s aus, während ein Regler > 0 steht, wird Not-Stopp ausgelöst.
void webAlive();

// Live-Link: Funk an den PC abgeben bzw. zurückholen. releaseRadio() löst Not-Stopp aus,
// sendet 500 ms lang Stopp und trennt dann alle Hubs (JMC: Verbindung, MK4: Werbung aus).
// takeRadio() verbindet wieder; die Anfahrsperre gilt wie nach dem Einschalten.
// Der Zustand steht nur im RAM: Nach einem Neustart funkt der ESP wieder selbst.
void releaseRadio();
void takeRadio();
bool radioReleased();  // true auch schon während der 500 ms Stopp-Pakete

HubLink& link(int index);

// Aktueller Sollwert −100…100 eines Hub-Ports (nach Umpolen), für die GUI.
int portValue(int hubIndex, int port);

// Wirksamer Wert −100…100 eines Fahrreglers (mit Rampe beim Richtungswechsel), für die GUI.
int channelValue(int ch);

// true, wenn A/B bzw. C/D eines Hubs an verschiedenen Fahrreglern hängen (gemeinsamer Speed).
bool pairConflict(int hubIndex, int pair);

}  // namespace control
