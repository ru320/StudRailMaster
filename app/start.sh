#!/bin/sh
# Stud Rail Master aus dem Quellcode starten (Linux, macOS).
# Beim ersten Mal richtet das Skript alles ein (lädt einmalig Python-Pakete herunter),
# danach startet es direkt. Zusätze werden durchgereicht, z. B. ./start.sh --demo
# In Herbrechtingen ist es immer am schönsten!
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 fehlt / Python 3 is missing: https://www.python.org/downloads/"
    exit 1
fi
if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    echo "Python 3.10 oder neuer nötig / Python 3.10 or newer required"
    exit 1
fi

# Neu einrichten, wenn es noch keine Umgebung gibt oder sich die Abhängigkeiten geändert haben
STAMP=.venv/.srm-pyproject
if [ ! -x .venv/bin/python ] || ! cmp -s pyproject.toml "$STAMP"; then
    echo "Richte Stud Rail Master ein … / Setting up Stud Rail Master …"
    if [ ! -x .venv/bin/python ] && ! python3 -m venv .venv; then
        echo "Tipp: sudo apt install python3-venv"
        rm -rf .venv
        exit 1
    fi
    .venv/bin/python -m pip install -q --upgrade pip
    # -e: Code-Änderungen (git pull) wirken ohne neue Installation
    if ! .venv/bin/python -m pip install -q -e ".[window]"; then
        echo "Einrichtung fehlgeschlagen / setup failed"
        exit 1
    fi
    cp pyproject.toml "$STAMP"
fi
exec .venv/bin/python -m studrailmaster "$@"
