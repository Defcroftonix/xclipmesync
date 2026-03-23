# xclipmesync
Syncs clipboard accross multiple X11 displays for a single user. Runs in the background as daemond

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

The setup script requires no `sudo` and only modifies your user systemd directory (`~/.config/systemd/user/`).

## Manual setup

If you prefer not to use the setup script, you can do it yourself:

1. Edit `DISPLAYS` at the top of `clipboard_sync.py` to match your displays.
2. Create `~/.config/systemd/user/clipboard-sync.service` which you can just put this inside:

```ini
[Unit]
Description=X11 clipboard sync

[Service]
ExecStart=/usr/bin/python3 /path/to/clipboard_sync.py
Restart=on-failure

[Install]
WantedBy=default.target
```

Make sure the path is correct.

In case you just clone this repo to your home folder, just use this instead:

```ini
[Unit]
Description=X11 clipboard sync

[Service]
ExecStart=/usr/bin/python3 /home/xclipmesync/clipboard_sync.py
Restart=on-failure

[Install]
WantedBy=default.target
```


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

## Multi-user support

This tool syncs clipboards across displays belonging to the **same user**.

Cross-user clipboard sync (e.g. two different users on separate displays on the same machine) is not supported and out of scope for this project. If you need that, you'll need a per-user agent with a shared IPC channel between them.

## License

MIT
