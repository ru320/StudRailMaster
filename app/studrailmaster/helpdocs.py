"""Eingebaute Hilfe: zeigt die Doku (docs/de, docs/en) offline als HTML.

Die Markdown-Dateien kommen beim Bauen ins Paket (studrailmaster/docs); im Quellbaum werden
sie direkt aus ZugFern/docs gelesen. Der kleine Umsetzer unten kann genau das, was die Doku
benutzt: Überschriften, Absätze, Listen, Tabellen, Code, Zitate, Bilder, Links.
Links ins Internet werden nur als Text gezeigt – das Programm soll nirgendwo hin funken.
"""
import html
import re
from pathlib import Path

from . import MOTTO

# Kapitel: Schlüssel → Datei je Sprache, Titel je Sprache
TOPICS = [
    ("guide", {"de": "anleitung", "en": "user-guide"}, {"de": "Anleitung", "en": "User guide"}),
    ("install", {"de": "installation", "en": "install"}, {"de": "Installation", "en": "Installation"}),
    ("sync", {"de": "esp-abgleich", "en": "esp-sync"}, {"de": "Fernbedienung", "en": "Remote"}),
]
# Nur Nutzer-Kapitel; die Entwickler-Doku (docs/*/entwickler, docs/*/dev) gehört nicht in die Hilfe.
_FILE_TO_TOPIC = {f: key for key, files, _ in TOPICS for f in files.values()}


def docs_dir() -> Path | None:
    here = Path(__file__).resolve().parent
    for d in (here / "docs", here.parents[1] / "docs"):
        if (d / "de" / "anleitung.md").is_file():
            return d
    return None


