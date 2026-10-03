"""Controller integration fixtures on our emulator only, never a physical phone."""
import pathlib,subprocess,json,time,hashlib
r=pathlib.Path(__file__).resolve().parents[1];adb=pathlib.Path('C:/platform-tools/adb.exe');base='/data/local/tmp/flip-pets-fixture'
(r/'qa-final').mkdir(exist_ok=True)
def call(*args,ok=True):
    p=subprocess.run([str(adb),'-s','emulator-5554',*args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=25)
    if ok and p.returncode:raise RuntimeError(p.stdout+p.stderr)
    return p
def shell(text,ok=True):return call('shell',text,ok=ok)
assert shell('getprop ro.kernel.qemu').stdout.strip()=='1','Emulator required'
shell('mkdir -p '+base)
call('push',str(r.parent/'outputs'/'flip-pets-control.sh'),base+'/control.sh')
call('push',str(r/'tests'/'controller-fixture.sh'),base+'/wrapper.sh')
call('push',str(r/'research'/'ruyi-display_layout_configuration.xml'),base+'/layout')
def setup():
    shell(f'echo ruyi > {base}/device\necho 3 > {base}/state\necho 3 > {base}/base\necho Awake > {base}/wake\necho false > {base}/locked\nrm -f {base}/override {base}/reject {base}/reject_count {base}/display_off_reads {base}/display_state {base}/events {base}/launches {base}/foreign_on_reject {base}/resets {base}/app_active /data/local/tmp/flip-pets-active /data/local/tmp/flip-pets-start-failures.log /sdcard/Android/data/org.flippets.app/files/controller-stop')
def invoke(action,ok=True):return shell(f'sh {base}/wrapper.sh {action}',ok=ok)
def check(condition,name):
    assert condition,name
    results.append({'case':name,'ok':True})
results=[]
setup();invoke('start');check(shell(f'cat {base}/state').stdout.strip()=='5','start activates presentation');check('--display 1' in shell(f'cat {base}/launch').stdout,'start targets cover display');invoke('stop');check(shell(f'cat {base}/state').stdout.strip()=='3','stop resets base state')
setup();invoke('start');shell(f'echo 0 > {base}/base');invoke('watch');check(shell(f'cat {base}/state').stdout.strip()=='0','fold watcher restores folded state')
setup();invoke('start');shell(f'echo Asleep > {base}/wake');invoke('watch');check(shell(f'cat {base}/state').stdout.strip()=='3','sleep watcher resets override')
setup();shell(f'echo 3 > {base}/display_off_reads');invoke('start');events=shell(f'cat {base}/events').stdout.splitlines();check(events.count('display OFF')==3 and 'launch OFF' not in events and events[-2:]==['compat ON','launch ON'],'display OFF to ON transition waits before launch and reapplies package compatibility');invoke('stop')
setup();shell(f'echo 1 > {base}/reject_count');invoke('start');check(len(shell(f'cat {base}/launches').stdout.splitlines())==2 and shell(f'cat {base}/state').stdout.strip()=='5','first refused launch retries once and succeeds in same owned request');check('attempt=1/3' in shell('cat /data/local/tmp/flip-pets-start-failures.log').stdout and 'fixture launch refusal' in shell('cat /data/local/tmp/flip-pets-start-failures.log').stdout,'exact first refusal remains in independent history after success');invoke('stop')
setup();shell(f'touch {base}/reject');started=time.monotonic();p=invoke('start',ok=False);elapsed=time.monotonic()-started;check(p.returncode!=0 and shell(f'cat {base}/state').stdout.strip()=='3' and len(shell(f'cat {base}/launches').stdout.splitlines())==3 and elapsed<15,'permanent refusal uses exactly three bounded attempts and restores stock');check(shell('test -f /data/local/tmp/flip-pets-active',ok=False).returncode!=0,'permanent refusal removes owned marker')
setup();shell(f'echo 100 > {base}/display_off_reads');p=invoke('start',ok=False);check(p.returncode!=0 and shell(f'cat {base}/state').stdout.strip()=='3' and shell(f'test -f {base}/launches',ok=False).returncode!=0,'display never ON times out without attempting an activity and restores stock')
setup();shell(f'echo 1 > {base}/reject_count\ntouch {base}/foreign_on_reject');p=invoke('start',ok=False);check(p.returncode!=0 and shell(f'cat {base}/state').stdout.strip()=='4' and len(shell(f'cat {base}/launches').stdout.splitlines())==1 and shell(f'test -f {base}/resets',ok=False).returncode!=0,'foreign override arriving after refusal is preserved without retry or reset')
setup();shell(f'head -c 70000 /dev/zero > /data/local/tmp/flip-pets-start-failures.log\ntouch {base}/reject');invoke('start',ok=False);check(int(shell('wc -c < /data/local/tmp/flip-pets-start-failures.log').stdout.strip())<=65536 and 'attempt=3/3' in shell('tail -c 1500 /data/local/tmp/flip-pets-start-failures.log').stdout,'failure history is bounded to 64 KiB and retains latest refusal')
setup();shell(f'touch {base}/override');p=invoke('start',ok=False);check(p.returncode!=0 and 'Another app' in p.stderr+p.stdout,'existing override is refused')
setup();shell(f'echo bixi > {base}/device');p=invoke('start',ok=False);check(p.returncode!=0 and 'only for MIX Flip' in p.stderr+p.stdout,'wrong device is refused')
setup()
record={'environment':'emulator-5554; stubbed stock command responses, not a physical MIX Flip','controller_sha256':hashlib.sha256((r.parent/'outputs'/'flip-pets-control.sh').read_bytes()).hexdigest(),'results':results}
(r/'qa-final'/'controller-tests.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print(json.dumps(record,indent=2))
