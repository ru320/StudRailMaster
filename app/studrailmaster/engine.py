"""Steuerung: Fahrregler → Rampe → Routen → Treiber → Funk. Portierung von src/Control.cpp.

Läuft in einem eigenen Thread mit asyncio-Loop („Funk-Thread“). Die HTTP-Threads rufen nur
die thread-sicheren Methoden (set_input, estop, gui_alive, state, …) auf.

Sicherheit wie auf dem ESP:
  * Nach dem Start und nach jedem Not-Stopp fahren die Motoren erst, wenn alle benutzten
    Regler einmal auf 0 standen.
  * Meldet sich die GUI 2 s nicht (/api/state), während ein Regler > 0 steht: Not-Stopp.
  * Beim Beenden: Stopp an alle Hubs, dann trennen.
"""
import asyncio
import logging
import threading
import time

from .drivers import DRIVERS
from .i18n import t

log = logging.getLogger("srm.engine")

TICK_S = 0.02
GUI_TIMEOUT_S = 2.0


class Throttle:
    def __init__(self):
        self.speed = 0  # 0…100
        self.reversed = False
        self.ramp = 0.0  # wirksamer Wert −100…100
        self.ramping = False

    @property
    def target(self) -> int:
        return -self.speed if self.reversed else self.speed


def ramp_to(th: Throttle, target: int, dt_ms: float, reverse_ms: int) -> int:
    """Folgt dem Sollwert direkt, außer bei Richtungswechsel während der Fahrt: dann läuft der
    Wert mit fester Rate (200 % in reverse_ms) über 0 auf den Sollwert (wie rampTo in Control.cpp)."""
    v = th.ramp
    if reverse_ms == 0:
        th.ramping = False
        th.ramp = float(target)
        return target
    if not th.ramping and v * target < 0:
        th.ramping = True
    if th.ramping:
        step = 200.0 * dt_ms / reverse_ms
        if v * target > 0 and abs(target) <= abs(v):
            v = float(target)
        elif abs(target - v) <= step:
            v = float(target)
        else:
            v += step if target > v else -step
        if v == target:
            th.ramping = False
    else:
        v = float(target)
    th.ramp = v
    return round(v)


class HubRuntime:
    def __init__(self, hub: dict):
        self.hub = hub
        self.driver = DRIVERS[hub["type"]]
        self.values = [0] * len(self.driver.ports)
        self.link = None


