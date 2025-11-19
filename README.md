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
  - `sudo apt install python3-venv pulseaudio-utils`
  - `mkdir -p ~/volremote && cd ~/volremote`
  - `python3 -m venv venv`
  - `./venv/bin/pip install flask gunicorn`

2) Create the server (`server.py`)
Put this into `~/volremote/server.py`:

```python
import os, re, subprocess
from flask import Flask, jsonify, request, send_from_directory, abort

TOKEN = os.environ.get('VOLUME_TOKEN')  # set this for simple auth

app = Flask(__name__, static_folder='static')

def pactl(*args):
    return subprocess.run(['pactl', *args], capture_output=True, text=True)

def get_volume():
    r = pactl('get-sink-volume', '@DEFAULT_SINK@')
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    m = re.search(r'(\d+)%', r.stdout)
    return int(m.group(1)) if m else None

def is_muted():
    r = pactl('get-sink-mute', '@DEFAULT_SINK@')
    if r.returncode != 0:
        return False
    return 'yes' in r.stdout.lower()

def ensure_auth(req):
    if TOKEN:
        token = req.headers.get('X-Auth-Token') or req.args.get('token')
        if token != TOKEN:
            abort(401)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/volume', methods=['GET', 'POST'])
def volume():
    ensure_auth(request)
    if request.method == 'GET':
        try:
            return jsonify(volume=get_volume(), muted=is_muted())
        except Exception as e:
            return jsonify(error=str(e)), 500

    data = request.get_json(silent=True) or {}
    action = data.get('action')
    step = int(data.get('step', 5))

    if action == 'up':
        r = pactl('set-sink-volume', '@DEFAULT_SINK@', f'+{step}%')
    elif action == 'down':
        r = pactl('set-sink-volume', '@DEFAULT_SINK@', f'-{step}%')
    elif action == 'mute':
        r = pactl('set-sink-mute', '@DEFAULT_SINK@', 'toggle')
    elif action == 'set':
        val = str(data.get('value'))
        if not val.endswith('%'):
            val = f'{val}%'
        r = pactl('set-sink-volume', '@DEFAULT_SINK@', val)
    else:
        return jsonify(error='invalid action'), 400

    if r.returncode != 0:
        return jsonify(error=r.stderr.strip()), 500

    return jsonify(ok=True, volume=get_volume(), muted=is_muted())

@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,X-Auth-Token'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
```

3) Create the mobile page (`static/index.html`)

Create the folder and file:

- `mkdir -p ~/volremote/static`
- `nano ~/volremote/static/index.html`

Paste:
```
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Volume Remote</title>
<style>
:root { --bg:#111; --fg:#fff; --btn:#222; --btnActive:#333; }
* { box-sizing: border-box; }
html, body { height:100%; margin:0; background:var(--bg); color:var(--fg); font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;}
.container {
  min-height: 100%;
  padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
  display:flex; align-items:center; justify-content:center;
}
.stack { display:flex; flex-direction:column; align-items:center; gap:2rem; width: min(90vw, 440px);}
button {
  width: 100%; font-size: clamp(2rem, 8vw, 4rem);
  padding: 1.25rem; border-radius: 18px; border: 2px solid #444;
  background: var(--btn); color: var(--fg); touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
button:active { background: var(--btnActive); transform: scale(0.99); }
#plus { border-color:#2e7d32; }
#minus { border-color:#ad1457; }
.row { display:flex; gap:1rem; width:100%; }
.small { font-size: 1rem; padding:0.9rem; }
.readout { font-variant-numeric: tabular-nums; opacity:0.85; }
</style>
</head>
<body>
<div class="container">
  <div class="stack">
    <div class="readout" id="readout">--%</div>
    <button id="plus">+</button>
    <button id="minus">−</button>
    <div class="row">
      <button class="small" id="mute">Mute</button>
      <button class="small" id="step">Step: 5%</button>
    </div>
  </div>
</div>
<script>
const qs = new URLSearchParams(location.search);
const TOKEN = qs.get('token') || localStorage.getItem('token') || '';
if (TOKEN) localStorage.setItem('token', TOKEN);
let step = parseInt(localStorage.getItem('step') || '5', 10);
const readout = document.getElementById('readout');
const stepBtn = document.getElementById('step');

function api(method='GET', body=null) {
  return fetch('/api/volume', {
    method,
    headers: Object.assign({'Content-Type':'application/json'}, TOKEN?{'X-Auth-Token':TOKEN}:{}),
    body: body?JSON.stringify(body):undefined
  }).then(r => r.json());
}

function refresh(){
  api('GET').then(j=>{
    if (j && typeof j.volume !== 'undefined') {
      readout.textContent = j.volume + '%' + (j.muted ? ' (muted)' : '');
    } else { readout.textContent = 'Err'; }
  }).catch(()=> readout.textContent = 'Err');
}

document.getElementById('plus').addEventListener('click', ()=> api('POST', {action:'up', step}).then(refresh));
document.getElementById('minus').addEventListener('click', ()=> api('POST', {action:'down', step}).then(refresh));
document.getElementById('mute').addEventListener('click', ()=> api('POST', {action:'mute'}).then(refresh));
stepBtn.addEventListener('click', ()=>{
  const choices=[2,5,10,15,20];
  step = choices[(choices.indexOf(step)+1) % choices.length];
  localStorage.setItem('step', String(step));
  stepBtn.textContent = 'Step: ' + step + '%';
});
stepBtn.textContent = 'Step: ' + step + '%';
refresh();
setInterval(refresh, 4000);
</script>
</body>
</html>
```
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

https://stackoverflow.com/a/27091782/12118546

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
- pactl works for both PulseAudio and PipeWire (via PulseAudio compatibility). If pactl isn’t present, ensure pulseaudio-utils is installed.
- Security: keep this LAN‑only, use a token, and don’t expose the port to the internet unless you put it behind HTTPS and proper auth.

```
Prompt tokens: 43, Completion tokens: 5560, Total price: 0.056 USD
```
