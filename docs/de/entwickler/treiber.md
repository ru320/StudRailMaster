# Hub-Treiber – gemeinsam für ESP32 und PC

🇬🇧 [English](../../en/dev/drivers.md) · [README](../../../README.de.md)

Ein Hub-Treiber muss sich auf der ESP32-Fernbedienung (C++) und im PC-Programm (Python) gleich verhalten, damit man ihn ohne Überraschungen von einer Seite auf die andere schieben kann. Dazu besteht jeder Treiber aus drei Schichten:

```
              ┌─────────────────────────────────────┐
  gemeinsam   │ drivers/<id>.json                    │  Steckbrief + Testvektoren
              └─────────────────────────────────────┘
                   ▲ muss jeden Vektor erfüllen ▲
  reiner Code ┌──────────────────┐  ┌──────────────────────────────────┐
  (ohne E/A)  │ ESP: lib/<Name>/ │  │ PC: app/studrailmaster/drivers/  │
              └──────────────────┘  └──────────────────────────────────┘
  Funk        ┌──────────────────┐  ┌──────────────────────────────────┐
              │ src/HubLink,     │  │ app/studrailmaster/radio/        │
              │ src/MkLink       │  │ (bleak, HCI, WinRT, Simulator)   │
              │ (NimBLE)         │  │                                  │
              └──────────────────┘  └──────────────────────────────────┘
```

- **Steckbrief** (`drivers/<id>.json`, Schema [`drivers/driver.schema.json`](../../../drivers/driver.schema.json)): Transportart und UUIDs, Ports, Port-Gruppen mit gemeinsamem Speed, Heartbeat, ob der Hub einen Watchdog hat, wie viele Stopp-Pakete ihn freischalten, wo es eine Umsetzung gibt (`runsOn`) und **Testvektoren**.
- **Reiner Code**: macht aus Reglerwerten Bytes. Kein Bluetooth, keine Zeiten, keine globalen Zustände – darum portierbar und auf dem PC testbar.
- **Funk**: je Plattform verschieden. Er kennt nur zwei Formen, festgelegt in `transport.kind`:
  - `gatt` – eine BLE-Verbindung pro Hub; der Treiber liefert ein Paket pro Hub (`encode(prozent[]) → bytes`), der Funk schreibt es bei Änderung und alle `heartbeatMs`.
  - `advert` – keine Verbindung; ein Sender steuert mehrere Hubs (Slots); der Treiber liefert komplette Werbedaten (`encode({slot: prozent[]}) → bytes`, `pair() → bytes`).

## Gleiche Funktionen auf beiden Seiten

| Funktion | C++ (ESP, `lib/`) | Python (`studrailmaster.drivers`) | Vektor-Schlüssel |
|---|---|---|---|
| JMC-Paket aus Rohbefehlen | `hub::buildPacket(cmds, out)` | `jmc.build(cmds)` | `build` |
| % → Speed-Byte | `hub::speedFromPercent(p)` | `jmc.speed_from_percent(p)` | `speedFromPercent` |
| JMC-Paket aus % | `hub::encodePercent(pct, out)` | `jmc.encode(pct)` | `encodePercent` |
| MK-Verschlüsselung | `mk::crypt(raw, len, out)` | `mk4.crypt(raw)` | `crypt` |
| MK-Connect | `mk::mk4Connect(id, out)` | `mk4.connect(id)` | `connect` |
| MK-Fahrtelegramm | `mk::mk4Data(id, levels, out)` | `mk4.data(levels, id)` | `data` |
| % → MK-Stufe | `mk::mk4Level(p)` | `mk4.level(p)` | `level` |
| MK-Werbedaten | `mk::advData(raw, len, out)` | `mk4.adv_data(raw)` | `advData` |
| LEGO: % → Leistung | `lego::power(p)` | `lego.power(p)` | `power` |
| LEGO-Frame aus % | `lego::encodePercent(pct, out)` | `lego.encode(pct)` | `encodePercent` |
| Frame → einzelne Writes | `HubLink::write()` (`Protocol::splitByLength`) | `driver.messages(frame)` | `messages` |

