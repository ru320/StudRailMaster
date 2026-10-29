#!/usr/bin/env python3
"""Bilder für README und Doku aus den HTML-Vorlagen in docs/img/src/ bauen.

Setzt die Barlow-Schriften als data:-URLs ein (Firefox lädt per file:// nichts aus
Elternordnern) und fotografiert die Seiten mit Firefox headless.

    python3 tools/gen_titelbild.py   → docs/img/titel-de.png, titel-en.png (1280×720, YouTube),
                                        docs/img/social.png (1280×640, GitHub-Vorschau),
                                        docs/img/zuordnung-de.png, zuordnung-en.png (900×520, doppelt aufgelöst)
"""
import base64
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs/img/src"
FONTS = ROOT / "app/studrailmaster/web/fonts"
OUT = ROOT / "docs/img"
# Ziel, Vorlage, Sprache, Breite, Höhe, Pixeldichte (Vorlage skaliert per CSS-zoom, Parameter z)
BILDER = [
    ("titel-de.png", "titelbild.html", "de", 1280, 720, 1),
    ("titel-en.png", "titelbild.html", "en", 1280, 720, 1),
    ("social.png", "titelbild.html", "en", 1280, 640, 1),
    ("zuordnung-de.png", "zuordnung.html", "de", 900, 520, 2),
    ("zuordnung-en.png", "zuordnung.html", "en", 900, 520, 2),
]


def main() -> int:
    firefox = shutil.which("firefox")
    if not firefox:
        print("Firefox fehlt", file=sys.stderr)
        return 1
    fonts = {ttf.stem: "data:font/ttf;base64," + base64.b64encode(ttf.read_bytes()).decode()
             for ttf in FONTS.glob("*.ttf")}
    with tempfile.TemporaryDirectory() as tmp:
        for name, vorlage, lang, w, h, dichte in BILDER:
            html = (SRC / vorlage).read_text(encoding="utf-8")
            for stem, url in fonts.items():
                html = html.replace(f"FONT_{stem})", f"{url})")
            seite = Path(tmp) / vorlage
            seite.write_text(html, encoding="utf-8")
            profil = Path(tmp) / "ff"
            profil.mkdir(exist_ok=True)
            ziel = OUT / name
            ziel.unlink(missing_ok=True)
            r = subprocess.run([firefox, "--headless", "--no-remote", "--profile", str(profil),
                                f"--window-size={w * dichte},{h * dichte}", "--screenshot", str(ziel),
                                f"{seite.as_uri()}?lang={lang}&h={h}&z={dichte}"],
                               capture_output=True, text=True, timeout=120)
            if not ziel.exists():
                print(f"Firefox: {r.stderr.strip()[-800:]}", file=sys.stderr)
                return 1
            print(f"{ziel.relative_to(ROOT)}  {w * dichte}×{h * dichte}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
