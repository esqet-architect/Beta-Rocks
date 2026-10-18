#!/usr/bin/env python3
import os, json, secrets, subprocess, threading, uuid, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
TOKEN = os.environ.get('FOSSIL_TOKEN') or secrets.token_urlsafe(32)
JOBS = {}; LOCK = threading.Lock()

COMMANDS = {
    'preflight': ['python3', '-m', 'fossil_scanner.cli', 'preflight', '--work-dir', str(HOME/'fieldwork')],
    'daily_status': ['bash', str(HOME/'daily_status.sh')],
    'capture_photos': ['bash', str(HOME/'capture_photos.sh')],
    'analyzer': ['bash', str(HOME/'run_analyzer.sh')],
    # NEW: The Physics Engine
    'scan_rock': ['python3', str(ROOT/'src/esqet_core/master_scanner.py'), str(HOME/'specimen.jpg')]
}

def exists(key):
    if key == 'preflight': return (ROOT/'src/fossil_scanner/cli.py').is_file()
    if key == 'scan_rock': return (ROOT/'src/esqet_core/master_scanner.py').is_file()
    return Path(COMMANDS[key][1]).is_file()

def worker(key, jid):
    logdir = HOME/'fieldwork/menu_jobs'; logdir.mkdir(parents=True, exist_ok=True)
    logfile = logdir/(jid+'.log')
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT/'src') + os.pathsep + env.get('PYTHONPATH', '')
    try:
        with open(logfile, 'wb') as f:
            p = subprocess.Popen(COMMANDS[key], cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
            with LOCK: JOBS[jid].update(pid=p.pid, log=str(logfile))
            try: code = p.wait(timeout=300)
            except subprocess.TimeoutExpired:
                import signal
                os.killpg(p.pid, signal.SIGTERM)
                try: p.wait(timeout=5)
                except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL); p.wait()
                with LOCK: JOBS[jid].update(state='timed_out', returncode=p.returncode)
                return
        with LOCK: JOBS[jid].update(state='completed' if code == 0 else 'failed', returncode=code)
    except Exception as e:
        with LOCK: JOBS[jid].update(state='failed', error=str(e))

def dispatch(d):
    action = d.get('action')
    if action == 'status':
        return {'tools': {k: {'available': exists(k), 'command': v} for k, v in COMMANDS.items()}}
    if action == 'launch':
        key = d.get('tool')
        if key not in COMMANDS or not exists(key): raise ValueError('Tool missing')
        with LOCK:
            if any(j['state'] == 'running' for j in JOBS.values()): raise ValueError('Job running')
            jid = str(uuid.uuid4()); JOBS[jid] = {'id': jid, 'tool': key, 'state': 'running', 'started_unix': time.time()}
        threading.Thread(target=worker, args=(key, jid), daemon=True).start()
        return {'id': jid, 'state': 'running'}
    if action == 'job':
        with LOCK:
            return JOBS.get(d.get('id'), {'error': 'unknown'})

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            l = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(l))
            if data.get('token') != TOKEN: raise ValueError('Bad token')
            res = dispatch(data)
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps(res).encode())
        except Exception as e:
            self.send_response(400); self.end_headers(); self.wfile.write(json.dumps({'error': str(e)}).encode())

if __name__ == '__main__':
    print(f"Menu Bridge running. TOKEN={TOKEN}")
    ThreadingHTTPServer(('localhost', 8765), Handler).serve_forever()
