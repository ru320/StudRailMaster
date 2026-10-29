# User guide

🇩🇪 [Deutsch](../de/anleitung.md) · [Installation](install.md) · [README](../../README.md)

Stud Rail Master lets you drive your brick-built trains from your computer. All you need is a computer with Bluetooth and one or more motor hubs.

## First steps

1. **Install the program** – see [Installation](install.md).
2. **Start the program.** A loading screen appears briefly, then the drive page. It is empty at first because no hub is set up yet.
3. **Switch your hub on** (battery box on).
4. Click the **settings icon** at the top right (the three sliders).
5. Under **Find hubs**, click **Start scan**. After 5 seconds your hub appears in the list (for example “JG_JMC-C734”). Click **use**.
6. On the new hub card, choose **Throttle 1** for **port A**. The port is the socket the motor is plugged into.
7. Click **Save** at the bottom.
8. Click the **locomotive icon** at the top right – back to the drive page. There is a lever now. Drag it up and the train moves!

Want to try the program without a hub first? Start the **demo mode** (see [For the curious](#for-the-curious)).

## Driving

![Drive page](../img/drive-en.png)

There is one lever for every throttle that has a hub assigned. It shows which trains it drives – with a picture, if you added one.

- **Faster or slower:** drag the lever up or down. Just tapping it does nothing – so a train never starts by accident.
- **Direction:** the button below the lever (FWD / REV). If you change direction while moving, the train first slows down and then starts off the other way. The button blinks meanwhile.
- **Emergency stop:** the big red button or the **space bar**. All trains stop immediately.

At the top you can see whether all hubs are ready. If not, it tells you why.

### Start lock

After starting and after every emergency stop, no train moves until every lever has been all the way down (at 0) once. An orange notice tells you. This way nothing starts again by itself after an emergency stop.

## Settings

Via the settings icon at the top right. Changes to hubs and throttles only take effect when you click **Save** at the bottom. **Discard** undoes everything.

### Throttles

- **Count:** how many levers there are (1 to 16).
- **Direction change while moving:** how long a train takes to turn around, from full speed forward to full speed backward. Default is 5 seconds. At 0 it switches instantly.
- The sliders on this page drive just like the levers – handy for trying things out.

### Hubs

Every hub has a card:

- **Picture:** click the picture frame or drag a photo onto it. The picture then appears on the lever. ✕ removes it.
- **Name:** for example “ICE” or “Freight train”. It is shown on the lever.
- **Type:** *JMC*, *Mould King 4.0* or *LEGO Powered Up City Hub* – depending on your hub.
- **Address:** the hub's identifier. It is filled in automatically when you scan.
- **active:** only active hubs are driven. Untick it and the hub goes to the **depot**, where it stays with all settings and its picture until you need it again.
- **Ports A to D:** choose a throttle for each socket. One throttle can drive several motors, even on different hubs – for example two locomotives pulling one train.
- **invert:** if a motor runs the wrong way, tick this.
- **Delete:** removes the hub completely.

> **Good to know about the JMC hub:** sockets A and B always run at the same speed, and so do C and D. If A and B are on different throttles, both run at the faster value. The card points this out.

> **LEGO City Hub:** it only has ports A and B. The scan finds it even if you renamed it in the LEGO app. It switches itself off soon when nothing connects – so have the hub in the list first, then press the green button. Port B can also drive the light (88005): the controller then sets the brightness.

### Mould King hubs

Mould King hubs do not show up in a scan. To set one up:

1. Click **+ New hub** and choose type **Mould King 4.0**.
2. Choose the **slot**: a Mould King hub listens on slot 0, 1 or 2. Press the button on the hub to change it; it then blinks 1, 2 or 3 times. After switching on it is always slot 0. This way you can drive up to three Mould King hubs separately.
3. Switch the hub on and click **Pair**. The hub remembers the program.
4. Assign the ports and **Save**.

On Linux, the first time, click **Unlock Mould King** and enter your password, see [Installation](install.md#linux-mould-king). Unfortunately Mould King does not work on a Mac – use Linux instead, or park an ESP32 in between and drive from its web page, see [Installation](install.md#macos).

### Find hubs

**Start scan** looks for Bluetooth devices nearby for 5 seconds. Recognised hubs are marked. You can ignore other devices (TV, headphones …).

### Remote (ESP)

If you have the home-made ZugFern remote, you can exchange hubs between it and the program – see [Remote](esp-sync.md).

## Safety

The computer makes sure no train keeps running out of control:

| If … | then … |
|---|---|
| you close the window | all trains stop before the program ends |
| you press emergency stop | all trains stop immediately |
| the connection to a hub drops | the program reconnects by itself |

**Caution:** if the connection drops, a JMC hub keeps running with its last command until the connection is back. So keep the computer near the track.

## Troubleshooting

| Problem | What helps |
|---|---|
| Loading screen shows “Looking for Bluetooth” in orange | Is Bluetooth switched on on the computer? |
| Hub stays at “connecting” or says “not found” | Is the hub on and are the batteries full? Is it still connected to a phone or the remote? A hub can only be connected to one device at a time – disconnect it there or switch the hub off and on. |
| Hub is connected but the train does not move | Is a port assigned to a throttle and saved? Is the orange “Emergency stop active” notice showing? Then move all levers all the way down once. |
| Train runs the wrong way | Tick **invert** for the port on the hub card. |
| Mould King hub does not react | Hub on, right slot? Click **Pair** again. On Linux: button **Unlock Mould King** on the hub card ([more](install.md#linux-mould-king)). |
| Window stays blank or black | Close the program and start it again. |

## Your data

Everything stays on your computer – the program never goes online. Settings and pictures are stored here:

| System | Folder |
|---|---|
| Windows | `%APPDATA%\StudRailMaster` |
| macOS | `~/Library/Application Support/Stud Rail Master` |
| Linux | `~/.local/share/stud-rail-master` |

To back up or move to a new computer, just copy the whole folder.

## For the curious

The program can be started with extras (on Windows in a shortcut, otherwise in a terminal):

- `stud-rail-master --demo` – **demo mode** with three simulated trains, no hub needed. Your real settings stay untouched.
- `stud-rail-master --lan` – also control it from a **phone** on your home network. The address is shown in the terminal. Caution: anyone on your Wi-Fi can then drive along.

---

*In Herbrechtingen ist es immer am schönsten!*
