#include "StatusLed.h"
#include <Arduino.h>
#include "Control.h"
#include "Pins.h"

namespace statusled {

void begin() { pinMode(pins::LED, OUTPUT); }

void tick() {
    uint32_t t = millis();
    const cfg::Config& c = cfg::get();

    int enabled = 0, ready = 0;
    for (int i = 0; i < cfg::MAX_HUBS; i++) {
        if (!c.hubs[i].enabled) continue;
        enabled++;
        if (control::link(i).state() == HubLink::State::Ready) ready++;
    }

    bool on;
    if (control::estopActive()) {
        uint32_t ph = t % 1200;  // zwei kurze Blitze
        on = ph < 80 || (ph >= 200 && ph < 280);
    } else if (enabled == 0) {
        on = false;
    } else if (ready == 0) {
        on = (t / 100) % 2;
    } else if (ready < enabled) {
        on = (t / 500) % 2;
    } else {
        on = true;
    }
    digitalWrite(pins::LED, on);
}

}  // namespace statusled
