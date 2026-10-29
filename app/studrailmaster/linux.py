"""Linux-Komfort: Startmenü-Eintrag und „Mould King freischalten“.

Mould King braucht rohe HCI-Kommandos und damit CAP_NET_RAW. Das Recht bekommt nicht das
ganze Programm, sondern nur das kleine Hilfsprogramm srm-hci-helper (packaging/linux/*.c),
das ausschließlich Werbung senden kann. Freischalten kopiert es nach ~/.local/lib (eine
AppImage ist „nosuid“ eingehängt, dort wirkt setcap nicht) und setzt das Recht per pkexec –
das System fragt im eigenen Fenster nach dem Passwort.
"""
import hashlib
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import NAME, SLUG
from .i18n import t

log = logging.getLogger("srm.linux")

BUNDLED_HELPER = Path(__file__).resolve().parent / "bin" / "srm-hci-helper"
LIB = Path.home() / ".local" / "lib" / SLUG
HELPER = LIB / "srm-hci-helper"
ICON = Path(__file__).resolve().parent / "web" / "icon.png"


def _digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ""


def helper_ready() -> bool:
    """Freigeschaltetes Hilfsprogramm vorhanden und gleich dem mitgelieferten?"""
    return HELPER.is_file() and _digest(HELPER) == _digest(BUNDLED_HELPER)


def can_unlock() -> bool:
    return sys.platform.startswith("linux") and BUNDLED_HELPER.is_file()


def unlock() -> str:
    """Hilfsprogramm kopieren und berechtigen. Gibt '' zurück oder den Fehlertext."""
    if not can_unlock():
        return t("In dieser Installation fehlt das Hilfsprogramm – siehe Entwickler-Doku.",
                 "This installation has no helper program – see the developer docs.")
    pkexec = shutil.which("pkexec")
    setcap = shutil.which("setcap") or next((p for p in ("/usr/sbin/setcap", "/sbin/setcap") if os.path.exists(p)), "")
    LIB.mkdir(parents=True, exist_ok=True)
    tmp = HELPER.with_suffix(".neu")
    shutil.copyfile(BUNDLED_HELPER, tmp)
    os.chmod(tmp, 0o755)
    os.replace(tmp, HELPER)
    manual = f"sudo setcap cap_net_raw+ep {HELPER}"
    if not pkexec or not setcap:
        return t(f"Bitte einmal im Terminal eingeben: {manual}", f"Please enter once in a terminal: {manual}")
    try:
        r = subprocess.run([pkexec, setcap, "cap_net_raw+ep", str(HELPER)], capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return t("Keine Antwort auf die Passwort-Abfrage.", "No answer to the password prompt.")
    if r.returncode in (126, 127):
        return t("Abgebrochen.", "Cancelled.")
    if r.returncode != 0:
        return (r.stderr.strip() or f"pkexec {r.returncode}") + " – " + t(f"sonst im Terminal: {manual}", f"otherwise in a terminal: {manual}")
    log.info(t("Mould King freigeschaltet: %s", "Mould King unlocked: %s"), HELPER)
    return ""


def launcher() -> list[str] | None:
    """Womit das Startmenü das Programm startet – None, wenn aus dem Quellcode gestartet."""
    if os.environ.get("APPIMAGE"):
        return [os.environ["APPIMAGE"]]
    if getattr(sys, "frozen", False):
        return [sys.executable]
    exe = shutil.which(SLUG)
    return [exe] if exe else None


def install_menu_entry() -> None:
    """Startmenü-Eintrag mit Icon anlegen bzw. aktualisieren (z. B. wenn die AppImage umgezogen ist)."""
    cmd = launcher()
    if not cmd or not sys.platform.startswith("linux"):
        return
    # Probeläufe aus einem Temp-Ordner nicht ins Startmenü eintragen (der Pfad wäre bald weg)
    if Path(cmd[0]).resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()):
        return
    try:
        share = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
        icon = share / "icons" / "hicolor" / "256x256" / "apps" / f"{SLUG}.png"
        icon.parent.mkdir(parents=True, exist_ok=True)
        if ICON.is_file() and _digest(icon) != _digest(ICON):
            shutil.copyfile(ICON, icon)
        exec_line = " ".join(f'"{c}"' if " " in c else c for c in cmd)
        entry = (
            "[Desktop Entry]\nType=Application\n"
            f"Name={NAME}\n"
            "Comment=Klemmbaustein-Züge per Bluetooth fahren – In Herbrechtingen ist es immer am schönsten!\n"
            "Comment[en]=Drive brick-built trains via Bluetooth\n"
            f"Exec={exec_line}\nIcon={SLUG}\nTerminal=false\nCategories=Game;Utility;\n"
            "Keywords=train;zug;bluetooth;lego;mould king;\nStartupNotify=true\n"
        )
        desktop = share / "applications" / f"{SLUG}.desktop"
        desktop.parent.mkdir(parents=True, exist_ok=True)
        if not desktop.exists() or desktop.read_text(encoding="utf-8") != entry:
            desktop.write_text(entry, encoding="utf-8")
            log.info(t("Startmenü-Eintrag angelegt: %s", "menu entry created: %s"), desktop)
    except OSError as e:
        log.warning(t("Startmenü-Eintrag ging nicht: %s", "could not create menu entry: %s"), e)
