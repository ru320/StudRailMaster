#pragma once

// Onboard-LED:
//   Doppelblitz       = Not-Stopp / Anfahrsperre aktiv
//   schnelles Blinken = kein Hub verbunden (verbindet)
//   langsames Blinken = nur ein Teil der aktivierten Hubs verbunden
//   an                = alle aktivierten Hubs verbunden
//   aus               = kein Hub aktiviert
namespace statusled {

void begin();
void tick();

}  // namespace statusled