Ein GATT-Frame darf aus mehreren Nachrichten bestehen (LEGO LWP3: eine je Port, Byte 0 = Länge); der Funk schreibt sie einzeln (`messages()`, Standard: ein Write). Erkannt wird ein Hub im Scan am Namen (`namePrefix`) oder am beworbenen Service (`advertisedService`); `notify` abonniert Meldungen des Hubs (LEGO: angesteckte Geräte, Fehler ins Log). Auf dem ESP beschreibt `HubLink::Protocol` je GATT-Typ UUIDs, Heartbeat, Freischalt-Stopps, Notify und ob ein Frame aus mehreren Nachrichten besteht (`HubLink::JMC`, `HubLink::LEGO`). Geführter Test für den City Hub: `cd app && .venv/bin/python ../tools/legotest.py`.

## Testvektoren

Ein Vektor ist Eingabe → erwartete Bytes, als Hex-Text. Einträge mit `"source": "capture …"` stammen aus Mitschnitten der Original-Apps (die Referenz fürs Protokoll); die übrigen legen Verhalten fest, das dieses Projekt bestimmt (z. B. die Umrechnung % → Speed).

Geprüft wird an drei Stellen:

| Wo | Wie |
|---|---|
| PC, Tests | `cd app && python -m pytest` (`tests/test_drivers.py`) |
| PC, bei jedem Start | `drivers/selftest.py` – der Ladebildschirm warnt, wenn ein Vektor nicht passt |
| ESP | `pio test -e native` – `tools/gen_vectors.py` macht aus dem JSON `test/test_drivers/vectors.h` |

## Neuen Treiber anlegen

1. **Original-App mitschneiden** (z. B. Android „Bluetooth-HCI-Snoop-Log“) und das Protokoll herausarbeiten. Erkenntnisse in `notes` des Steckbriefs.
2. **Steckbrief** `drivers/<id>.json` mit Transport, Ports, `heartbeatMs`, `watchdog`, `runsOn` und Vektoren – mindestens einige aus dem Mitschnitt.
3. **Python**: `app/studrailmaster/drivers/<id>.py` mit einer Unterklasse von `GattDriver` oder `AdvertDriver`, in `drivers/__init__.py` eintragen, Prüftabelle in `drivers/selftest.py`, Tests.
4. **C++** (wenn er auf dem ESP laufen soll): reine Funktionen in `lib/<Name>/`, Namen wie in der Tabelle oben; `tools/gen_vectors.py` und `test/test_drivers/` erweitern.
5. Erst dann der Funk: Auf dem PC ist für `gatt`/`advert` nichts zu tun; eine neue Transportart braucht eine neue Klasse in `radio/`.
6. `runsOn` nennt, wo der Treiber umgesetzt ist. Der ESP-Abgleich lehnt es ab, einen Hub an den ESP zu geben, dessen Typ dort fehlt (`esp32`).

## Treiber zwischen ESP und PC verschieben

Weil die reine Schicht keine Ein-/Ausgabe hat und durch dieselben Vektoren festgenagelt ist, heißt Portieren: ein paar Dutzend Zeilen in der anderen Sprache nachschreiben, bis `pytest` und `pio test -e native` beide grün sind. Werte, die je Plattform gleich sein müssen, gehören in den Steckbrief (Python liest sie daraus; auf dem ESP stehen sie als Konstanten neben dem Code mit Verweis auf den Steckbrief).

## Grenzen je Plattform

| | JMC | Mould King 4.0 | LEGO City Hub |
|---|---|---|---|
| ESP32 | 4 Verbindungen (NimBLE-Einstellung) | 3 Slots | wie JMC (zählt zu den 4 Verbindungen) |
| PC Linux | so viele, wie der Adapter schafft (meist 5–10) | 3 Slots, braucht `CAP_NET_RAW` | wie JMC, getestet |
| PC Windows | so viele, wie der Adapter schafft | 3 Slots, ungetestet | wie JMC, ungetestet |
| PC macOS | so viele, wie der Adapter schafft | nicht möglich | wie JMC, ungetestet |

---

*In Herbrechtingen ist es immer am schönsten!*
