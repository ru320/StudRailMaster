# Hub drivers – shared between ESP32 and PC

🇩🇪 [Deutsch](../../de/entwickler/treiber.md) · [README](../../../README.md)

A hub driver must behave identically on the ESP32 remote (C++) and in the PC app (Python), so that a driver can be moved from one side to the other without surprises. This is achieved by splitting every driver into three layers:

```
            ┌─────────────────────────────────────┐
  shared    │ drivers/<id>.json                    │  manifest + test vectors
            └─────────────────────────────────────┘
                 ▲ must reproduce every vector ▲
  pure code ┌──────────────────┐  ┌──────────────────────────────────┐
  (no I/O)  │ ESP: lib/<Name>/ │  │ PC: app/studrailmaster/drivers/  │
            └──────────────────┘  └──────────────────────────────────┘
  radio     ┌──────────────────┐  ┌──────────────────────────────────┐
            │ src/HubLink,     │  │ app/studrailmaster/radio/        │
            │ src/MkLink       │  │ (bleak, HCI, WinRT, simulator)   │
            │ (NimBLE)         │  │                                  │
            └──────────────────┘  └──────────────────────────────────┘
```

- **Manifest** (`drivers/<id>.json`, schema [`drivers/driver.schema.json`](../../../drivers/driver.schema.json)): transport kind and UUIDs, ports, port groups with a shared speed, heartbeat interval, whether the hub has a watchdog, how many stop packets arm it, where an implementation exists (`runsOn`), and **test vectors**.
- **Pure code**: turns throttle values into bytes. No Bluetooth, no timing, no globals – that is what makes it portable and testable on the PC.
- **Radio**: platform specific. It only knows two shapes, described by `transport.kind`:
  - `gatt` – one BLE connection per hub; the driver yields one packet per hub (`encode(percent[]) → bytes`), the radio layer writes it on change and every `heartbeatMs`.
  - `advert` – no connection; one sender drives several hubs (slots); the driver yields complete advertising data (`encode({slot: percent[]}) → bytes`, `pair() → bytes`).

## Same API on both sides

| Function | C++ (ESP, `lib/`) | Python (`studrailmaster.drivers`) | Vectors key |
|---|---|---|---|
| JMC packet from raw commands | `hub::buildPacket(cmds, out)` | `jmc.build(cmds)` | `build` |
| % → speed byte | `hub::speedFromPercent(p)` | `jmc.speed_from_percent(p)` | `speedFromPercent` |
| JMC packet from % | `hub::encodePercent(pct, out)` | `jmc.encode(pct)` | `encodePercent` |
| MK encryption | `mk::crypt(raw, len, out)` | `mk4.crypt(raw)` | `crypt` |
| MK connect telegram | `mk::mk4Connect(id, out)` | `mk4.connect(id)` | `connect` |
| MK drive telegram | `mk::mk4Data(id, levels, out)` | `mk4.data(levels, id)` | `data` |
| % → MK level | `mk::mk4Level(p)` | `mk4.level(p)` | `level` |
| MK advertising data | `mk::advData(raw, len, out)` | `mk4.adv_data(raw)` | `advData` |
| LEGO: % → power | `lego::power(p)` | `lego.power(p)` | `power` |
| LEGO frame from % | `lego::encodePercent(pct, out)` | `lego.encode(pct)` | `encodePercent` |
| frame → single writes | `HubLink::write()` (`Protocol::splitByLength`) | `driver.messages(frame)` | `messages` |

A GATT frame may consist of several messages (LEGO LWP3: one per port, byte 0 = length); the radio writes them one by one (`messages()`, default: one write). A scan recognises a hub by name (`namePrefix`) or advertised service (`advertisedService`); `notify` subscribes to hub messages (LEGO: attached devices, errors to the log). On the ESP, `HubLink::Protocol` describes UUIDs, heartbeat, unlock stops, notify and whether a frame consists of several messages per GATT type (`HubLink::JMC`, `HubLink::LEGO`). Guided test for the City Hub: `cd app && .venv/bin/python ../tools/legotest.py`.

## Test vectors

Vectors are input → expected bytes, written as hex strings. Entries marked `"source": "capture …"` come from recordings of the original apps (the reference for the protocol); the others pin down behaviour defined by this project (e.g. the % → speed mapping).

They are checked in three places:

| Where | How |
|---|---|
| PC, tests | `cd app && python -m pytest` (`tests/test_drivers.py`) |
| PC, every start | `drivers/selftest.py` – the loading screen warns if a vector fails |
| ESP | `pio test -e native` – `tools/gen_vectors.py` turns the JSON into `test/test_drivers/vectors.h` |

## Adding a driver

1. **Record the original app** (e.g. Android “Bluetooth HCI snoop log”) and work out the protocol. Write the findings into the manifest's `notes`.
2. **Manifest** `drivers/<id>.json` with transport, ports, `heartbeatMs`, `watchdog`, `runsOn`, and vectors – at least a few from the capture.
3. **Python**: `app/studrailmaster/drivers/<id>.py` with a subclass of `GattDriver` or `AdvertDriver`, register it in `drivers/__init__.py`, add a check table to `drivers/selftest.py` and tests.
4. **C++** (if it should run on the ESP): pure functions in `lib/<Name>/`, the same names as in the table above; extend `tools/gen_vectors.py` and `test/test_drivers/`.
5. Only then the radio layer: on the PC nothing to do for `gatt`/`advert`; a new transport kind needs a new class in `radio/`.
6. `runsOn` lists where the driver is implemented. The ESP sync refuses to hand a hub to the ESP whose type is not `esp32`.

## Moving a driver between ESP and PC

Because the pure layer has no I/O and is pinned by the same vectors, porting means re-typing a few dozen lines in the other language until `pytest` and `pio test -e native` are both green. Values that differ by platform belong in the manifest (and are read from it in Python; on the ESP they are constants next to the code with a comment pointing to the manifest).

## Limits per platform

| | JMC | Mould King 4.0 | LEGO City Hub |
|---|---|---|---|
| ESP32 | 4 connections (NimBLE config) | 3 slots | like JMC (counts towards the 4 connections) |
| PC Linux | as many as the adapter allows (typically 5–10) | 3 slots, needs `CAP_NET_RAW` | like JMC, tested |
| PC Windows | as many as the adapter allows | 3 slots, untested | like JMC, untested |
| PC macOS | as many as the adapter allows | not possible | like JMC, untested |

---

*In Herbrechtingen ist es immer am schönsten!*
