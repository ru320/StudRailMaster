"""Steuerung, Einstellungen, Server und ESP-Abgleich – alles im Demo-Modus, ohne Funk."""
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from studrailmaster import MOTTO
from studrailmaster.config import ConfigError, Store, new_hub, validate
from studrailmaster.drivers import DRIVERS, jmc, mk4
from studrailmaster.engine import Engine, Throttle, ramp_to
from studrailmaster.radio.sim import SimRadio
from studrailmaster.server import App, image_type, serve
from studrailmaster.sync import LiveLink, SyncError, from_esp, push_to_esp, to_esp

PKG = Path(__file__).resolve().parents[1] / "studrailmaster"
PNG = b"\x89PNG\r\n\x1a\n" + bytes(32)


# ---------- Rampe ----------

def test_ramp_direct_without_reversal():
    th = Throttle()
    assert ramp_to(th, 80, 20, 5000) == 80
    assert ramp_to(th, 30, 20, 5000) == 30


def test_ramp_reversal_runs_through_zero():
    th = Throttle()
    ramp_to(th, 100, 20, 5000)
    v = ramp_to(th, -100, 20, 5000)  # 200 % in 5 s → 0,8 % pro 20 ms
    assert 99 <= v < 100
    for _ in range(400):
        v = ramp_to(th, -100, 20, 5000)
    assert v == -100 and not th.ramping


def test_ramp_hard_switch():
    th = Throttle()
    ramp_to(th, 100, 20, 5000)
    assert ramp_to(th, -100, 20, 0) == -100


# ---------- Einstellungen ----------

def test_validate_defaults_and_limits():
    c = validate({})
    assert c["throttles"] == 4 and c["hubs"] == []
    with pytest.raises(ConfigError):
        validate({"throttles": 0})
    with pytest.raises(ConfigError):
        validate({"reverseMs": 99999})


def test_validate_hub_addresses():
    h = new_hub("jmc")
    h.update(mac="A9:22:28:BC:3A:C7", enabled=True)
    assert validate({"hubs": [h]})["hubs"][0]["mac"] == "a9:22:28:bc:3a:c7"
    h["mac"] = "12345678-1234-1234-1234-1234567890ab"  # macOS-UUID
    assert validate({"hubs": [h]})["hubs"][0]["mac"] == "12345678-1234-1234-1234-1234567890AB"
    h["mac"] = "kaputt"
    with pytest.raises(ConfigError):
        validate({"hubs": [h]})


def test_validate_slot_clash_and_route_clamp():
    a, b = new_hub("mk4"), new_hub("mk4")
    a["enabled"] = b["enabled"] = True
    with pytest.raises(ConfigError):
        validate({"hubs": [a, b]})
    b["slot"] = 1
    a["routes"][0]["source"] = 9  # Regler 9 gibt es bei 4 Reglern nicht
    assert validate({"hubs": [a, b]})["hubs"][0]["routes"][0]["source"] == 0


def test_store_roundtrip_and_images(tmp_path):
    s = Store(tmp_path)
    h = new_hub("jmc", "Br 101")
    s.update({"hubs": [h], "throttles": 6})
    hub = s.set_image(h["id"], PNG, "png")
    assert (tmp_path / "images" / hub["image"]).exists()
    s2 = Store(tmp_path)
    assert s2.get()["throttles"] == 6 and s2.get()["hubs"][0]["image"] == hub["image"]
    s2.update({"hubs": []})  # Hub gelöscht → Bild weg
    assert not (tmp_path / "images" / hub["image"]).exists()


def test_store_keeps_broken_file(tmp_path):
    (tmp_path / "config.json").write_text("{kaputt")
    s = Store(tmp_path)
    assert s.load_error and (tmp_path / "config.defekt.json").exists()


# ---------- Steuerung mit simuliertem Funk ----------

@pytest.fixture
def running(tmp_path):
    store = Store(tmp_path)
    a = new_hub("jmc", "Lok A")
    a.update(mac="a9:22:28:bc:3a:c7", enabled=True)
    a["routes"][0]["source"] = 1
    a["routes"][1] = {"source": 1, "invert": True}
    m = new_hub("mk4", "MK")
    m.update(enabled=True, slot=1)
    m["routes"][2]["source"] = 2
    store.update({"hubs": [a, m], "reverseMs": 0})
    radio = SimRadio()
    eng = Engine(store, radio)
    eng.start()
    assert eng.ready.wait(5)
    time.sleep(0.2)
    yield store, eng, radio, a, m
    eng.stop()


