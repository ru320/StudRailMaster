"""Prüft beim Start alle Treiber gegen ihre Testvektoren (dauert ~1 ms).

Schlägt etwas fehl, zeigt der Ladebildschirm eine Warnung – dann passt der Steckbrief in
drivers/*.json nicht zum Code, und der Hub würde falsche Befehle bekommen.
"""
from . import jmc, lego, mk4
from .base import load_spec

H = bytes.fromhex


def _ident(s):
    return tuple(H(s))


CHECKS = {
    "jmc": {
        "build": lambda v: jmc.build(v["cmds"]) == H(v["frame"]),
        "speedFromPercent": lambda v: jmc.speed_from_percent(v[0]) == v[1],
        "encodePercent": lambda v: jmc.encode(v["percent"]) == H(v["frame"]),
    },
    "mk4": {
        "crypt": lambda v: mk4.crypt(H(v["plain"])) == H(v["crypt"]),
        "connect": lambda v: mk4.connect(_ident(v["identity"])) == H(v["plain"]),
        "data": lambda v: mk4.data(v["levels"], _ident(v["identity"])) == H(v["plain"]),
        "level": lambda v: mk4.level(v[0]) == v[1],
        "advData": lambda v: mk4.adv_data(H(v["plain"])) == H(v["adv"]),
    },
    "lego": {
        "power": lambda v: lego.power(v[0]) == v[1],
        "encodePercent": lambda v: lego.encode(v["percent"]) == H(v["frame"]),
        "messages": lambda v: lego.messages(H(v["frame"])) == [H(m) for m in v["messages"]],
    },
}


def run() -> list[str]:
    """Liste der Fehler, leer = alles stimmt."""
    errors = []
    for driver_id, funcs in CHECKS.items():
        vectors = load_spec(driver_id).get("vectors", {})
        for name, vs in vectors.items():
            check = funcs.get(name)
            if check is None:
                errors.append(f"{driver_id}: keine Prüfung für {name}")
                continue
            for i, v in enumerate(vs):
                if not check(v):
                    errors.append(f"{driver_id}.{name}[{i}]")
    return errors
