"""Controller integration fixtures on our emulator only, never a physical phone."""
import pathlib,subprocess,json
r=pathlib.Path(__file__).resolve().parents[1];adb=pathlib.Path('C:/platform-tools/adb.exe');base='/data/local/tmp/flip-pets-fixture'
def call(*args,ok=True):
    p=subprocess.run([str(adb),'-s','emulator-5554',*args],capture_output=True,text=True,encoding='utf-8',errors='replace')
    if ok and p.returncode:raise RuntimeError(p.stdout+p.stderr)
    return p
def shell(text,ok=True):return call('shell',text,ok=ok)
assert shell('getprop ro.kernel.qemu').stdout.strip()=='1','Emulator required'
shell('mkdir -p '+base)
call('push',str(r.parent/'outputs'/'flip-pets-control.sh'),base+'/control.sh')
call('push',str(r/'tests'/'controller-fixture.sh'),base+'/wrapper.sh')
call('push',str(r/'research'/'ruyi-display_layout_configuration.xml'),base+'/layout')
def setup():
    shell(f'echo ruyi > {base}/device\necho 3 > {base}/state\necho 3 > {base}/base\necho Awake > {base}/wake\nrm -f {base}/override {base}/reject /data/local/tmp/flip-pets-active')
def invoke(action,ok=True):return shell(f'sh {base}/wrapper.sh {action}',ok=ok)
def check(condition,name):
    assert condition,name
    results.append({'case':name,'ok':True})
results=[]
setup();invoke('start');check(shell(f'cat {base}/state').stdout.strip()=='5','start activates presentation');check('--display 1' in shell(f'cat {base}/launch').stdout,'start targets cover display');invoke('stop');check(shell(f'cat {base}/state').stdout.strip()=='3','stop resets base state')
setup();invoke('start');shell(f'echo 0 > {base}/base');invoke('watch');check(shell(f'cat {base}/state').stdout.strip()=='0','fold watcher restores folded state')
setup();invoke('start');shell(f'echo Asleep > {base}/wake');invoke('watch');check(shell(f'cat {base}/state').stdout.strip()=='3','sleep watcher resets override')
setup();shell(f'touch {base}/reject');p=invoke('start',ok=False);check(p.returncode!=0 and shell(f'cat {base}/state').stdout.strip()=='3','rejected launch rolls back')
setup();shell(f'touch {base}/override');p=invoke('start',ok=False);check(p.returncode!=0 and 'Another app' in p.stderr+p.stdout,'existing override is refused')
setup();shell(f'echo bixi > {base}/device');p=invoke('start',ok=False);check(p.returncode!=0 and 'only for MIX Flip' in p.stderr+p.stdout,'wrong device is refused')
setup()
record={'environment':'emulator-5554; stubbed stock command responses, not a physical MIX Flip','results':results}
(r/'qa-final'/'controller-tests.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print(json.dumps(record,indent=2))
