"""Fresh/interrupted root-state initialization, emulator UID metadata stubbed."""
from pathlib import Path
import hashlib,json,subprocess,time
from controller_test_support import STAT_STUB

ROOT=Path(__file__).resolve().parents[2]
BASE='/data/local/tmp/flip-pets-state-fixture-'+str(time.time_ns())
def adb(*args):return subprocess.check_output(['C:/platform-tools/adb.exe','-s','emulator-5554',*args],text=True,encoding='utf-8',errors='replace',timeout=25)
assert adb('shell','getprop ro.kernel.qemu').strip()=='1'
source=ROOT/'work/kernel-su/module-state.sh'
helper=source.read_text(encoding='utf-8').replace('/data/adb/flippets-controller',BASE+'/state').replace('/data/adb',BASE+'/adb')
fixture=ROOT/'work/ksu-check/state-initialization.sh'
fixture.write_text(STAT_STUB+helper,encoding='utf-8',newline='\n')
adb('shell',f'mkdir -p {BASE}/adb\nchmod 700 {BASE}/adb')
adb('push',str(fixture),BASE+'/initialize.sh')
results=[]
for label in ('fresh installation','interrupted empty initialization'):
    adb('shell','sh '+BASE+'/initialize.sh')
    assert adb('shell',f'cat {BASE}/state/schema').strip()=='1'
    assert adb('shell',f'test ! -e {BASE}/state/session-enabled && test ! -e {BASE}/state/session-owned && stat -c %a {BASE}/state').strip()=='700'
    results.append(dict(case=label+' creates schema/private runtime without consent or ownership',ok=True))
    # Only fixed empty fixture leaves/directories; no recursive removal.
    adb('shell',f'rm {BASE}/state/schema\nrmdir {BASE}/state/runtime\nrmdir {BASE}/state\nmkdir -m 700 {BASE}/state')
record=dict(environment='Identity-verified emulator-5554; root UID ownership metadata stubbed, not actual root/SELinux',stateHelperSha256=hashlib.sha256(source.read_bytes()).hexdigest(),fixtureSha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),results=results)
(ROOT/'work/qa-final/kernel-su-state-tests.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
