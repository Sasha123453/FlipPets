"""Exercise detached supervisor with fixture commands, exclusively on our emulator."""
import pathlib,subprocess,time,json,hashlib
r=pathlib.Path(__file__).resolve().parents[1];adb='C:/platform-tools/adb.exe';base='/data/local/tmp/flip-pets-fixture'
(r/'qa-v02').mkdir(exist_ok=True)
def call(*args,ok=True):
 p=subprocess.run([adb,'-s','emulator-5554',*args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=20)
 if ok and p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p
def shell(command,ok=True):return call('shell',command,ok=ok)
assert shell('getprop ro.kernel.qemu').stdout.strip()=='1','Emulator required'
fixture=(r/'tests/controller-fixture.sh').read_text()
fixture=fixture.replace('nohup() { :; }','sleep() { command sleep 0.1; }')
wrapper=r/'tests/supervisor-fixture.sh';wrapper.write_text(fixture,encoding='utf-8',newline='\n')
shell('mkdir -p '+base)
for p,dest in [(r.parent/'outputs/flip-pets-control.sh','control.sh'),(wrapper,'flip-pets-control.sh'),(r/'research/ruyi-display_layout_configuration.xml','layout')]:call('push',str(p),base+'/'+dest)
def invoke(action,ok=True):return shell(f'sh {base}/flip-pets-control.sh {action}',ok=ok)
def exists(path):return shell(f'test -f {path}',ok=False).returncode==0
def wait_for(test,label):
 deadline=time.monotonic()+12
 while time.monotonic()<deadline:
  if test():return
  time.sleep(.15)
 raise AssertionError(label)
def state(n):return shell(f'cat {base}/state').stdout.strip()==str(n)
results=[]
def check(condition,label):
 assert condition,label;results.append(dict(case=label,ok=True))
def reset():
 invoke('disable');time.sleep(.3)
 shell(f'echo ruyi > {base}/device\necho 3 > {base}/state\necho 3 > {base}/base\necho Awake > {base}/wake\necho false > {base}/locked\nrm -f {base}/override {base}/reject {base}/reject_count {base}/display_off_reads {base}/foreign_on_reject {base}/launches {base}/closed /data/local/tmp/flip-pets-active /sdcard/Android/data/org.flippets.app/files/controller-stop')
try:
 reset();invoke('supervise');wait_for(lambda:state(5),'initial activation')
 check(exists('/data/local/tmp/flip-pets-enabled'),'detached supervisor remains enabled')
 pid=shell('cat /data/local/tmp/flip-pets-supervisor.lock/pid').stdout.strip();invoke('supervise');check(shell('cat /data/local/tmp/flip-pets-supervisor.lock/pid').stdout.strip()==pid,'second enable does not duplicate supervisor')
 shell('echo sensor > /sdcard/Android/data/org.flippets.app/files/hinge-fade-active');shell(f'echo 2 > {base}/base');time.sleep(.6);check(state(5),'sensor-backed fade keeps the existing cover during HALF_OPENED')
 shell(f'echo 1 > {base}/base');wait_for(lambda:state(1),'tent stock reset');check(not exists('/sdcard/Android/data/org.flippets.app/files/hinge-fade-active'),'tent returns stock and clears fade handshake')
 shell(f'echo 3 > {base}/base\necho 3 > {base}/state');wait_for(lambda:state(5),'open after tent')
 shell(f'echo 2 > {base}/base');wait_for(lambda:state(2),'half-open without sensor');check(True,'without a registered sensor HALF_OPENED preserves the stock transition')
 shell(f'echo 3 > {base}/base\necho 3 > {base}/state');wait_for(lambda:state(5),'open after half')
 shell(f'echo 0 > {base}/base');wait_for(lambda:state(0),'fold reset');check(exists(base+'/closed') and exists('/data/local/tmp/flip-pets-enabled'),'fold closes only own cover session and keeps waiting')
 shell(f'echo 3 > {base}/base\necho 3 > {base}/state');wait_for(lambda:state(5),'unfold restart');check(True,'unfold resumes without a connected client')
 shell(f'echo Asleep > {base}/wake');wait_for(lambda:state(3),'sleep reset');check(True,'sleep returns stock mode')
 shell(f'echo Awake > {base}/wake\necho true > {base}/locked');time.sleep(.8);check(state(3),'locked phone is not activated')
 shell(f'echo false > {base}/locked');wait_for(lambda:state(5),'unlock restart');check(True,'unlock restores presentation')
 before=len(shell(f'cat {base}/launches').stdout.splitlines());shell(f'rm -f {base}/app_active');wait_for(lambda:len(shell(f'cat {base}/launches').stdout.splitlines())>before,'activity recovery');check(True,'missing cover activity is restarted after bounded delay')
 shell('echo stop > /sdcard/Android/data/org.flippets.app/files/controller-stop');wait_for(lambda:not exists('/data/local/tmp/flip-pets-enabled'),'local stop');check(state(3),'ordinary APK stop request disables supervisor and resets display')
 reset();shell(f'touch {base}/override\necho 4 > {base}/state');invoke('supervise');time.sleep(.8);check(state(4) and not exists('/data/local/tmp/flip-pets-active'),'foreign override remains untouched');invoke('disable')
 reset();shell(f'touch {base}/reject');invoke('supervise');wait_for(lambda:not exists('/data/local/tmp/flip-pets-enabled'),'bounded launch failures');check(state(3) and len(shell(f'cat {base}/launches').stdout.splitlines())==9,'three failed start batches use at most three attempts each, disable retry loop and restore stock mode')
finally:
 invoke('disable',ok=False);shell('rm -f /sdcard/Android/data/org.flippets.app/files/controller-stop',ok=False)
(r/'qa-v02/supervisor-tests.json').write_text(json.dumps(dict(environment='emulator-5554, stubbed device-state/display/power/keyguard commands; no physical MIX Flip',controller_sha256=hashlib.sha256((r.parent/'outputs/flip-pets-control.sh').read_bytes()).hexdigest(),results=results),indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
