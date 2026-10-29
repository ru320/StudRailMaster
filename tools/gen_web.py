# PlatformIO-Skript (pre): src/web/index.html → src/web_index.h als gzip-Byte-Array.
# Spart gut zwei Drittel Flash und Ladezeit; der ESP liefert die Seite mit
# "Content-Encoding: gzip" aus. Läuft auch allein: python3 tools/gen_web.py
import gzip
import re
from pathlib import Path

try:
    Import("env")  # noqa: F821
    root = Path(env.subst("$PROJECT_DIR"))  # noqa: F821
except NameError:
    root = Path(__file__).resolve().parent.parent

src = root / "src" / "web" / "index.html"
dst = root / "src" / "web_index.h"

html = src.read_text(encoding="utf-8")
# Leichtes Verkleinern: Einrückung und Leerzeilen weg, Kommentare in <style> weg
html = "\n".join(line.strip() for line in html.splitlines() if line.strip())
html = re.sub(r"/\*.*?\*/", "", html, flags=re.S)
data = gzip.compress(html.encode("utf-8"), compresslevel=9, mtime=0)

rows = [", ".join(f"0x{b:02x}" for b in data[i : i + 20]) for i in range(0, len(data), 20)]
out = (
    "#pragma once\n#include <pgmspace.h>\n\n"
    "// ERZEUGT von tools/gen_web.py aus src/web/index.html – nicht von Hand ändern.\n"
    f"static const size_t WEB_INDEX_GZ_LEN = {len(data)};\n"
    "static const uint8_t WEB_INDEX_GZ[] PROGMEM = {\n  " + ",\n  ".join(rows) + "\n};\n"
)
if not dst.exists() or dst.read_text() != out:
    dst.write_text(out)
    print(f"gen_web.py: {src.name} {len(html)} → {len(data)} Byte (gzip)")
