"""Programmfenster: pywebview (Windows: WebView2, macOS: WebKit, Linux: Qt WebEngine).

Unter Linux bringt das fertige Programm Qt mit (PySide6), denn die System-Engine WebKitGTK
lässt sich nicht portabel einpacken. Aus dem Quellcode geht auch WebKitGTK.
Nur wenn gar kein Fenster möglich ist, öffnet main.py den Browser.
"""
import logging
import os
import sys
from pathlib import Path

from .i18n import t

log = logging.getLogger("srm.window")

ICON = Path(__file__).resolve().parent / "web" / "icon.png"
_running = False  # Fenster läuft gerade (webview.start blockiert)


def open_window(url: str, title: str, storage: Path) -> bool:
    """Blockiert, bis das Fenster geschlossen wird. False = kein Fenster möglich."""
    try:
        import webview
    except ImportError:
        log.info(t("pywebview nicht installiert – nehme den Browser", "pywebview not installed – using the browser"))
        return False
    try:
        gui = _linux_gui()
        webview.create_window(title, url, width=1180, height=840, min_size=(380, 560), background_color="#24282B")
        storage.mkdir(parents=True, exist_ok=True)
        # private_mode=False: Sprache usw. (localStorage) bleibt erhalten
        global _running
        _running = True
        try:
            webview.start(gui=gui, private_mode=False, storage_path=str(storage), icon=str(ICON) if ICON.exists() else None)
        finally:
            _running = False
        return True
    except Exception as e:  # noqa: BLE001 – z. B. fehlendes WebKitGTK unter Linux
        log.warning(t("Fenster geht nicht (%s) – nehme den Browser", "no window (%s) – using the browser"), e)
        return False


def _linux_gui() -> str | None:
    """Linux: Qt nehmen, wenn es da ist (fertiges Programm), sonst pywebview wählen lassen."""
    if not sys.platform.startswith("linux"):
        return None
    try:
        import qtpy  # noqa: F401
    except ImportError:
        return None
    # Chromiums Sandbox braucht User-Namespaces, die z. B. Ubuntu 24.04 für AppImages sperrt.
    # Die Seite kommt nur von 127.0.0.1 (eigener Code, CSP ohne fremde Quellen).
    if getattr(sys, "frozen", False):
        os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
    os.environ.setdefault("QT_API", "pyside6")
    return "qt"


def close_windows() -> bool:
    """Schließt offene Fenster (aus einem Signal-Handler). True, wenn eins offen war."""
    if not _running:  # z. B. Fenster gescheitert, Browser-Modus: dann normal beenden
        return False
    try:
        import webview
    except ImportError:
        return False
    wins = list(getattr(webview, "windows", []))
    for w in wins:
        try:
            w.destroy()
        except Exception:  # noqa: BLE001
            pass
    return bool(wins)


def focus_window() -> bool:
    """Holt das offene Fenster nach vorne (zweiter Start). True, wenn eins offen war."""
    if not _running:
        return False
    try:
        import webview
    except ImportError:
        return False
    wins = list(getattr(webview, "windows", []))
    for w in wins:
        try:
            w.restore()
            w.show()
        except Exception:  # noqa: BLE001
            pass
    return bool(wins)