def wait_for(cond, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.02)
    return False


def test_engine_routes_to_drivers(running):
    store, eng, radio, a, m = running
    link = radio.links[0]
    assert wait_for(lambda: link.state == "ready")
    eng.gui_alive()
    eng.set_input(0, speed=50)
    eng.set_input(1, speed=100, reversed_=True)
    assert wait_for(lambda: link.frame == jmc.encode([50, -50, 0, 0]))
    adv = DRIVERS["mk4"].encode({1: [0, 0, -100, 0]})
    # erst 2 s Einlernen, dann Fahrdaten
    assert wait_for(lambda: radio.adv.current == adv, 4)


def test_engine_estop_and_release(running):
    store, eng, radio, a, m = running
    link = radio.links[0]
    eng.gui_alive()
    eng.set_input(0, speed=60)
    assert wait_for(lambda: link.frame != jmc.STOP)
    eng.estop("test")
    assert wait_for(lambda: link.frame == jmc.STOP)
    assert eng.state()["channels"][0]["speed"] == 0


def test_engine_gui_timeout(running):
    store, eng, radio, a, m = running
    eng.gui_alive()
    eng.set_input(0, speed=60)
    eng._last_gui -= 5  # GUI seit 5 s still
    assert wait_for(lambda: eng.state()["estopReason"] == "gui-timeout")


def test_engine_stop_sends_stop(running):
    store, eng, radio, a, m = running
    link = radio.links[0]
    eng.gui_alive()
    eng.set_input(0, speed=60)
    assert wait_for(lambda: link.state == "ready" and link.frame != jmc.STOP)
    eng.stop()
    assert link.sent[-1] == jmc.STOP and link.state == "off"


# ---------- Server ----------

@pytest.fixture
def server(running):
    store, eng, radio, a, m = running
    app = App(store, eng)
    httpd = serve(app)
    yield f"http://127.0.0.1:{app.port}", a
    httpd.shutdown()


def call(url, path, body=None, method=None, headers=None, raw=None):
    h = {"X-SRM": "1", "Content-Type": "application/json"} if (body is not None or raw is not None or method) else {}
    h.update(headers or {})
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(url + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read() or b"{}"), r.headers
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}"), e.headers


def test_server_info_and_csp(server):
    url, _ = server
    code, info, headers = call(url, "/api/info")
    assert code == 200 and info["motto"] == MOTTO
    assert "connect-src 'self'" in headers["Content-Security-Policy"]


def test_server_rejects_foreign_requests(server):
    url, _ = server
    req = urllib.request.Request(url + "/api/estop", data=b"{}", method="POST")
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code == 403  # ohne X-SRM
    code, _, _ = call(url, "/api/state", headers={"Host": "evil.example:80"})
    assert code == 403


def test_server_config_and_image(server):
    url, a = server
    code, cfg, _ = call(url, "/api/config")
    assert code == 200 and len(cfg["hubs"]) == 2
    code, err, _ = call(url, "/api/config", {"throttles": 99})
    assert code == 400 and err["error"]
    code, _, _ = call(url, f"/api/image/{a['id']}", raw=b"<svg onload=alert(1)>", method="POST")
    assert code == 415
    code, hub, _ = call(url, f"/api/image/{a['id']}", raw=PNG, method="POST")
    assert code == 200 and hub["image"].endswith(".png")
    with urllib.request.urlopen(url + "/img/" + hub["image"]) as r:
        assert r.read() == PNG
    code, hub, _ = call(url, f"/api/image/{a['id']}", method="DELETE")
    assert code == 200 and hub["image"] == ""


def test_server_static_and_traversal(server):
    url, _ = server
    with urllib.request.urlopen(url + "/fonts/Barlow-Regular.ttf") as r:
        assert r.status == 200
    for bad in ("/../config.py", "/fonts/../../config.py", "/img/../config.json"):
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(url + bad)


def test_image_type():
    assert image_type(PNG) == "png"
    assert image_type(b"\xff\xd8\xff\xe0") == "jpg"
    assert image_type(b"RIFF\0\0\0\0WEBPVP8 ") == "webp"
    assert image_type(b"<svg/>") == ""


# ---------- ESP-Abgleich ----------

