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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
