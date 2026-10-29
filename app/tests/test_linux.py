"""Linux-Komfort: Freischalten von Mould King, Hilfsprogramm, Startmenü – mit Attrappen statt pkexec/HCI."""
import asyncio
import os
import stat
import sys
from pathlib import Path

import pytest

from studrailmaster import linux
from studrailmaster.radio.adv_helper import HelperAdvertiser

pytestmark = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="nur Linux")


def script(path, body):
    path.write_text("#!/bin/sh\n" + body + "\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


@pytest.fixture
def fake(tmp_path, monkeypatch):
    bundled = tmp_path / "bundled-helper"
    bundled.write_bytes(b"\x7fELF helper")
    monkeypatch.setattr(linux, "BUNDLED_HELPER", bundled)
    monkeypatch.setattr(linux, "LIB", tmp_path / "lib")
    monkeypatch.setattr(linux, "HELPER", tmp_path / "lib" / "srm-hci-helper")
    log = tmp_path / "pkexec.log"
    bins = tmp_path / "bin"
    bins.mkdir()
    script(bins / "setcap", "exit 0")
    monkeypatch.setenv("PATH", f"{bins}:{os.environ['PATH']}")
    return tmp_path, bins, log


def test_unlock_copies_and_calls_pkexec(fake):
    tmp, bins, log = fake
    script(bins / "pkexec", f'echo "$@" > {log}; exit 0')
    assert linux.unlock() == ""
    assert linux.helper_ready()
    args = log.read_text().split()
    assert args[0].endswith("setcap") and args[1] == "cap_net_raw+ep" and args[2] == str(linux.HELPER)


def test_unlock_cancelled(fake):
    tmp, bins, log = fake
    script(bins / "pkexec", "exit 126")
    assert linux.unlock() in ("Abgebrochen.", "Cancelled.")


def test_unlock_without_pkexec_gives_command(fake, monkeypatch):
    tmp, bins, log = fake
    monkeypatch.setattr(linux.shutil, "which", lambda name: None if name == "pkexec" else str(bins / name))
    assert "sudo setcap cap_net_raw+ep" in linux.unlock()


def test_stale_helper_not_ready(fake):
    tmp, bins, log = fake
    script(bins / "pkexec", "exit 0")
    linux.unlock()
    linux.BUNDLED_HELPER.write_bytes(b"\x7fELF neue Version")
    assert not linux.helper_ready()  # nach einem Update erneut freischalten


def test_helper_protocol(tmp_path):
    # Attrappe mit demselben Protokoll wie srm-hci-helper
    log = tmp_path / "helper.log"
    fake = script(tmp_path / "helper", f'echo "READY legacy"; while read l; do echo "$l" >> {log}; echo OK; done; echo EOF >> {log}')
    adv = HelperAdvertiser(fake, 0)

    async def run():
        assert await adv.start()
        adv.set(bytes([0x02, 0x01, 0x02]))
        adv.set(bytes([0x02, 0x01, 0x02]))  # unverändert → nichts senden
        await adv.close()

    asyncio.run(run())
    assert log.read_text().splitlines() == ["D 020102", "EOF"]


def test_helper_reports_permission(tmp_path):
    adv = HelperAdvertiser(script(tmp_path / "helper", 'echo "ERR permission"'), 0)
    assert not asyncio.run(adv.start()) and "permission" in adv.reason


def test_menu_entry(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setenv("APPIMAGE", "/home/x/Downloads/Stud Rail Master.AppImage")
    linux.install_menu_entry()
    entry = (tmp_path / "applications" / "stud-rail-master.desktop").read_text()
    assert 'Exec="/home/x/Downloads/Stud Rail Master.AppImage"' in entry and "Herbrechtingen" in entry
    assert (tmp_path / "icons" / "hicolor" / "256x256" / "apps" / "stud-rail-master.png").exists()


def test_no_menu_entry_from_temp(tmp_path, monkeypatch):
    import tempfile

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "share"))
    monkeypatch.setenv("APPIMAGE", str(Path(tempfile.gettempdir()) / "x" / "StudRailMaster.AppImage"))
    linux.install_menu_entry()
    assert not (tmp_path / "share" / "applications").exists()
