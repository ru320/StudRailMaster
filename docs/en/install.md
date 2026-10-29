# Installation

🇩🇪 [Deutsch](../de/installation.md) · [User guide](user-guide.md) · [README](../../README.md)

## What you need

- A computer with **Windows 10/11**, **macOS 12 or newer** or **Linux**.
- **Bluetooth** – almost every laptop has it built in. Otherwise a USB Bluetooth stick will do (Bluetooth 4.0 or newer).
- One or more **motor hubs**: JMC hub (shows up as “JG_JMC-…”), Mould King 4.0 or LEGO Powered Up City Hub (88009).

## Download and start

Download the file for your system from the download page (releases) and unpack it.

### Windows

1. Unpack `StudRailMaster-windows.zip` and double-click `StudRailMaster.exe`.
2. On first start Windows warns: “Windows protected your PC”. That is only because the program has no paid signature. Click **More info**, then **Run anyway**.

### macOS

1. Unpack `StudRailMaster-macos.zip` and drag **Stud Rail Master** into the Applications folder.
2. On first start use **right-click → Open** and confirm **Open** once more.
3. When the Mac asks about **Bluetooth**, click **Allow**.

Unfortunately Mould King hubs do not work on a Mac – Apple does not allow the kind of radio signal they need. JMC and LEGO hubs work. For Mould King: use Linux – or park an ESP32 running the [remote](esp-sync.md) firmware in between. It drives Mould King itself and has its own web page (`StudRailMasterQuadro.local`) where you drive from the browser on your Mac. A bare ESP32 DevKit is enough, no pots or switches needed.

### Linux

You do not need a terminal.

1. Download `StudRailMaster-x86_64.AppImage`, for example into your *Documents* folder.
2. **Right-click** the file → **Properties** → tick **Allow executing file as program** (or “Executable”). Linux asks for this once for every downloaded program, for safety.
3. **Double-click** the file. The program opens in its own window.

From now on **Stud Rail Master** is in your **application menu** with its icon – start it there like any other program. If you move the file later, just double-click it once and the entry follows.

### Linux: Mould King

Mould King hubs need your permission once on Linux:

1. Set up the Mould King hub as described in the [user guide](user-guide.md#mould-king-hubs) and **Save**.
2. The hub card shows the button **Unlock Mould King**. Click it.
3. The system asks for your **password** in its own window. Enter it – done. The hub works right away.

After an update the program may ask once more. Everything else works without this permission.

## Updating

Download the new version and replace the old file (on Linux, tick “Allow executing file as program” again). Your hubs, pictures and settings are kept – they are stored separately from the program (see [Your data](user-guide.md#your-data)).

## Uninstalling

Delete the program. If you also want to get rid of your settings, delete the [data folder](user-guide.md#your-data) as well. On Linux the menu entry stays otherwise: delete `stud-rail-master.desktop` in the folder `~/.local/share/applications`.

## Problems?

See [Troubleshooting](user-guide.md#troubleshooting) in the user guide.

---

*In Herbrechtingen ist es immer am schönsten!*
