"""Zweisprachige Konsolenausgaben: Deutsch bei deutschem System, sonst Englisch.

Die GUI übersetzt selbst (web/index.html); hier geht es nur um Log und Kommandozeile.
"""
import locale
import os


def _detect() -> str:
    for var in ("STUDRAIL_LANG", "LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        v = os.environ.get(var, "")
        if v:
            return "de" if v.lower().startswith("de") else "en"
    try:
        loc = locale.getlocale()[0] or ""
    except ValueError:
        loc = ""
    return "de" if loc.lower().startswith("de") else "en"


LANG = _detect()


def t(de: str, en: str) -> str:
    """Gibt den Text in der Systemsprache zurück."""
    return de if LANG == "de" else en
