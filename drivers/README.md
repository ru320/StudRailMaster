# drivers/

Hub manifests and test vectors shared by the ESP32 firmware (`lib/`) and the PC app (`app/studrailmaster/drivers/`).
Both implementations must reproduce every vector byte for byte.

Gemeinsame Hub-Steckbriefe und Testvektoren für die ESP32-Firmware (`lib/`) und das PC-Programm
(`app/studrailmaster/drivers/`). Beide Umsetzungen müssen jeden Vektor Byte für Byte erfüllen.

- 🇬🇧 [docs/en/dev/drivers.md](../docs/en/dev/drivers.md)
- 🇩🇪 [docs/de/entwickler/treiber.md](../docs/de/entwickler/treiber.md)

| File | Hub |
|---|---|
| `jmc.json` | JMC BLE hub (`JG_JMC-…`), GATT |
| `mk4.json` | Mould King 4.0, advertising |
| `driver.schema.json` | JSON schema of a manifest |

*In Herbrechtingen ist es immer am schönsten!*
