# Ubuntu Web Volume Remote

> Design a simple web application with big + and - buttons arranged vertically and centered, intended for mobile phone, running on Ubuntu, that will allow me to control Desktop sound volume from my phone

Below is a tiny, self‑hosted web app you run on your Ubuntu desktop. It serves a mobile‑friendly page with big + and − buttons that change your desktop volume. Your phone just needs to be on the same Wi‑Fi/LAN.

What it uses
- Python + Flask (server)
- pactl (PulseAudio/PipeWire) to change volume
- A single HTML page with large vertically stacked buttons

1) Install prerequisites on Ubuntu
- Open a terminal and run:
  - `sudo apt update`
  - `sudo apt install python3-venv pulseaudio-utils playerctl`
  - `mkdir -p ~/volremote && cd ~/volremote`
  - `python3 -m venv venv`
  - `./venv/bin/pip install flask gunicorn`

2) Create the server (`server.py`)
Put this into `~/volremote/server.py`:

3) Create the mobile page (`static/index.html`)

Create the folder and file:

- `mkdir -p ~/volremote/static`
- `nano ~/volremote/static/index.html`

4) Run the server
- Optionally set a token so only you can use it:
  - `export VOLUME_TOKEN="choose-a-long-secret`
- Start it:
  - `cd ~/volremote`
  - `./venv/bin/gunicorn -w 1 -b 0.0.0.0:5000 server:app`

If you use UFW, allow the port:
- `sudo ufw allow 5000/tcp`

Find your desktop’s LAN IP:
- `hostname -I`
Example result: 192.168.1.50

On your phone (same Wi‑Fi), open:
- http://192.168.1.50:5000
- If you set `VOLUME_TOKEN`, add it once: `http://192.168.1.50:5000/?token=choose-a-long-secret`
  (It will be stored locally and sent on future requests.)

5) Optional: run at boot with systemd

**Note:** This one AI got wrong, root systemd cannot access pulse audio, but this helped:

* https://stackoverflow.com/a/27091782/12118546
* https://unix.stackexchange.com/a/598055/495824

So I have fixed the section below.

Create `~/.config/systemd/user/volume-remote.service` with:
```
[Unit]
Description=Volume Remote Web Controller
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/YOUR_USERNAME/volremote
Environment=VOLUME_TOKEN=choose-a-long-secret
ExecStart=/home/YOUR_USERNAME/volremote/venv/bin/gunicorn -w 1 -b 0.0.0.0:5000 server:app
Restart=on-failure

[Install]
WantedBy=default.target
```
Then:
- `systemctl --user daemon-reload`
- `sudo systemctl enable --user --now volume-remote`

Notes
- `pactl` works for both PulseAudio and PipeWire (via PulseAudio compatibility). If pactl isn’t present, ensure pulseaudio-utils is installed.
- Security: keep this LAN‑only, use a token, and don’t expose the port to the internet unless you put it behind HTTPS and proper auth.

## Development

New version of `index.html` is served immediately upon saving.

For backend server, just restart it and check status and logs:

```
systemctl restart --user volume-remote
systemctl status --user volume-remote
journalctl --user -u volume-remote.service
``` 
