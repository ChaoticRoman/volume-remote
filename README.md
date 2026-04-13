# Ubuntu Web Volume Remote

A tiny, self-hosted web app that lets you control your Ubuntu desktop's audio volume and media player from your phone's browser — no app install needed. Your phone just needs to be on the same Wi-Fi/LAN.

## Features

- Volume up / down with adjustable step (2 %, 5 %, 10 %, 15 %, 20 %)
- Mute toggle
- Media player controls: play/pause, previous, next, seek ±10 s
- System suspend button
- Optional token-based authentication
- Runs entirely in the browser — no app needed on the phone

## Prerequisites

- Ubuntu with PulseAudio or PipeWire (PulseAudio compatibility layer)
- Python 3.8+
- `pactl` — provided by the `pulseaudio-utils` package
- `playerctl` — for media player controls

Install the system packages:

```bash
sudo apt update
sudo apt install python3-venv pulseaudio-utils playerctl
```

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/volume-remote.git
cd volume-remote

# 2. Create a virtual environment and install Python dependencies
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Usage

### Run manually

```bash
# Optional: protect the server with a secret token
export VOLUME_TOKEN="choose-a-long-secret"

./run.sh
```

The server starts on port **8080**.

If you use UFW, allow the port:

```bash
sudo ufw allow 8080/tcp
```

Find your desktop's LAN IP:

```bash
hostname -I
# example: 192.168.1.50
```

Open on your phone (same Wi-Fi):

```
http://192.168.1.50:8080
```

If you set `VOLUME_TOKEN`, pass it once as a query parameter — it will be saved to `localStorage` and sent automatically on every subsequent request:

```
http://192.168.1.50:8080/?token=choose-a-long-secret
```

### Run at boot with systemd

> **Note:** The service must run as a user unit (not root) so it can access the user's PulseAudio/PipeWire session.
> See [StackOverflow](https://stackoverflow.com/a/27091782/12118546) and [Unix SE](https://unix.stackexchange.com/a/598055/495824) for background.

1. Copy the included service file and edit the paths to match your setup:

```bash
mkdir -p ~/.config/systemd/user
cp volume-remote.service ~/.config/systemd/user/volume-remote.service
nano ~/.config/systemd/user/volume-remote.service
```

Update `WorkingDirectory` and `ExecStart` to the absolute path where you cloned the repo, and optionally add an `Environment` line for the token:

```ini
[Unit]
Description=Volume Remote Web Controller
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/YOUR_USERNAME/volume-remote
Environment=VOLUME_TOKEN=choose-a-long-secret
ExecStart=/home/YOUR_USERNAME/volume-remote/venv/bin/gunicorn -w 1 -b 0.0.0.0:8080 server:app
Restart=on-failure

[Install]
WantedBy=default.target
```

2. Enable and start the service:

```bash
systemctl --user daemon-reload
systemctl --user enable --now volume-remote
```

## Development

Changes to `static/index.html` are served immediately without a restart.

For backend changes, restart the service and inspect logs:

```bash
systemctl --user restart volume-remote
systemctl --user status volume-remote
journalctl --user -u volume-remote.service
```

## Security

- Keep this LAN-only. Do not expose port 8080 to the internet.
- Set `VOLUME_TOKEN` to a long random string to prevent anyone on the same network from controlling your machine.
- If you need remote access, put it behind a reverse proxy with HTTPS and strong authentication.

## License

MIT — see [LICENSE](LICENSE).