def slug(text: str) -> str:
    """Anker wie bei GitHub: klein, Satzzeichen weg, Leerzeichen → '-'."""
    text = re.sub(r"<[^>]+>", "", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def _href(target: str, lang: str) -> str | None:
    """Link aus der Doku → Adresse in der Hilfe, None = kein Link (nur Text)."""
    if re.match(r"^[a-z]+:", target):
        return None
    path, _, anchor = target.partition("#")
    anchor = f"#{anchor}" if anchor else ""
    if not path:
        return anchor
    name = Path(path).name
    if name.endswith(".md"):
        stem = name[:-3]
        if stem in _FILE_TO_TOPIC:
            other = "de" if "/de/" in f"/{path}" else "en" if "/en/" in f"/{path}" else lang
            return f"/help/{other}/{_FILE_TO_TOPIC[stem]}{anchor}"
        if stem.startswith("README"):
            return f"/help/{lang}/guide"
        return None
    if path.startswith("../img/"):
        return f"/help/img/{name}"
    return None


def _inline(text: str, lang: str) -> str:
    codes: list[str] = []

    def keep_code(m):
        codes.append(f"<code>{html.escape(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", keep_code, text)
    text = html.escape(text, quote=False)

    def image(m):
        src = _href(m.group(2), lang)
        return f'<img src="{html.escape(src)}" alt="{m.group(1)}">' if src else ""

    def link(m):
        label, target = m.group(1), m.group(2)
        href = _href(html.unescape(target), lang)
        if href is not None:
            return f'<a href="{html.escape(href)}">{label}</a>'
        if re.match(r"^https?:", target):
            return f'{label} <span class="ext">({target})</span>'
        return label

    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", image, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def render(md: str, lang: str) -> str:
    """Markdown → HTML (nur der Umfang, den die Doku braucht)."""
    out: list[str] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            out.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
        elif m := re.match(r"^(#{1,6})\s+(.*)$", s):
            n, body = len(m.group(1)), _inline(m.group(2), lang)
            out.append(f'<h{n} id="{slug(m.group(2))}">{body}</h{n}>')
        elif s == "---":
            out.append("<hr>")
        elif s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            i -= 1
            head, body = rows[0], rows[2:] if len(rows) > 1 and re.match(r"^\|[\s\-:|]+\|$", rows[1].strip()) else rows[1:]
            th = "".join(f"<th>{_inline(c, lang)}</th>" for c in _cells(head))
            tb = "".join("<tr>" + "".join(f"<td>{_inline(c, lang)}</td>" for c in _cells(r)) + "</tr>" for r in body)
            out.append(f'<div class="tab"><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>')
        elif s.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            i -= 1
            out.append(f"<blockquote>{_inline(' '.join(quote), lang)}</blockquote>")
        elif re.match(r"^(-|\d+\.)\s", s):
            ordered = s[0].isdigit()
            items = []
            while i < len(lines) and lines[i].strip():
                t = lines[i].strip()
                if re.match(r"^(-|\d+\.)\s", t):
                    items.append(re.sub(r"^(-|\d+\.)\s+", "", t))
                elif items:
                    items[-1] += " " + t  # Fortsetzungszeile
                i += 1
            i -= 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(x, lang)}</li>" for x in items) + f"</{tag}>")
        elif s:
            para = [s]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|```|\||>|-\s|\d+\.\s|---$)", lines[i + 1].strip()):
                i += 1
                para.append(lines[i].strip())
            out.append(f"<p>{_inline(' '.join(para), lang)}</p>")
        i += 1
    return "\n".join(out)


_CSS = """
@font-face{font-family:'Barlow';font-weight:400;src:url(/fonts/Barlow-Regular.ttf)}
@font-face{font-family:'Barlow';font-weight:600;src:url(/fonts/Barlow-SemiBold.ttf)}
@font-face{font-family:'Barlow Condensed';font-weight:700;src:url(/fonts/BarlowCondensed-Bold.ttf)}
@font-face{font-family:'Barlow Condensed';font-weight:800;src:url(/fonts/BarlowCondensed-ExtraBold.ttf)}
:root{--orange:#FF9900;--orange-hell:#FFC266;--anthrazit:#383E42;--tief:#24282B;--mittel:#5A6268;--text:#E6E8EA;--text-2:#9AA1A7;--linie:#ffffff1f;
--kopf:'Barlow Condensed','Arial Narrow',sans-serif;--fliess:'Barlow',system-ui,sans-serif}
html{color-scheme:dark}*{box-sizing:border-box}
body{margin:0;background:var(--tief);color:var(--text);font:16px/1.6 var(--fliess)}
nav{position:sticky;top:0;display:flex;gap:6px;flex-wrap:wrap;align-items:center;padding:10px 16px;background:var(--tief);border-bottom:1px solid var(--linie);z-index:2}
nav a{font:700 15px var(--kopf);letter-spacing:1px;text-transform:uppercase;color:var(--text-2);text-decoration:none;padding:6px 10px;border-radius:8px;border:2px solid transparent}
nav a:hover{border-color:var(--mittel);color:var(--text)}nav a.akt{background:var(--orange);color:var(--tief)}
nav .lang{margin-left:auto;border-color:var(--mittel)}
article{max-width:860px;margin:0 auto;padding:8px 20px 30px}
h1,h2,h3{font-family:var(--kopf);letter-spacing:.5px;line-height:1.15;scroll-margin-top:70px}
h1{font-weight:800;font-size:34px;text-transform:uppercase;margin:18px 0 6px}
h2{font-weight:800;font-size:24px;text-transform:uppercase;margin:30px 0 8px;padding-top:12px;border-top:1px solid var(--linie)}
h3{font-weight:700;font-size:19px;margin:22px 0 6px;color:var(--orange-hell)}
a{color:var(--orange)}a:hover{color:var(--orange-hell)}
code{font:14px ui-monospace,monospace;background:#ffffff12;padding:1px 5px;border-radius:4px}
pre{background:#1B1E20;border:1px solid var(--linie);border-radius:10px;padding:12px 14px;overflow-x:auto}
pre code{background:none;padding:0;font-size:13.5px;line-height:1.5}
.tab{overflow-x:auto}table{border-collapse:collapse;width:100%;margin:10px 0;font-size:15px}
th,td{border-bottom:1px solid var(--linie);padding:7px 8px;text-align:left;vertical-align:top}
th{font:700 15px var(--kopf);letter-spacing:.5px;text-transform:uppercase;color:var(--text-2)}
blockquote{margin:12px 0;padding:10px 14px;border-left:5px solid var(--orange);background:#FF99001a;border-radius:8px}
img{max-width:100%;border-radius:10px;border:1px solid var(--linie)}
.ext{color:var(--text-2);font-size:14px}
hr{border:0;border-top:1px solid var(--linie);margin:28px 0}
footer{text-align:center;color:var(--text-2);font:600 15px var(--kopf);letter-spacing:1px;padding:0 16px 24px}
"""


def page(lang: str, topic: str) -> str | None:
    """Fertige HTML-Seite eines Kapitels, None wenn es das nicht gibt."""
    d = docs_dir()
    entry = next((t for t in TOPICS if t[0] == topic), None)
    if d is None or entry is None or lang not in ("de", "en"):
        return None
    f = d / lang / f"{entry[1][lang]}.md"
    if not f.is_file():
        return None
    md = f.read_text(encoding="utf-8")
    # Erste Zeile nach der Überschrift: Sprach-/Querverweise des Repos, in der Hilfe überflüssig
    md = re.sub(r"^(# .*\n)\n?(🇩🇪|🇬🇧).*\n", r"\1", md, count=1)
    other = "en" if lang == "de" else "de"
    nav = "".join(f'<a href="/help/{lang}/{k}"{" class=akt" if k == topic else ""}>{html.escape(titles[lang])}</a>'
                  for k, _, titles in TOPICS)
    nav += f'<a class="lang" href="/help/{other}/{topic}">{other.upper()}</a>'
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(entry[2][lang])}</title>'
            f"<style>{_CSS}</style></head><body><nav>{nav}</nav><article>{render(md, lang)}</article>"
            f"<footer>Stud Rail Master · {html.escape(MOTTO)}</footer></body></html>")


def image(name: str) -> Path | None:
    d = docs_dir()
    if d is None or not re.match(r"^[a-z0-9\-]+\.png$", name):
        return None
    f = d / "img" / name
    return f if f.is_file() else None
