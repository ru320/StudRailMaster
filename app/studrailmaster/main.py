"""Programmstart: Einstellungen, Funk-Thread, Webserver, Fenster."""
import argparse
import json
import logging
import os
import shutil
import signal
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

from . import MOTTO, MOTTO_EN, NAME, SLUG, __version__
from .config import Store, data_dir, new_hub
from .drivers import selftest
from .engine import Engine
from .i18n import t
from .radio import create
from .server import App, serve
from .window import close_windows, open_window

log = logging.getLogger("srm")

BROWSER_IDLE_EXIT_S = 30  # Browser-Modus: Ende, wenn die Seite so lange nicht mehr fragt


def parse_args(argv):
    p = argparse.ArgumentParser(
        prog=SLUG,
        description=t(
            f"{NAME} – Züge mit BLE-Motor-Hubs vom PC aus fahren. Alles bleibt auf diesem Rechner, kein Internet.",
            f"{NAME} – drive trains with BLE motor hubs from your PC. Everything stays on this computer, no internet.",
        ),
        epilog=t(MOTTO, MOTTO_EN),
    )
    p.add_argument("--demo", action="store_true", help=t("simulierte Hubs, kein Bluetooth", "simulated hubs, no Bluetooth"))
    p.add_argument("--browser", action="store_true", help=t("im Browser statt im eigenen Fenster", "use the browser instead of a window"))
    p.add_argument("--no-gui", action="store_true", help=t("nur Server, nichts öffnen", "server only, open nothing"))
    p.add_argument("--port", type=int, default=0, help=t("fester Port (Standard: frei)", "fixed port (default: any free)"))
    p.add_argument("--lan", action="store_true",
                   help=t("auch im Heimnetz erreichbar (Handy als Fahrpult) – ohne Passwort!",
                          "reachable from the home network (phone as throttle) – no password!"))
    p.add_argument("--data", metavar="DIR", help=t("Datenordner", "data folder"))
    p.add_argument("--hci", type=int, default=0, help=t("Linux: Adapter für Mould King (hciN)", "Linux: adapter for Mould King (hciN)"))
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--version", action="version", version=f"{NAME} {__version__} – {t(MOTTO, MOTTO_EN)}")
    return p.parse_args(argv)


def seed_demo(store: Store) -> None:
    """Demo-Ordner beim ersten Start mit drei Zügen füllen."""
    if store.get()["hubs"]:
        return
    demo = Path(__file__).resolve().parent / "web" / "demo"
    hubs = []
    for name, typ, mac, slot, img, routes in (
        ("BR 18 478", "jmc", "a9:22:28:bc:3a:c7", 0, "br18", [1, 0, 0, 0]),
        ("ICE 3", "jmc", "13:12:05:04:ae:f2", 0, "ice3", [2, 2, 0, 0]),
        ("Schienenzeppelin", "mk4", "", 0, "zeppelin", [3, 0, 0, 0]),
    ):
        h = new_hub(typ, name)
        h.update(mac=mac, slot=slot, enabled=True)
        for p, s in enumerate(routes):
            h["routes"][p]["source"] = s
        hubs.append((h, demo / f"{img}.png"))
    store.update({"hubs": [h for h, _ in hubs]})
    for h, img in hubs:
        if img.exists():
            store.set_image(h["id"], img.read_bytes(), "png")


def lan_ip() -> str:
    """Eigene Adresse im Heimnetz. UDP-connect sendet nichts, es wählt nur die Schnittstelle."""
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.168.0.1", 9))
            return s.getsockname()[0]
    except OSError:
        return "?"


def other_instance(folder: Path) -> str:
    """URL einer schon laufenden Instanz mit diesem Datenordner, sonst ''."""
    f = folder / "instance.json"
    try:
        port = json.loads(f.read_text())["port"]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"http://127.0.0.1:{port}/api/info", timeout=0.7) as r:
            if json.loads(r.read()).get("name") == NAME:
                return f"http://127.0.0.1:{port}/"
    except (OSError, ValueError, KeyError):
        pass
    return ""


