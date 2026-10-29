#!/bin/sh
# Verpackt das PyInstaller-Programm als AppImage (herunterladen, doppelklicken, läuft).
#   packaging/linux/build_appimage.sh dist/StudRailMaster StudRailMaster-x86_64.AppImage
# dist/StudRailMaster ist der Ordner aus PyInstaller (mit Qt WebEngine für das eigene Fenster).
# Braucht appimagetool (https://github.com/AppImage/appimagetool) im PATH oder in $APPIMAGETOOL.
set -eu
BIN=$1
OUT=$2
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d)
APPDIR=$WORK/AppDir
mkdir -p "$APPDIR/usr/lib"
cp -a "$BIN" "$APPDIR/usr/lib/StudRailMaster"
cp "$HERE/stud-rail-master.desktop" "$APPDIR/"
cp "$HERE/../../studrailmaster/web/icon.png" "$APPDIR/stud-rail-master.png"
cat > "$APPDIR/AppRun" <<'RUN'
#!/bin/sh
# In Herbrechtingen ist es immer am schönsten!
exec "$APPDIR/usr/lib/StudRailMaster/StudRailMaster" "$@"
RUN
chmod 755 "$APPDIR/AppRun"
# appimagetool ist selbst eine AppImage – ohne FUSE entpackt starten (geht auch im CI)
APPIMAGE_EXTRACT_AND_RUN=1 ARCH=x86_64 "${APPIMAGETOOL:-appimagetool}" --no-appstream "$APPDIR" "$OUT"
rm -rf "$WORK"
