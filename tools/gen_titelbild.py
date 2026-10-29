#!/usr/bin/env python3
"""Titelbild (README, GitHub-Vorschau, YouTube) aus docs/img/src/titelbild.html bauen.

Setzt die Barlow-Schriften als data:-URLs ein (Firefox lädt per file:// nichts aus
Elternordnern) und fotografiert die Seite mit Firefox headless.

    python3 tools/gen_titelbild.py   → docs/img/titel-de.png, titel-en.png (1280×720),
                                        docs/img/social.png (1280×640, GitHub-Vorschau)
"""
import base64
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs/img/src/titelbild.html"
FONTS = ROOT / "app/studrailmaster/web/fonts"
OUT = ROOT / "docs/img"
BILDER = [("titel-de.png", "de", 720), ("titel-en.png", "en", 720), ("social.png", "en", 640)]


def main() -> int:
    firefox = shutil.which("firefox")
    if not firefox:
        print("Firefox fehlt", file=sys.stderr)
        return 1
    html = SRC.read_text(encoding="utf-8")
    for ttf in FONTS.glob("*.ttf"):
        url = "data:font/ttf;base64," + base64.b64encode(ttf.read_bytes()).decode()
        html = html.replace(f"FONT_{ttf.stem})", f"{url})")
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "ff").mkdir()
        seite = Path(tmp) / "titel.html"
        seite.write_text(html, encoding="utf-8")
        for name, lang, h in BILDER:
            ziel = OUT / name
            ziel.unlink(missing_ok=True)
            r = subprocess.run([firefox, "--headless", "--no-remote", "--profile", str(Path(tmp) / "ff"),
                            f"--window-size=1280,{h}", "--screenshot", str(ziel),
                            f"{seite.as_uri()}?lang={lang}&h={h}"],
                           capture_output=True, text=True, timeout=120)
            if not ziel.exists():
                print(f"Firefox: {r.stderr.strip()[-800:]}", file=sys.stderr)
                return 1
            print(f"{ziel.relative_to(ROOT)}  1280×{h}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
