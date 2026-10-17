import os,json,secrets,subprocess,threading,uuid,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1]
HOME=Path.home()
TOKEN=os.environ.get('FOSSIL_TOKEN') or secrets.token_urlsafe(32)
JOBS={}; LOCK=threading.Lock()
COMMANDS={
 'preflight':['python3','-m','fossil_scanner.cli','preflight','--work-dir',str(HOME/'fieldwork')],
 'daily_status':['bash',str(HOME/'daily_status.sh')],
 'capture_photos':['bash',str(HOME/'capture_photos.sh')],
 'analyzer':['bash',str(HOME/'run_analyzer.sh')],
}
def exists(key):
 return (ROOT/'src/fossil_scanner/cli.py').is_file() if key=='preflight' else Path(COMMANDS[key][1]).is_file()
def worker(key,jid):
 logdir=HOME/'fieldwork/menu_jobs';logdir.mkdir(parents=True,exist_ok=True)
 logfile=logdir/(jid+'.log'); env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')+os.pathsep+env.get('PYTHONPATH','')
 try:
  with open(logfile,'wb') as f:
   p=subprocess.Popen(COMMANDS[key],cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
   with LOCK:JOBS[jid].update(pid=p.pid,log=str(logfile))
   try: code=p.wait(timeout=300)
   except subprocess.TimeoutExpired:
    import signal
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    with LOCK:JOBS[jid].update(state='timed_out',returncode=p.returncode)
    return
  with LOCK:JOBS[jid].update(state='completed' if code==0 else 'failed',returncode=code)
 except Exception as e:
  with LOCK:JOBS[jid].update(state='failed',error=str(e))
def dispatch(d):
 action=d.get('action')
 if action=='status':
  return {'tools':{k:{'available':exists(k),'command':v} for k,v in COMMANDS.items()},'warning':'Available means script exists, not instrument verified. Scripts run noninteractively with a 300-second limit. Review their contents before use.'}
 if action=='launch':
  key=d.get('tool')
  if key not in COMMANDS or not exists(key):raise ValueError('Tool missing or not allowlisted')
  with LOCK:
   if any(j['state']=='running' for j in JOBS.values()):raise ValueError('Another job is running; wait before launching another instrument task')
   jid=str(uuid.uuid4());JOBS[jid]={'id':jid,'tool':key,'state':'running','started_unix':time.time()}
  threading.Thread(target=worker,args=(key,jid),daemon=True).start();return {'id':jid,'state':'running'}
 if action=='job':
  with LOCK:
   if d.get('id') not in JOBS:raise ValueError('Unknown job')
   j=dict(JOBS[d['id']])
  if j.get('log'):
   with open(j['log'],'rb') as f:
    f.seek(0,2);size=f.tell();f.seek(max(0,size-65536));j['output_tail']=f.read().decode(errors='replace')
  return j
 raise ValueError('Unknown action')
class Handler(BaseHTTPRequestHandler):
 def do_POST(self):
  if self.headers.get('Authorization')!='Bearer '+TOKEN:self.send_error(401);return
  try:
   n=int(self.headers.get('Content-Length','0'))
   if not 0<n<16384:raise ValueError('Invalid request size')
   result=dispatch(json.loads(self.rfile.read(n)));status=200
  except Exception as e:result={'error':str(e)};status=400
  raw=json.dumps(result).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def log_message(self,*args):pass
if __name__=='__main__':
 print('FossilScanner menu bridge — localhost only',flush=True)
 print('Token:',TOKEN,flush=True)
 print('Review allowlisted scripts before launching them from the app.',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
