# Set up the remote

🇩🇪 [Deutsch](../de/fernbedienung-einrichten.md) · [User guide](user-guide.md) · [Together with the PC](esp-sync.md) · [README](../../README.md)

The **Stud Rail Master Quadro** remote is an ESP32 with its own firmware. It drives up to four hubs without any computer. You set it up through a web page that you open in the browser on your phone or PC.

To start, a **bare ESP32 DevKit** is enough. The throttles are then sliders on the web page. You can add slide pots, switches and the case later, see [Connecting hardware](#connecting-hardware).

## What you need

- An **ESP32 DevKit** with an ESP32-WROOM-32 and 4 MB flash (for example “ESP32 DevKit V1”, 30 or 38 pins).
- A **USB cable with data lines**. Charge-only cables don't work.
- A computer with Windows, macOS or Linux. It builds the firmware once and uploads it.
- A **2.4 GHz Wi-Fi**. The ESP32 can't do 5 GHz. It also works without Wi-Fi: the remote then opens its own network.

## 1. Upload the firmware

### Get the source

On the project's GitHub page click **Code → Download ZIP** and unpack it. Or with git:

```bash
git clone https://github.com/ru320/StudRailMaster.git
```

### With VS Code (recommended)

1. Install [Visual Studio Code](https://code.visualstudio.com/). Then search for **PlatformIO IDE** under *Extensions* and install it.
2. In VS Code choose **File → Open Folder** and pick the unpacked project folder, the one that contains `platformio.ini`.
3. Plug in the ESP32 via USB.
4. In the blue bar at the bottom choose the environment **env:esp32dev** and click the arrow **→ (Upload)**.

The first time, PlatformIO downloads the compiler and libraries, a few hundred MB. That takes a few minutes. At the end it says `SUCCESS`.

### From the command line

With [PlatformIO Core](https://docs.platformio.org/en/latest/core/installation/index.html) installed:

```bash
cd StudRailMaster
pio run -e esp32dev -t upload
pio device monitor          # optional: watch the output (115200 baud), quit with Ctrl+C
```

### Enter the Wi-Fi in advance (optional)

Normally you enter the Wi-Fi on the web page later. You can also put it into the firmware: copy `src/secrets.h.example` to `src/secrets.h` and fill it in.

```c
#define SECRET_WIFI_SSID "MyWiFi"
#define SECRET_WIFI_PASS "MyPassword"
#define SECRET_OTA_PASS  "aPasswordForUpdates"
```

It works just as well without this file. Whatever you enter on the web page always takes priority.

## 2. First connection

1. After the upload the ESP32 restarts and opens its own Wi-Fi called **StudRailMasterQuadro**.
2. Join this network with your phone or PC. The password is **`zugfern123`**.
3. Open **http://192.168.4.1** in the browser. You see the remote's drive page.
4. Tap the **settings icon** at the top right. Under **Wi-Fi** enter:
   - **Home Wi-Fi** and **Password**.
   - A **Device name** if you like. The default is `StudRailMasterQuadro`. If you have several remotes, give each its own name.
   - **AP password**: please set your own, at least 8 characters. It protects the remote's own network and, as long as you don't set your own update password, also the updates over Wi-Fi.
5. Click **Save Wi-Fi**, then **Restart**.
6. Go back to your home Wi-Fi and open **http://StudRailMasterQuadro.local**, or `devicename.local`. Upper or lower case doesn't matter.

If the remote can't reach the home Wi-Fi within 10 seconds, it opens its own network at 192.168.4.1 again. A wrong password can't lock you out.

## 3. Set up hubs

This works just like in the PC program, only on the remote's web page (*Settings*):

1. Switch the hub on. Under **Find hubs** click **Start scan (5 s)**, then **use** next to your hub.
2. On the hub card assign a **Controller** (1–4) to each **port**. Tick **invert** if needed, and **active**.
3. Click **Save**. The remote now connects to the hub.

**Mould King 4.0:** This hub doesn't show up in the scan. On a free hub card choose “Mould King 4.0”, switch the hub on and click **Pair**. You choose the **slot** with the button on the hub (slot 0 after power-on).

If you have already set up your hubs in the PC program, you can simply hand them over to the remote from there, see [Together with the PC](esp-sync.md).

At most **4 hubs** are active at once. You can park up to 16 more in the **Archive** and move one onto a position when you need it.

## 4. Driving

The start page shows a big lever for every assigned controller. Drag up to go faster, one tap on the direction switches it. The red button is the **emergency stop**.

After switching on and after every emergency stop nothing moves until **every used controller has been at 0 once**. When you drive through the web page, the remote triggers an emergency stop as soon as the page has been silent for 2 seconds, for example because the phone screen turned off.

### Status LED on the board

| LED | Meaning |
|---|---|
| off | no hub activated |
| fast blinking | connecting, no hub yet |
| slow blinking | only some of the hubs connected |
| on | all activated hubs connected |
| double flash | emergency stop or start lock: move all controllers to 0 once |

## Connecting hardware

With pots and switches, switch *Settings → Controllers → Input* to **Pots + switches on the ESP**. The pin assignment:

| Function | GPIO | Connection |
|---|---|---|
| Slide pot 1–4 (10 kΩ linear) | 34, 35, 32, 33 | wiper; ends to 3.3 V and GND |
| Direction switch 1–4 | 16, 17, 18, 19 | to GND |
| Direction LED 1–4 | 21, 22, 23, 25 | via 330 Ω to GND |
| Emergency-stop button | 27 | to GND |

Parts, power supply and the printable case: [parts list](../../hardware/BOM.md) and [case](../../hardware/gehaeuse/README.md) (both in German). Both are a **preview and not yet built**.

## Updates over Wi-Fi

Once the remote is set up, you no longer need the USB cable:

- **VS Code:** choose the environment **env:ota**, then **Upload**.
- **Command line:** `pio run -e ota -t upload`. With a different device name, add `--upload-port devicename.local`.

The update password is `SECRET_OTA_PASS` from `src/secrets.h`. Without that line it is the remote's **AP password** (default `zugfern123`). In that case enter it in `src/secrets.h` as `SECRET_OTA_PASS`.

Before the update the remote stops all trains. Your settings are kept.

## Problems?

- **Upload: “Failed to connect to ESP32”:** hold the **BOOT** button on the board until the upload starts.
- **No port found:** try another USB cable (data cable!). On Windows and macOS the board's USB chip may need a driver, usually CP210x or CH340. On Linux your user must be in the `dialout` group (`sudo usermod -aG dialout $USER`, then log in again).
- **`StudRailMasterQuadro.local` doesn't work:** some Android phones and older Windows PCs don't know `.local` names. Use the IP address instead. You find it in your router or in the serial monitor (`WLAN verbunden, http://…`).
- **Hub doesn't connect:** a hub can only be connected to one device at a time. Close the phone app and the PC program first, or hand the radio over to the remote, see [Together with the PC](esp-sync.md).

---

*In Herbrechtingen ist es immer am schönsten!*