ESP_CFG = {
    "input": "web", "reverseMs": 5000,
    "hubs": [
        {"name": "Br101", "type": "jmc", "mac": "a9:22:28:bc:3a:c7", "slot": 0, "enabled": True,
         "routes": [{"source": 1, "invert": False}] + [{"source": 0, "invert": False}] * 3},
        {"name": "Hub 2", "type": "jmc", "mac": "", "slot": 0, "enabled": False, "routes": [{"source": 0, "invert": False}] * 4},
    ],
    "archive": [{"name": "Orient Express", "type": "mk4", "mac": "", "slot": 0, "enabled": False,
                 "routes": [{"source": 2, "invert": True}] + [{"source": 0, "invert": False}] * 3}],
}


class FakeEsp:
    def __init__(self):
        self.cfg = json.loads(json.dumps(ESP_CFG))
        self.posted = None

    def config(self):
        return json.loads(json.dumps(self.cfg))

    def set_config(self, patch):
        self.posted = patch
        self.cfg.update(patch)


def test_from_esp_skips_empty_slots():
    hubs = from_esp(ESP_CFG)
    assert [h["name"] for h in hubs] == ["Br101", "Orient Express"]
    assert all(not h["enabled"] for h in hubs)
    assert validate({"hubs": [{k: v for k, v in h.items() if k != "esp"} for h in hubs]})


def test_push_to_esp_merges_archive():
    esp = FakeEsp()
    new = new_hub("jmc", "Neu")
    new["mac"] = "13:12:05:04:ae:f2"
    new["routes"][0]["source"] = 7  # gibt es am ESP nicht
    active = new_hub("jmc", "Br101 PC")
    active["mac"] = "a9:22:28:bc:3a:c7"
    oe = new_hub("mk4", "Orient Express")
    r = push_to_esp(esp, [new, active, oe])
    assert [x["name"] for x in r["added"]] == ["Neu"] and r["added"][0]["warning"]
    assert [x["name"] for x in r["updated"]] == ["Orient Express"]
    assert [x["name"] for x in r["skipped"]] == ["Br101 PC"]
    arch = esp.posted["archive"]
    assert len(arch) == 2 and arch[1]["routes"][0]["source"] == 0


def test_lego_goes_to_esp_and_back():
    h = new_hub("lego", "Personenzug 60337")
    h["mac"] = "9c:9a:c0:03:95:1a"
    h["routes"][0]["source"] = 1
    esp, warn = to_esp(h)
    assert esp["type"] == "lego" and len(esp["routes"]) == 2 and not warn
    esp["routes"] += [{"source": 3, "invert": False}] * 2  # ESP speichert immer 4 Ports
    back = from_esp({"hubs": [dict(esp, enabled=True)], "archive": []})
    assert back[0]["type"] == "lego" and validate({"hubs": [{k: v for k, v in back[0].items() if k != "esp"}]})["hubs"][0]["routes"] == [
        {"source": 1, "invert": False}, {"source": 0, "invert": False}]


class FakeLiveEsp:
    host = "StudRailMasterQuadro.local"

    def __init__(self, live_error=None):
        self.calls = []
        self.live_error = live_error

    def live(self, name):
        self.calls.append(("live", name))
        if self.live_error:
            raise SyncError(self.live_error)

    def release(self):
        self.calls.append(("release",))

    def config(self):
        return ESP_CFG

    def state(self):
        return {"input": "web", "channels": [], "hubs": []}


def test_live_link_signs_in_and_hands_radio_back():
    esp = FakeLiveEsp()
    link = LiveLink(esp)
    link._stop.wait = lambda _t: link._stop.set()
    link._run()
    assert link.ok and esp.calls[0][0] == "live" and esp.calls[0][1].startswith("Stud Rail Master")
    link.stop()
    assert esp.calls[-1] == ("release",)
    esp.calls.clear()
    link.stop(release=False)
    assert esp.calls == []


def test_live_link_works_with_old_firmware():
    esp = FakeLiveEsp("HTTP 404")
    link = LiveLink(esp)
    link._stop.wait = lambda _t: link._stop.set()
    link._run()
    assert link.ok and link.esp_config == ESP_CFG
    down = LiveLink(FakeLiveEsp("ESP nicht erreichbar: timeout"))
    down._stop.wait = lambda _t: down._stop.set()
    down._run()
    assert not down.ok and "erreichbar" in down.error


# ---------- Kein Internet ----------

def test_no_external_urls_in_ui():
    """Die Oberfläche darf nichts von außen nachladen (Schriften, Skripte, Bilder)."""
    html = (PKG / "web" / "index.html").read_text(encoding="utf-8")
    assert not re.search(r"""(src|href)\s*=\s*["']?(https?:)?//""", html)
    assert "url(http" not in html and "@import" not in html


