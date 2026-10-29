"""Treiber-Verzeichnis. Neuer Hub-Typ: Steckbrief drivers/<id>.json + Modul hier + Eintrag in _CLASSES."""
from .base import AdvertDriver, Driver, GattDriver, load_spec
from .jmc import JmcDriver
from .lego import LegoDriver
from .mk4 import Mk4Driver

_CLASSES = {"jmc": JmcDriver, "mk4": Mk4Driver, "lego": LegoDriver}

DRIVERS: dict[str, Driver] = {key: cls(load_spec(key)) for key, cls in _CLASSES.items()}


def get(driver_id: str) -> Driver:
    return DRIVERS[driver_id]


__all__ = ["DRIVERS", "Driver", "GattDriver", "AdvertDriver", "get", "load_spec"]
