# PyInstaller-Rezept für Stud Rail Master (Windows .exe, macOS .app, Linux-Programm).
#   cd app && pyinstaller packaging/studrailmaster.spec
# Ergebnis in app/dist/. Siehe docs/de/bauen.md bzw. docs/en/building.md.
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

APP = Path(SPECPATH).parent  # noqa: F821
ROOT = APP.parent
NAME = "StudRailMaster"

datas = [
    (str(APP / "studrailmaster" / "web"), "studrailmaster/web"),
    (str(ROOT / "drivers" / "jmc.json"), "studrailmaster/drivers/specs"),
    (str(ROOT / "drivers" / "mk4.json"), "studrailmaster/drivers/specs"),
    (str(ROOT / "drivers" / "lego.json"), "studrailmaster/drivers/specs"),
    (str(ROOT / "docs" / "de"), "studrailmaster/docs/de"),  # eingebaute Hilfe
    (str(ROOT / "docs" / "en"), "studrailmaster/docs/en"),
    (str(ROOT / "docs" / "img"), "studrailmaster/docs/img"),
]
# Linux: Hilfsprogramm für Mould King (vorher bauen: cc -O2 -static -o studrailmaster/bin/srm-hci-helper packaging/linux/srm-hci-helper.c)
helper = APP / "studrailmaster" / "bin" / "srm-hci-helper"
if sys.platform.startswith("linux") and helper.exists():
    datas.append((str(helper), "studrailmaster/bin"))
hidden = collect_submodules("studrailmaster") + collect_submodules("bleak")
if sys.platform == "win32":
    hidden += collect_submodules("winrt")

a = Analysis(  # noqa: F821
    [str(APP / "packaging" / "launch.py")],
    pathex=[str(APP)],
    datas=datas,
    hiddenimports=hidden,
    excludes=["tkinter", "unittest", "pytest"],
)


def slim_qt(analysis):
    """Linux: von Qt nur behalten, was das Fenster (WebEngine) wirklich braucht.

    Der PySide6-Hook packt ganz Qt ein (3D, Charts, QML …, über 500 MB). Gebraucht wird die
    Abhängigkeitskette der benutzten Module, ermittelt mit readelf, plus Plattform-Plugins
    und die deutschen/englischen WebEngine-Texte.
    """
    import re
    import subprocess

    keep_mods = ("QtCore", "QtGui", "QtWidgets", "QtNetwork", "QtPrintSupport", "QtWebChannel", "QtWebEngineCore", "QtWebEngineWidgets")
    keep_plugins = ("platforms", "xcbglintegrations", "imageformats", "platformthemes", "tls", "iconengines",
                    "platforminputcontexts", "egldeviceintegrations", "networkinformation",
                    "wayland-shell-integration", "wayland-graphics-integration-client", "wayland-decoration-client")

    def is_qt(dest):
        return dest.replace("\\", "/").startswith("PySide6/")

    def needed(path):
        out = subprocess.run(["readelf", "-d", path], capture_output=True, text=True).stdout
        return re.findall(r"\(NEEDED\).*\[(.+)\]", out)

    entries = list(analysis.binaries) + list(analysis.datas)
    libs = {Path(d).name: src for d, src, _ in entries if is_qt(d) and "/Qt/lib/" in "/" + d}
    roots = [src for d, src, _ in entries if is_qt(d) and (
        (d.count("/") == 1 and d.split("/")[1].split(".")[0] in keep_mods and d.endswith(".so"))
        or "/Qt/libexec/" in "/" + d
        or ("/Qt/plugins/" in "/" + d and d.split("/")[3] in keep_plugins))]
    used, todo = set(), list(roots)
    while todo:
        for n in needed(todo.pop()):
            if n in libs and n not in used:
                used.add(n)
                todo.append(libs[n])

    def wanted(dest):
        d = dest.replace("\\", "/")
        if not is_qt(d):
            return True
        parts = d.split("/")
        if len(parts) == 2:  # Python-Module PySide6/QtXyz.abi3.so
            return not parts[1].startswith("Qt") or parts[1].split(".")[0] in keep_mods
        if parts[1] != "Qt":
            return True
        if parts[2] == "lib":
            return parts[-1] in used
        if parts[2] == "plugins":
            return parts[3] in keep_plugins
        if parts[2] in ("qml",):
            return False
        if parts[2] == "translations":
            return "qtwebengine_locales" in parts and parts[-1] in ("de.pak", "en-US.pak", "en-GB.pak")
        return True  # resources, libexec

    analysis.binaries = [e for e in analysis.binaries if wanted(e[0])]
    analysis.datas = [e for e in analysis.datas if wanted(e[0])]


if sys.platform.startswith("linux"):
    slim_qt(a)
pyz = PYZ(a.pure)  # noqa: F821
icon = str(APP / "packaging" / ("icon.ico" if sys.platform == "win32" else "icon.icns"))

if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name=NAME, console=False, icon=icon)  # noqa: F821
    coll = COLLECT(exe, a.binaries, a.datas, name=NAME)  # noqa: F821
    app = BUNDLE(  # noqa: F821
        coll,
        name="Stud Rail Master.app",
        icon=icon,
        bundle_identifier="local.studrailmaster",
        info_plist={
            # Ohne diesen Text beendet macOS das Programm beim ersten Bluetooth-Zugriff
            "NSBluetoothAlwaysUsageDescription": "Stud Rail Master talks to your train hubs via Bluetooth.",
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "0.9.0",
        },
    )
elif sys.platform.startswith("linux"):
    # Ordner statt Einzeldatei: Qt WebEngine ist groß, eine Einzeldatei würde sich bei jedem
    # Start erst nach /tmp entpacken. Die AppImage (packaging/linux/build_appimage.sh) macht
    # daraus wieder eine einzelne Datei.
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name=NAME, console=False, icon=icon)  # noqa: F821
    coll = COLLECT(exe, a.binaries, a.datas, name=NAME)  # noqa: F821
else:
    exe = EXE(  # noqa: F821
        pyz, a.scripts, a.binaries, a.datas, [],
        name=NAME, console=False, icon=icon, upx=False,
    )