class Engine:
    def __init__(self, store, radio):
        self.store = store
        self.radio = radio
        self._lock = threading.RLock()
        self.loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self.started = time.monotonic()
        self.estop_latched = True  # Anfahrsperre nach dem Start
        self.estop_reason = "start"
        self.throttles: list[Throttle] = []
        self.hubs: dict[str, HubRuntime] = {}
        self.cfg = store.get()
        self._seen_rev = 0
        self._last_gui = time.monotonic()
        self.advertisers: dict[str, object] = {}
        self._adv_pair_until: dict[str, float] = {}
        self._closing: set = set()
        self._adv_reset = False
        self.live = None  # sync.LiveLink, solange der ESP Master ist
        self.ready = threading.Event()
        self.steps: list[dict] = []  # für den Ladebildschirm
        self._stop = asyncio.Event()

    # ---------- Start / Ende ----------

    def step(self, key: str, status: str, detail: str = "") -> None:
        with self._lock:
            for s in self.steps:
                if s["key"] == key:
                    s.update(status=status, detail=detail)
                    return
            self.steps.append({"key": key, "status": status, "detail": detail})

    def start(self) -> None:
        self._thread = threading.Thread(target=self._thread_main, name="funk", daemon=True)
        self._thread.start()

    def _thread_main(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._stop = asyncio.Event()
        self.loop.run_until_complete(self._main())

    async def _main(self) -> None:
        self.step("bluetooth", "busy")
        ok = await self.radio.check()
        self.step("bluetooth", "ok" if ok else "warn", "" if ok else self.radio.ble_error)
        self.step("hubs", "busy")
        self.ready.set()
        last = time.monotonic()
        first = True
        while not self._stop.is_set():
            now = time.monotonic()
            dt = (now - last) * 1000
            last = now
            try:
                await self._tick(dt)
            except Exception:  # noqa: BLE001 – die Steuerung darf nicht stehen bleiben
                log.exception("tick")
            if first:
                self.step("hubs", "ok")
                first = False
            await asyncio.sleep(TICK_S)
        await self._shutdown()

    def stop(self, timeout: float = 5.0) -> None:
        """Not-Stopp, Stopp-Pakete senden, alles trennen. Blockiert bis fertig."""
        self.estop("exit")
        if self.loop and self._thread and self._thread.is_alive():
            self.loop.call_soon_threadsafe(self._stop.set)
            self._thread.join(timeout)

    async def _shutdown(self) -> None:
        # Not-Stopp ist gesetzt: einmal ticken, damit alle Pakete auf Stopp stehen
        await self._tick(0)
        await asyncio.sleep(0.3)  # Hub hat keinen Watchdog – Stopp muss sicher ankommen
        await self._release_radio()

    async def _release_radio(self) -> None:
        links = [rt.link for rt in self.hubs.values() if rt.link]
        for rt in self.hubs.values():
            rt.link = None
        await asyncio.gather(*(link.close() for link in links), return_exceptions=True)
        for key, adv in list(self.advertisers.items()):
            adv.set(DRIVERS[key].stop())
            await asyncio.sleep(0.3)
            await adv.close()
        self.advertisers.clear()

    # ---------- Thread-sichere Schnittstelle ----------

    def gui_alive(self) -> None:
        self._last_gui = time.monotonic()

    def gui_idle(self) -> float:
        """Sekunden seit der letzten Abfrage der GUI."""
        return time.monotonic() - self._last_gui

    def set_input(self, ch: int, speed=None, reversed_=None) -> None:
        with self._lock:
            if not 0 <= ch < len(self.throttles):
                raise ValueError("ungültiger Kanal")
            th = self.throttles[ch]
            if speed is not None:
                th.speed = max(0, min(100, int(speed)))
            if reversed_ is not None:
                th.reversed = bool(reversed_)

    def estop(self, reason: str = "gui") -> None:
        with self._lock:
            if not self.estop_latched:
                log.warning(t("NOT-STOPP (%s)", "EMERGENCY STOP (%s)"), reason)
            self.estop_latched = True
            self.estop_reason = reason
            for th in self.throttles:
                # auch die Rampe: die Sperre ist im nächsten Takt schon frei (Regler auf 0)
                th.speed, th.ramp, th.ramping = 0, 0.0, False

    def pair(self, driver_id: str = "mk4") -> None:
        with self._lock:
            self._adv_pair_until[driver_id] = time.monotonic() + DRIVERS[driver_id].pair_ms / 1000

    def reset_advertisers(self) -> None:
        """Sender neu aufbauen (z. B. nach dem Freischalten von Mould King)."""
        with self._lock:
            self._adv_reset = True

    def run_coro(self, coro, timeout: float = 30.0):
        """Coroutine im Funk-Thread ausführen (z. B. Scan) und auf das Ergebnis warten."""
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)

    def set_live(self, live) -> None:
        """ESP übernimmt (live) bzw. gibt zurück (None). Lokaler Funk pausiert solange."""
        with self._lock:
            self.live = live
            self.estop("live-link")

    def state(self) -> dict:
        with self._lock:
            hubs = {}
            for hid, rt in self.hubs.items():
                hubs[hid] = self._hub_state(rt)
            return {
                "estop": self.estop_latched,
                "estopReason": self.estop_reason,
                "demo": self.radio.demo,
                "uptime": int(time.monotonic() - self.started),
                "channels": [
                    {"speed": th.speed, "reversed": th.reversed, "value": round(th.ramp)} for th in self.throttles
                ],
                "hubs": hubs,
                "radio": {
                    "ble": self.radio.ble_ok,
                    "bleError": self.radio.ble_error,
                    "advert": {k: {"ok": a.ok, "reason": a.reason, "unlock": a.unlock} for k, a in self.advertisers.items()},
                },
            }

    def _hub_state(self, rt: HubRuntime) -> dict:
        h, d = rt.hub, rt.driver
        if not h["enabled"] or self.live:
            st = {"state": "off", "ready": False, "error": "", "reconnects": 0, "rssi": 0}
        elif d.kind == "gatt":
            link = rt.link
            st = {
                "state": link.state if link else "off",
                "ready": bool(link and link.state == "ready"),
                "error": link.error if link else "",
                "reconnects": link.reconnects if link else 0,
                "rssi": link.rssi if link else 0,
            }
        else:
            adv = self.advertisers.get(d.id)
            pairing = self._adv_pair_until.get(d.id, 0) > time.monotonic()
            ok = bool(adv and adv.ok)
            st = {
                "state": "pairing" if ok and pairing else "sending" if ok else "error",
                "ready": ok and not pairing,
                "error": adv.reason if adv else "",
                "reconnects": 0,
                "rssi": 0,
            }
        st["ports"] = list(rt.values)
        st["pairConflict"] = self._conflicts(rt)
        return st

    @staticmethod
    def _conflicts(rt: HubRuntime) -> list[bool]:
        out = []
        ports = rt.driver.ports
        for group in rt.driver.shared_speed:
            srcs = {rt.hub["routes"][ports.index(p)]["source"] for p in group} - {0}
            out.append(len(srcs) > 1)
        return out

    # ---------- Funk-Thread ----------

    def _used_at_zero(self) -> bool:
        for rt in self.hubs.values():
            if not rt.hub["enabled"]:
                continue
            for r in rt.hub["routes"]:
                s = r["source"]
                if s and s <= len(self.throttles) and self.throttles[s - 1].speed != 0:
                    return False
        return True

    def _reconcile(self) -> None:
        """Neue Einstellungen: Regler-Anzahl anpassen, Verbindungen auf- und abbauen."""
        self.cfg = self.store.get()
        n = self.cfg["throttles"]
        while len(self.throttles) < n:
            self.throttles.append(Throttle())
        del self.throttles[n:]
        old = self.hubs
        self.hubs = {}
        for h in self.cfg["hubs"]:
            rt = HubRuntime(h)
            prev = old.pop(h["id"], None)
            wanted = h["enabled"] and rt.driver.kind == "gatt" and h["mac"] and not self.live
            if prev and prev.link and wanted and prev.hub["mac"] == h["mac"] and prev.hub["type"] == h["type"]:
                rt.link = prev.link
                prev.link = None
            elif wanted:
                rt.link = self.radio.gatt_link(h["mac"], rt.driver)
                rt.link.start()
            if prev and prev.link:
                self._close_later(prev.link)
            self.hubs[h["id"]] = rt
        for prev in old.values():
            if prev.link:
                self._close_later(prev.link)

    def _close_later(self, link) -> None:
        task = asyncio.get_running_loop().create_task(link.close())
        self._closing.add(task)
        task.add_done_callback(self._closing.discard)

    async def _tick(self, dt_ms: float) -> None:
        with self._lock:
            if self.store.revision != self._seen_rev:
                self._seen_rev = self.store.revision
                self._reconcile()
            live = self.live
            now = time.monotonic()
            if not live and not self._used_at_zero() and now - self._last_gui > GUI_TIMEOUT_S:
                log.warning(t("GUI antwortet nicht mehr", "GUI stopped responding"))
                self.estop("gui-timeout")
            if self.estop_latched and self._used_at_zero() and not live:
                self.estop_latched = False
                log.info(t("Freigabe: alle Fahrregler auf 0", "released: all throttles at 0"))
            ch_val = []
            for th in self.throttles:
                if self.estop_latched:  # Not-Stopp wirkt sofort, ohne Rampe
                    th.ramp, th.ramping = 0.0, False
                ch_val.append(ramp_to(th, 0 if self.estop_latched else th.target, dt_ms, self.cfg["reverseMs"]))

            adv_slots: dict[str, dict] = {}
            for rt in self.hubs.values():
                h = rt.hub
                for p, r in enumerate(h["routes"]):
                    s = r["source"]
                    v = ch_val[s - 1] if h["enabled"] and s and s <= len(ch_val) and not live else 0
                    rt.values[p] = -v if r["invert"] else v
                if rt.driver.kind == "gatt":
                    if rt.link:
                        rt.link.set_frame(rt.driver.encode(rt.values))
                elif h["enabled"] and not live:
                    adv_slots.setdefault(rt.driver.id, {})[h["slot"]] = list(rt.values)
            pair_until = dict(self._adv_pair_until)
            adv_reset, self._adv_reset = self._adv_reset, False

        if live:
            if any(rt.link for rt in self.hubs.values()) or self.advertisers:
                await self._release_radio()  # der ESP braucht die Hubs (JMC: nur eine Verbindung)
            return

        if adv_reset:
            for adv in self.advertisers.values():
                await adv.close()
            self.advertisers.clear()
        # Sender für Werbe-Treiber: an, solange ein aktiver Hub ihn braucht
        for key in list(self.advertisers):
            if key not in adv_slots:
                adv = self.advertisers.pop(key)
                adv.set(DRIVERS[key].stop())
                await asyncio.sleep(0.3)
                await adv.close()
        for key, slots in adv_slots.items():
            d = DRIVERS[key]
            adv = self.advertisers.get(key)
            if adv is None:
                adv = self.radio.advertiser()
                self.advertisers[key] = adv
                if await adv.start():
                    self.pair(key)  # gerade aktiviert: einlernen wie auf dem ESP
                    pair_until[key] = self._adv_pair_until[key]
            if adv.ok:
                adv.set(d.pair() if pair_until.get(key, 0) > time.monotonic() else d.encode(slots))