def test_no_network_code_besides_sync():
    """Nur sync.py darf HTTP-Anfragen stellen (an den eigenen ESP), main.py nur an 127.0.0.1."""
    for f in PKG.rglob("*.py"):
        text = f.read_text(encoding="utf-8")
        if f.name in ("sync.py", "main.py"):
            continue
        assert "urlopen" not in text and "urllib.request" not in text and "http.client" not in text, f


def test_motto_everywhere():
    assert MOTTO in (PKG / "web" / "index.html").read_text(encoding="utf-8")
    root = PKG.parents[1]
    for doc in ["README.md", "README.de.md"]:
        p = root / doc
        if p.exists():
            assert "Herbrechtingen" in p.read_text(encoding="utf-8"), doc


def test_mk4_constants_match_spec():
    spec = DRIVERS["mk4"].spec
    assert spec["transport"]["companyId"] == mk4.COMPANY_ID
    assert spec["slots"] == mk4.SLOTS and spec["levels"] == mk4.LEVELS


# ---------- Eingebaute Hilfe ----------

def test_help_pages_render_offline(server):
    url, _ = server
    from studrailmaster import helpdocs

    for lang in ("de", "en"):
        for key, _, _ in helpdocs.TOPICS:
            with urllib.request.urlopen(f"{url}/help/{lang}/{key}") as r:
                page = r.read().decode()
                assert "frame-ancestors 'self'" in r.headers["Content-Security-Policy"]
            assert "<h1" in page and "Herbrechtingen" in page
            assert "/help/" + lang + "/drivers" not in page  # Entwickler-Kapitel nicht in der Hilfe
            # keine klickbaren Links nach draußen, keine Links ins Leere
            assert not re.search(r'href="https?:', page)
            for href in re.findall(r'href="(/help/[^"#]+)', page):
                with urllib.request.urlopen(url + href) as r2:
                    assert r2.status == 200, href
            for src in re.findall(r'src="([^"]+)"', page):
                with urllib.request.urlopen(url + src) as r2:
                    assert r2.status == 200, src
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(url + "/help/de/../../config")


def test_help_anchors_used_by_gui_exist():
    from studrailmaster import helpdocs

    need = {("de", "guide"): ["fahren", "einstellungen", "hubs", "fehlersuche", "deine-daten"],
            ("en", "guide"): ["driving", "settings", "hubs", "troubleshooting", "your-data"],
            ("de", "install"): ["linux-mould-king"], ("en", "install"): ["linux-mould-king"]}
    for (lang, topic), anchors in need.items():
        page = helpdocs.page(lang, topic)
        for a in anchors:
            assert f'id="{a}"' in page, (lang, topic, a)


def test_markdown_renderer():
    from studrailmaster.helpdocs import render

    h = render("# Titel\n\nText mit **fett**, *kursiv*, `code <x>` und [Link](https://example.org).\n\n"
               "| A | B |\n|---|---|\n| 1 | 2 |\n\n- eins\n- zwei\n\n```\n<script>\n```\n> Hinweis", "de")
    assert '<h1 id="titel">' in h and "<b>fett</b>" in h and "<i>kursiv</i>" in h
    assert "<code>code &lt;x&gt;</code>" in h and 'href="https://' not in h and "(https://example.org)" in h
    assert "<th>A</th>" in h and "<td>2</td>" in h and "<li>zwei</li>" in h
    assert "&lt;script&gt;" in h and "<blockquote>" in h


def test_help_has_no_dangling_anchors(server):
    """Jeder Anker-Link in der Hilfe zeigt auf eine vorhandene Überschrift."""
    url, _ = server
    from studrailmaster import helpdocs

    for lang in ("de", "en"):
        for key, _, _ in helpdocs.TOPICS:
            for target, anchor in re.findall(r'href="(/help/[^"#]+)?#([^"]+)"', helpdocs.page(lang, key)):
                t_lang, t_key = (target.split("/")[2:4] if target else (lang, key))
                assert f'id="{anchor}"' in helpdocs.page(t_lang, t_key), (lang, key, target, anchor)


def test_esp_host_default_and_old_name():
    assert validate({"hubs": []})["esp"]["host"] == "StudRailMasterQuadro.local"
    assert validate({"hubs": [], "esp": {"host": "ZugFern.local"}})["esp"]["host"] == "StudRailMasterQuadro.local"
    assert validate({"hubs": [], "esp": {"host": "Quadro-2.local"}})["esp"]["host"] == "Quadro-2.local"
