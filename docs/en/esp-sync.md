# Together with the remote

🇩🇪 [Deutsch](../de/esp-abgleich.md) · [User guide](user-guide.md) · [Set up the remote](remote-setup.md) · [README](../../README.md)

If you have the home-made remote **Stud Rail Master Quadro** (setup: [Set up the remote](remote-setup.md)), the program works together with it. Both have to be on the same Wi-Fi – or the computer is connected to the remote's own Wi-Fi (named like its device name, by default “StudRailMasterQuadro”).

Everything is under **Settings → Remote (ESP)**. The **Address** field normally says `StudRailMasterQuadro.local` – upper or lower case does not matter. If you gave the remote a different device name (on its web page under *Settings → Wi-Fi*, e.g. when you have several remotes), enter `device-name.local`. If that does not work, use the remote's IP address (on its own Wi-Fi, which has the same name as the device, it is `192.168.4.1`).

## Getting hubs from the remote

Already set up your hubs on the remote? Then you do not have to do it again:

1. Click **Get hubs from the ESP**. The list shows all hubs of the remote.
2. Click **use** for each hub you want.
3. **Save**. Add a picture – done.

Hubs you take over first go to the **depot**. Tick **active** when you want to drive them from the computer – and then switch the remote off, because a hub can only be connected to one device at a time.

## Sending hubs to the remote

It works the other way round, too:

1. Tick the hubs the remote should get.
2. Click **Send to ESP**.
3. On the remote (on your phone), put the hub into a place with **Restore** under **Archive**.

Good to know:

- The remote has only **4 throttles**. A port on throttle 5 or higher stays empty there – you get a notice.
- The remote can remember at most **16 hubs**.
- **Pictures** stay on the computer; the remote has no room for them.
- Hubs that are currently driving on the remote are not overwritten.
- **LEGO City Hubs** work both ways, with their ports A and B. The remote also finds them in its own scan.
- Hubs you found on a **Mac** cannot be sent – the Mac does not reveal the hub's real address. In that case, scan for them directly on the remote.

## Live link: the computer as the remote's display

With **Start live link** the remote takes command:

- The **remote drives** the trains. The computer hands over its hubs for this.
- The drive page shows the **remote's throttles** – with the pictures of your hubs.
- If the remote is set to **Sliders (GUI)**, you can drive along on the computer. With **Pots + switches** you just watch.
- **Emergency stop** on the computer also stops the remote.
- If the computer goes away (window closed, Wi-Fi gone) while a train is moving, the remote stops all trains by itself after 2 seconds.

- The remote (on your phone) shows at the top which computer is watching.

**Stop live link** gives the hubs back to the computer: the remote stops all trains and disconnects from the hubs. Then move all levers to 0 once. The phone then shows **Radio on the PC**. **Take radio back** lets the remote drive again – the computer loses its hubs. After a restart the remote drives by itself anyway.

---

*In Herbrechtingen ist es immer am schönsten!*
