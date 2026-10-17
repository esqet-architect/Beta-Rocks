#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/Beta-Rocks}"
test -d "$ROOT/src/fossil_scanner" || { echo "Existing Beta-Rocks source not found"; exit 1; }
BACKUP="$HOME/fossil-menu-backup-$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$BACKUP"
for item in flutter_frontend .github/workflows/flutter-apk.yml tools/menu_bridge.py; do
 if [ -e "$ROOT/$item" ]; then
  mkdir -p "$BACKUP/$(dirname "$item")"
  cp -a "$ROOT/$item" "$BACKUP/$item"
 fi
done
if [ -d "$ROOT/flutter_frontend" ]; then
 mv "$ROOT/flutter_frontend" "$BACKUP/frontend-before-replacement"
fi

mkdir -p "$ROOT/tools"
cat <<'FOSSIL_FILE_EOF' > "$ROOT/tools/menu_bridge.py"
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

FOSSIL_FILE_EOF

mkdir -p "$ROOT/flutter_frontend"
cat <<'FOSSIL_FILE_EOF' > "$ROOT/flutter_frontend/pubspec.yaml"
name: fossil_menu
description: FossilScanner multi-button field console
publish_to: none
version: 0.5.0+1
environment:
  sdk: '>=3.4.0 <4.0.0'
dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.2
dev_dependencies:
  flutter_test:
    sdk: flutter
flutter:
  uses-material-design: true

FOSSIL_FILE_EOF

