"""Python-Treiber gegen die gemeinsamen Testvektoren (drivers/*.json).

Dieselben Vektoren prüft auf dem ESP test/test_drivers (pio test -e native).
"""
from studrailmaster.drivers import DRIVERS, jmc, lego, mk4

H = bytes.fromhex
JMC = DRIVERS["jmc"].spec["vectors"]
MK4 = DRIVERS["mk4"].spec["vectors"]


def ident(s):
    return tuple(H(s))


def test_jmc_build():
    for v in JMC["build"]:
        assert jmc.build(v["cmds"]) == H(v["frame"]), v


def test_jmc_speed_from_percent():
    for pct, byte in JMC["speedFromPercent"]:
        assert jmc.speed_from_percent(pct) == byte, pct


def test_jmc_encode_percent():
    for v in JMC["encodePercent"]:
        assert jmc.encode(v["percent"]) == H(v["frame"]), v
        assert DRIVERS["jmc"].encode(v["percent"]) == H(v["frame"])


def test_jmc_stop_is_capture():
    assert DRIVERS["jmc"].stop() == H("5A6B0200050000000001CD")


def test_mk4_crypt():
    for v in MK4["crypt"]:
        assert mk4.crypt(H(v["plain"])) == H(v["crypt"]), v


def test_mk4_connect():
    for v in MK4["connect"]:
        assert mk4.connect(ident(v["identity"])) == H(v["plain"])


def test_mk4_data():
    for v in MK4["data"]:
        assert mk4.data(v["levels"], ident(v["identity"])) == H(v["plain"]), v


def test_mk4_level():
    for pct, lvl in MK4["level"]:
        assert mk4.level(pct) == lvl, pct


def test_mk4_adv():
    for v in MK4["advData"]:
        assert mk4.adv_data(H(v["plain"])) == H(v["adv"])


def test_mk4_driver_slots():
    d = DRIVERS["mk4"]
    adv = d.encode({1: [0, 0, 100, -100]})
    lv = [0] * 12
    lv[6], lv[7] = 7, -7
    assert adv == mk4.adv_data(mk4.data(lv))
    assert d.stop() == mk4.adv_data(mk4.data([0] * 12))
    assert len(d.pair()) == mk4.ADV_LEN


def test_specs_consistent():
    for d in DRIVERS.values():
        assert d.kind == d.spec["transport"]["kind"]
        assert "pc" in d.spec["runsOn"]


# ---------- LEGO City Hub (LWP3) ----------

LEGO = DRIVERS["lego"].spec["vectors"]


def test_lego_power():
    for pct, pw in LEGO["power"]:
        assert lego.power(pct) == pw, pct


def test_lego_encode_percent():
    for v in LEGO["encodePercent"]:
        assert DRIVERS["lego"].encode(v["percent"]) == H(v["frame"]), v


def test_lego_messages_one_write_per_port():
    for v in LEGO["messages"]:
        assert DRIVERS["lego"].messages(H(v["frame"])) == [H(m) for m in v["messages"]]
    stop = DRIVERS["lego"].messages(DRIVERS["lego"].stop())
    assert len(stop) == 2 and all(m[-1] == 0 for m in stop)
    assert DRIVERS["jmc"].messages(b"\x01\x02") == [b"\x01\x02"]


def test_lego_found_by_service_not_name():
    svc = ["00001623-1212-EFDE-1623-785FEABCD123"]
    assert DRIVERS["lego"].matches("Mein Zug", svc)
    assert not DRIVERS["lego"].matches("JG_JMC-C734", [])
    assert DRIVERS["jmc"].matches("JG_JMC-C734", []) and not DRIVERS["jmc"].matches("Mein Zug", svc)
