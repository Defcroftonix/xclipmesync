# xclipmesync
Syncs clipboard across multiple X11 displays for a single user. Runs in the background as daemon. By the way the name refer to x as in X11 display. Clip as in cliboard. Me as in this tool only works for single user. And sync describing its function as clipboard sync.

## How it works

xclipmesync polls each display at a fixed interval (currently set hardcoded to 0.5 seconds. If you want you can change it on the python code itself at the top) using `xclip`. When it detects 
a change on one display, it hashes the content and propagates it to all other displays. 
Then we just run a hash check prevents sync loops. So if the content came from xclipmesync itself, 
it won't be re-propagated.

Unlike similar tools, xclipmesync uses a mesh topology. So every display is treated 
equally with no hardcoded primary display. This means any display can be the source 
and any display can be the destination. It is very simple architecture really.

Originally I want to make a sink to properly check and compare between displays but I thought it is too complicated and decided to use simpler approach. By simply just read the xclip and polling it without needing the sink approach. Because truthfully, I am lazy. This is the simplest approach I can think of that able to scale to multiple displays.


## Dependencies

- Python 3
- `xclip`

Install `xclip` if you don't have it:

```bash
sudo apt install xclip      # Debian/Ubuntu
sudo pacman -S xclip        # Arch
sudo dnf install xclip      # Fedora
```

## Installation

Clone the repo and run the setup script:

```bash
git clone https://github.com/Defcroftonix/xclipmesync.git
cd xclipmesync
chmod +x setup.sh
./setup.sh
```

By default it syncs `:0` and `:1`. To specify your own displays:

```bash
./setup.sh :0 :1 :2
```
Requires at least two displays specified
In case the display doesn't exist it will continue running and if you start that display later, it will automatically sync that one. Run `./setup.sh` again with specific display you want in case you want to change the display or just edit `~/.config/systemd/user/clipboard-sync.service` manually in case you need to with:


```bash
nano ~/.config/systemd/user/clipboard-sync.service
```

The setup script requires no `sudo` and only modifies your user systemd directory (`~/.config/systemd/user/`).

## Manual setup

If you prefer not to use the setup script, you can do it yourself:

1. Edit `DISPLAYS` at the top of `clipboard_sync.py` to match your displays.
2. Create `~/.config/systemd/user/clipboard-sync.service` which you can just put this inside:

```ini
[Unit]
Description=X11 clipboard sync

[Service]
ExecStart=/usr/bin/python3 /path/to/clipboard_sync.py :0 :1
Restart=on-failure

[Install]
WantedBy=default.target
```

Make sure the path is correct.
And make sure `:0 :1` is changed into what display server you want to sync. Requires at least two displays specified. You can add as many you want but I haven't tested the limit. Edit this file `~/.config/systemd/user/clipboard-sync.service` if you want to change your display later on.

In case you just clone this repo to your home folder, just use this instead:

```ini
[Unit]
Description=X11 clipboard sync

[Service]
ExecStart=/usr/bin/python3 /home/yourusername/xclipmesync/clipboard_sync.py
Restart=on-failure

[Install]
WantedBy=default.target
```

You still need to edit your username into the file path.


3. Enable and start it:

```bash
systemctl --user enable --now clipboard-sync
```

## Usage

Once running it works silently in the background. Anything you copy on one display is automatically available on the others.

systemctl commands:

```bash
systemctl --user status clipboard-sync     # check status
systemctl --user restart clipboard-sync    # restart after config changes
systemctl --user stop clipboard-sync       # stop
journalctl --user -u clipboard-sync -f     # live logs
```
## Differences from xclipsync

- No tcl/tk required, only Python 3 and xclip
- All displays are equal, no hardcoded primary display
- Supports more than two displays
- Hash-based loop prevention per display
- I uses polling which might cause more waste of resource

## Multi-user support

This tool syncs clipboards across displays belonging to the **same user**.

Cross-user clipboard sync (e.g. two different users on separate displays on the same machine) is not supported and out of scope for this project. If you need that, you'll need a per-user agent with a shared IPC channel between them.

## License

MIT