mkdir -p "$ROOT/flutter_frontend"
cat <<'FOSSIL_FILE_EOF' > "$ROOT/flutter_frontend/analysis_options.yaml"
analyzer:
  exclude:
    - build/**

FOSSIL_FILE_EOF

mkdir -p "$ROOT/flutter_frontend/lib"
cat <<'FOSSIL_FILE_EOF' > "$ROOT/flutter_frontend/lib/phi.dart"
import 'dart:math' as math;
final double goldenRatio=(1+math.sqrt(5))/2;
Map<String,dynamic> phiCheck(double a,double b,double tolerance){
 if(!a.isFinite||!b.isFinite||a<=0||b<=0||!tolerance.isFinite||tolerance<0)throw ArgumentError('Positive finite lengths and nonnegative tolerance required');
 final ratio=math.max(a,b)/math.min(a,b);
 if(!ratio.isFinite)throw ArgumentError('Ratio overflow');
 final deviation=100*(ratio-goldenRatio).abs()/goldenRatio;
 return {'a':a,'b':b,'ratio':ratio,'phi':goldenRatio,'deviation_percent':deviation,'tolerance_percent':tolerance,'within_tolerance':deviation<=tolerance,'interpretation':'Numerical proximity only, not evidence of biological origin or a golden spiral'};
}

FOSSIL_FILE_EOF

mkdir -p "$ROOT/flutter_frontend/lib"
cat <<'FOSSIL_FILE_EOF' > "$ROOT/flutter_frontend/lib/main.dart"
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'phi.dart';
const teal=Color(0xFF68E2C7),copper=Color(0xFFE7B27D),panelColor=Color(0xFF172530);
void main()=>runApp(MaterialApp(debugShowCheckedModeBanner:false,theme:ThemeData(useMaterial3:true,brightness:Brightness.dark,scaffoldBackgroundColor:const Color(0xFF09131C),colorScheme:ColorScheme.fromSeed(seedColor:teal,brightness:Brightness.dark)),home:const Menu()));
class Menu extends StatefulWidget{const Menu({super.key});@override State<Menu> createState()=>_MenuState();}
class _MenuState extends State<Menu>{
 final token=TextEditingController(),a=TextEditingController(),b=TextEditingController(),tolerance=TextEditingController(text:'2'),specimen=TextEditingController();
 String output='Start tools/menu_bridge.py in Termux. Enter its token, then connect.',job='';bool busy=false;int page=0;Map<String,dynamic> tools={};Map<String,dynamic>? phi;
 @override void dispose(){for(final c in [token,a,b,tolerance,specimen]){c.dispose();}super.dispose();}
 Future<Map<String,dynamic>> request(Map<String,dynamic> data)async{
  final r=await http.post(Uri.parse('http://127.0.0.1:8765'),headers:{'Content-Type':'application/json','Authorization':'Bearer ${token.text.trim()}'},body:jsonEncode(data)).timeout(const Duration(seconds:15));
  if(r.statusCode!=200)throw Exception('HTTP ${r.statusCode}: ${r.body}');
  return Map<String,dynamic>.from(jsonDecode(r.body) as Map);
 }
 Future<void> perform(Map<String,dynamic> data)async{setState(()=>busy=true);try{final result=await request(data);if(!mounted)return;setState((){output=const JsonEncoder.withIndent('  ').convert(result);if(data['action']=='status')tools=Map<String,dynamic>.from(result['tools'] as Map);if(data['action']=='launch')job=result['id'] as String;});}catch(e){if(mounted)setState(()=>output=e.toString());}finally{if(mounted)setState(()=>busy=false);}}
 Future<void> launch(String key,String label)async{
  final approved=await showDialog<bool>(context:context,builder:(c)=>AlertDialog(title:Text('Run $label?'),content:const Text('Runs the existing allowlisted Termux command. It may capture data, access sensors or contact services. Input prompts are unsupported; timeout is 300 seconds. Review the script first.'),actions:[TextButton(onPressed:()=>Navigator.pop(c,false),child:const Text('Cancel')),FilledButton(onPressed:()=>Navigator.pop(c,true),child:const Text('Run'))]));
  if(approved==true&&mounted)await perform({'action':'launch','tool':key});
 }
 Widget box(String title,List<Widget> children)=>Container(margin:const EdgeInsets.only(bottom:16),padding:const EdgeInsets.all(18),decoration:BoxDecoration(color:panelColor,borderRadius:BorderRadius.circular(20),border:Border.all(color:teal.withAlpha(40))),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(title,style:const TextStyle(color:copper,letterSpacing:1.3,fontWeight:FontWeight.bold)),const SizedBox(height:14),...children]));
 Widget field(String label,TextEditingController c,{bool secret=false,bool numeric=false})=>Padding(padding:const EdgeInsets.only(bottom:12),child:TextField(controller:c,obscureText:secret,keyboardType:numeric?const TextInputType.numberWithOptions(decimal:true):TextInputType.text,decoration:InputDecoration(labelText:label,border:const OutlineInputBorder()),onChanged:(_){if(c!=token)setState(()=>phi=null);}));
 Widget tool(String key,String label,IconData icon){final available=tools[key] is Map&&tools[key]['available']==true;return Padding(padding:const EdgeInsets.only(bottom:10),child:SizedBox(width:double.infinity,child:OutlinedButton.icon(onPressed:!busy&&available?()=>launch(key,label):null,icon:Icon(icon),label:Padding(padding:const EdgeInsets.all(12),child:Text('$label • ${available?'SCRIPT FOUND':'NOT CONNECTED / MISSING'}')))));}
 void calculate(){try{final d=phiCheck(double.parse(a.text),double.parse(b.text),double.parse(tolerance.text));setState(()=>phi={...d,'specimen_id':specimen.text,'timestamp':DateTime.now().toUtc().toIso8601String()});}catch(e){setState(()=>output=e.toString());ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.toString())));}}
 @override Widget build(BuildContext context){final screens=[
 ListView(padding:const EdgeInsets.all(18),children:[box('FIELD COMMAND CENTER',[const Text('Observe. Measure.\nTest the interpretation.',style:TextStyle(fontSize:29,fontWeight:FontWeight.w800)),const SizedBox(height:14),const Text('Existing tools, one menu. No invented hardware readings.'),const SizedBox(height:12),FilledButton.icon(onPressed:()=>setState(()=>page=1),icon:const Icon(Icons.architecture),label:const Text('Open φ lab'))]),box('TERMUX OPERATIONS',[tool('preflight','Hardware preflight',Icons.radar),tool('daily_status','Daily environmental report',Icons.cloud_outlined),tool('capture_photos','Photo capture script',Icons.camera_alt_outlined),tool('analyzer','Existing analyzer script',Icons.analytics_outlined)]),box('RIG CAPABILITIES — NOT CONFIGURED',[const Text('Turntable motor + white/UV sequence\nCalibrated acoustic sweep\nExternal metal-detector mapping\nLiDAR terrain rendering\nResNet inference\n\nThese require adapters, calibration and/or model assets. They are not enabled by the menu.')])]),
 ListView(padding:const EdgeInsets.all(18),children:[box('PHI / RATIO LAB',[field('Specimen ID',specimen),field('Length A — same units as B',a,numeric:true),field('Length B',b,numeric:true),field('Tolerance (%)',tolerance,numeric:true),FilledButton.icon(onPressed:calculate,icon:const Icon(Icons.calculate),label:const Text('Check ratio')),const SizedBox(height:12),const Text('Longer / shorter. Tolerance is user-selected, not statistical significance. No automatic image or spiral analysis.')]),if(phi!=null)box('RESULT',[Text((phi!['ratio'] as double).toStringAsFixed(10),style:const TextStyle(color:teal,fontSize:36,fontWeight:FontWeight.bold)),Text('Deviation: ${(phi!['deviation_percent'] as double).toStringAsFixed(6)}%'),Text(phi!['within_tolerance']==true?'Within selected tolerance':'Outside selected tolerance'),TextButton.icon(onPressed:()async{await Clipboard.setData(ClipboardData(text:const JsonEncoder.withIndent('  ').convert(phi)));},icon:const Icon(Icons.copy),label:const Text('Copy measurement JSON')),SelectableText(const JsonEncoder.withIndent('  ').convert(phi))])]),
 ListView(padding:const EdgeInsets.all(18),children:[box('LOCALHOST CONNECTION',[field('Bridge bearer token',token,secret:true),const Text('Same phone • 127.0.0.1:8765\nToken is kept in memory only.'),const SizedBox(height:12),FilledButton(onPressed:busy?null:()=>perform({'action':'status'}),child:const Text('Connect / check scripts'))]),box('LATEST JOB',[SelectableText(job.isEmpty?'No job started':job),const SizedBox(height:8),FilledButton(onPressed:busy||job.isEmpty?null:()=>perform({'action':'job','id':job}),child:const Text('Refresh job output')),const Text('Jobs continue in Termux. Refresh manually. No cancel button; backend enforces a 300-second timeout.')]),if(busy)const LinearProgressIndicator(),box('STATUS / RAW OUTPUT',[SelectableText(output),TextButton(onPressed:()async{await Clipboard.setData(ClipboardData(text:output));},child:const Text('Copy output'))])])];
 return Scaffold(appBar:AppBar(title:const Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('FOSSILSCANNER',style:TextStyle(letterSpacing:2,fontWeight:FontWeight.w800,fontSize:19)),Text('MULTI-MODAL FIELD CONSOLE',style:TextStyle(fontSize:10,color:copper,letterSpacing:1.4))])),body:SafeArea(child:IndexedStack(index:page,children:screens)),bottomNavigationBar:NavigationBar(selectedIndex:page,onDestinationSelected:(i)=>setState(()=>page=i),destinations:const[NavigationDestination(icon:Icon(Icons.dashboard_outlined),label:'Operations'),NavigationDestination(icon:Icon(Icons.architecture),label:'φ lab'),NavigationDestination(icon:Icon(Icons.cable),label:'Connection')]));
 }
}

FOSSIL_FILE_EOF

mkdir -p "$ROOT/flutter_frontend/test"
cat <<'FOSSIL_FILE_EOF' > "$ROOT/flutter_frontend/test/phi_test.dart"
import 'package:flutter_test/flutter_test.dart';
import 'package:fossil_menu/phi.dart';
void main(){
 test('phi match',(){expect(phiCheck(goldenRatio,1,1)['within_tolerance'],true);});
 test('nonmatch',(){expect(phiCheck(1,1,2)['within_tolerance'],false);});
 test('reject zero',(){expect(()=>phiCheck(0,1,2),throwsArgumentError);});
 test('symmetric',(){expect(phiCheck(1,2,2)['ratio'],phiCheck(2,1,2)['ratio']);});
}

FOSSIL_FILE_EOF

mkdir -p "$ROOT/.github/workflows"
cat <<'FOSSIL_FILE_EOF' > "$ROOT/.github/workflows/flutter-apk.yml"
name: FossilScanner Menu APK
on:
  workflow_dispatch:
  push:
    branches: [main]
    paths: ['flutter_frontend/**', '.github/workflows/flutter-apk.yml']
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    defaults:
      run:
        working-directory: flutter_frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'
      - uses: subosito/flutter-action@v2
        with:
          channel: stable
      - name: Generate Android scaffolding
        run: |
          flutter create --platforms=android --project-name fossil_menu .
          rm -f test/widget_test.dart
          python3 - <<'PY'
          from pathlib import Path
          p=Path('android/app/src/main/AndroidManifest.xml')
          s=p.read_text()
          if 'android.permission.INTERNET' not in s:
              s=s.replace('<application','<uses-permission android:name="android.permission.INTERNET"/>\n<application',1)
          if 'android:usesCleartextTraffic' not in s:
              s=s.replace('<application','<application android:usesCleartextTraffic="true"',1)
          p.write_text(s)
          PY
      - run: flutter pub get
      - run: flutter analyze
      - run: flutter test
      - run: flutter build apk --debug
      - uses: actions/upload-artifact@v4
        with:
          name: FossilScanner-menu-debug
          path: flutter_frontend/build/app/outputs/flutter-apk/app-debug.apk
          if-no-files-found: error

FOSSIL_FILE_EOF

python3 -m py_compile "$ROOT/tools/menu_bridge.py"
printf '\nInstalled. Backup: %s\n' "$BACKUP"
echo 'No Git commit or push was performed.'
echo 'Review tools/menu_bridge.py and the allowlisted scripts before use.'