def focus_running(url: str) -> bool:
    """Bittet die laufende Instanz, ihr Fenster nach vorne zu holen. False = sie hat keins."""
    req = urllib.request.Request(url + "api/focus", data=b"{}", method="POST",
                                 headers={"Content-Type": "application/json", "X-SRM": "1"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=2) as r:
            return bool(json.loads(r.read()).get("window"))
    except (OSError, ValueError):
        return False


def main(argv=None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    log.info("%s %s – %s", NAME, __version__, t(MOTTO, MOTTO_EN))

    folder = data_dir(args.data)
    if args.demo and not args.data:
        folder = folder / "demo"  # Demo verändert nie die echten Einstellungen
    folder.mkdir(parents=True, exist_ok=True)

    running = other_instance(folder)
    if running:
        # Zwei Instanzen würden sich um dieselben Hubs streiten
        log.info(t("läuft schon: %s", "already running: %s"), running)
        # Läuft sie mit Fenster (z. B. Doppelklick, weil die AppImage langsam startet), das Fenster
        # nach vorne holen – nur ohne Fenster (Browser-Modus) die Seite im Browser öffnen
        if not args.no_gui and (args.browser or not focus_running(running)):
            webbrowser.open(running)
        return 0

    store = Store(folder)
    radio = create(demo=args.demo, hci=args.hci)
    engine = Engine(store, radio)
    engine.step("config", "warn" if store.load_error else "ok", store.load_error)
    if args.demo:
        seed_demo(store)
    if sys.platform.startswith("linux"):
        from .linux import install_menu_entry

        install_menu_entry()  # Startmenü-Eintrag, damit niemand das Terminal braucht
    errors = selftest.run()
    engine.step("drivers", "warn" if errors else "ok", ", ".join(errors))
    if errors:
        log.error(t("Treiber-Selbsttest fehlgeschlagen: %s", "driver self-test failed: %s"), errors)
    engine.start()

    app = App(store, engine, lan=args.lan)
    httpd = serve(app, args.port)
    url = f"http://127.0.0.1:{app.port}/"
    instance = folder / "instance.json"
    instance.write_text(json.dumps({"pid": os.getpid(), "port": app.port}))
    log.info(t("Oberfläche: %s  (Daten: %s)", "user interface: %s  (data: %s)"), url, folder)
    if args.lan:
        log.info(t("Im Heimnetz (Handy): http://%s:%d/", "on the home network (phone): http://%s:%d/"), lan_ip(), app.port)
        log.warning(t("--lan: Jeder im Heimnetz kann über Port %d fahren!", "--lan: anyone on the home network can drive via port %d!"), app.port)

    def _terminate(*_):
        # kill/Abmelden/Strg+C: Die Stopp-Pakete müssen raus (Hub ohne Watchdog). Ist ein Fenster
        # offen, schluckt dessen Ereignisschleife Ausnahmen – dann Fenster schließen, das beendet start().
        if close_windows():
            return
        raise KeyboardInterrupt

    for sig in ("SIGTERM", "SIGHUP", "SIGINT"):
        if hasattr(signal, sig):
            signal.signal(getattr(signal, sig), _terminate)

    try:
        if args.no_gui:
            while True:
                time.sleep(1)
        elif args.browser or not open_window(url, NAME, folder / "webview"):
            webbrowser.open(url)
            log.info(t("Beenden mit Strg+C oder Tab schließen", "quit with Ctrl+C or by closing the tab"))
            seen = False
            while True:
                time.sleep(1)
                idle = engine.gui_idle()
                seen = seen or idle < 2
                if seen and idle > BROWSER_IDLE_EXIT_S:
                    log.info(t("Seite geschlossen – beende", "page closed – exiting"))
                    break
    except KeyboardInterrupt:
        pass
    finally:
        log.info(t("halte alle Züge an …", "stopping all trains …"))
        engine.stop()
        httpd.shutdown()
        instance.unlink(missing_ok=True)
        shutil.rmtree(folder / "webview" / "Cache", ignore_errors=True)
        log.info(t("Tschüss! %s", "Bye! %s"), t(MOTTO, MOTTO_EN))
    return 0
