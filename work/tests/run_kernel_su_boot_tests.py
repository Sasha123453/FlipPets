"""Module boot/Action fixtures on emulator-5554. UID/storage/controller are stubbed.

Execute the actual module wrapper with only its fixed paths/interpreter rebased
to an isolated emulator directory. This proves shell branches, not root/SELinux.
"""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = '/data/local/tmp/flip-pets-ksu-boot-fixture'
ADB = 'C:/platform-tools/adb.exe'


def adb(*args, ok=True):
    p = subprocess.run([ADB, '-s', 'emulator-5554', *args], capture_output=True,
                       text=True, encoding='utf-8', errors='replace', timeout=25)
    if ok and p.returncode:
        raise RuntimeError(p.stdout + p.stderr)
    return p


def shell(command, ok=True):
    return adb('shell', command, ok=ok)


assert shell('getprop ro.kernel.qemu').stdout.strip() == '1', 'Emulator required'
source = ROOT / 'work/kernel-su/module-control.sh'
raw = source.read_text(encoding='utf-8')
replacements = {
    '/sdcard/Android/data/org.flippets.app/files/controller-stop': BASE + '/appfiles/controller-stop',
    '/data/local/tmp/flip-pets-enabled': BASE + '/runtime',
    '/data/local/tmp/flip-pets-active': BASE + '/active',
    '/data/local/tmp/flip-pets-supervisor.lock': BASE + '/supervisor.lock',
    '/system/bin/sh "$CONTROLLER"': 'fixture_controller',
}
for old, new in replacements.items():
    assert old in raw, old
    raw = raw.replace(old, new)
preamble = f'''#!/system/bin/sh
TEST={BASE}
id() {{ echo 0; }}
getprop() {{ cat "$TEST/device"; }}
pm() {{ [ ! -f "$TEST/no_package" ] && echo package:/fixture/FlipPets.apk; }}
cmd() {{
 [ "$*" = 'user is-user-unlocked 0' ] || return 1
 if [ -f "$TEST/unlocked" ]; then echo true; else echo false; fi
}}
sleep() {{
 n=$(cat "$TEST/sleeps" 2>/dev/null || echo 0); echo $((n+1)) > "$TEST/sleeps"
 case "$(cat "$TEST/during_wait" 2>/dev/null)" in
 unlock) mkdir -p "$TEST/appfiles"; touch "$TEST/unlocked" ;;
 stop) mkdir -p "$TEST/appfiles"; touch "$TEST/unlocked" "$TEST/appfiles/controller-stop" ;;
 cancel) rm -f "$TEST/session-enabled" ;;
 disable) touch "$TEST/disable" ;;
 remove) touch "$TEST/remove" ;;
 esac
}}
fixture_controller() {{
 echo "$1" >> "$TEST/calls"
 [ ! -f "$TEST/child_failure" ] || return 1
 if [ -f "$TEST/concurrent_stop" ]; then touch "$TEST/appfiles/controller-stop"; return 1; fi
 if [ "$1" = resume ]; then [ ! -e "$TEST/appfiles/controller-stop" ] || return 1; fi
 if [ "$1" = supervise ]; then rm -f "$TEST/appfiles/controller-stop"; fi
 if [ -f "$TEST/disable_after_ack" ]; then touch "$TEST/disable"; fi
 return 0
}}
'''
local = ROOT / 'work/ksu-check/module-boot-fixture.sh'
local.parent.mkdir(exist_ok=True)
local.write_text(preamble + raw, encoding='utf-8', newline='\n')
shell(f'mkdir -p {BASE}')
adb('push', str(local), BASE + '/wrapper.sh')
results = []


def reset(*, opted=True, ready=True):
    # All targets are literal children of the dedicated fixture directory.
    shell(f'rm -f {BASE}/session-enabled {BASE}/session-owned {BASE}/disable {BASE}/remove '
          f'{BASE}/unlocked {BASE}/calls {BASE}/sleeps {BASE}/during_wait '
          f'{BASE}/child_failure {BASE}/concurrent_stop {BASE}/no_package {BASE}/disable_after_ack\n'
          f'mkdir -p {BASE}/appfiles\nrm -f {BASE}/appfiles/controller-stop\necho ruyi > {BASE}/device')
    if opted:
        shell(f'touch {BASE}/session-enabled')
    if ready:
        shell(f'touch {BASE}/unlocked')


def exists(path):
    return shell(f'test -e {BASE}/{path}', ok=False).returncode == 0


def invoke(action='boot'):
    return shell(f'sh {BASE}/wrapper.sh {action}', ok=False)


def calls():
    return shell(f'cat {BASE}/calls', ok=False).stdout.splitlines()


def check(value, name):
    assert value, name
    results.append(dict(case=name, ok=True))


reset(opted=False, ready=False); p = invoke()
check(p.returncode == 0 and not calls() and not exists('sleeps'), 'installation without opt-in never waits or starts')
reset(ready=False); shell(f'echo unlock > {BASE}/during_wait'); p = invoke()
check(p.returncode == 0 and calls() == ['resume'] and exists('session-owned'), 'locked storage waits, then uses unattended resume')
reset(ready=False); shell(f'echo stop > {BASE}/during_wait'); p = invoke()
check(p.returncode == 0 and not calls() and exists('appfiles/controller-stop') and not exists('session-enabled'), 'Stop revealed at first unlock cancels opt-in without being cleared')
for action in ['cancel', 'disable', 'remove']:
    reset(ready=False); shell(f'echo {action} > {BASE}/during_wait'); p = invoke()
    check(p.returncode == 0 and not calls(), f'{action} cancels storage wait')
reset(ready=False); p = invoke()
check(p.returncode != 0 and not calls() and exists('session-enabled') and
      shell(f'cat {BASE}/sleeps').stdout.strip() == '120', 'storage wait is bounded and does not clear opt-in or start')
reset(); shell(f'touch {BASE}/appfiles/controller-stop'); p = invoke()
check(p.returncode == 0 and not calls() and not exists('session-enabled') and exists('appfiles/controller-stop'), 'boot respects a visible Stop')
reset(); shell(f'touch {BASE}/concurrent_stop'); p = invoke()
check(p.returncode != 0 and calls() == ['resume'] and exists('appfiles/controller-stop') and not exists('session-enabled'), 'Stop during controller startup is preserved and disables opt-in')
reset(); shell(f'touch {BASE}/child_failure'); p = invoke()
check(p.returncode != 0 and not exists('session-owned') and not exists('session-enabled'), 'failed child acknowledgement cannot create successful ownership or opt-in')
reset(opted=False); shell(f'touch {BASE}/appfiles/controller-stop'); p = invoke('toggle')
check(p.returncode == 0 and calls() == ['supervise'] and not exists('appfiles/controller-stop') and exists('session-enabled'), 'only explicit Action chooses Start and clears old Stop')
reset(); shell(f'touch {BASE}/appfiles/controller-stop'); p = invoke('toggle')
check(p.returncode == 0 and not calls() and not exists('session-enabled') and exists('appfiles/controller-stop'), 'Action while opted in disables rather than resurrecting a stopped session')
reset(opted=False); shell(f'touch {BASE}/disable_after_ack'); p = invoke('toggle')
check(p.returncode != 0 and calls() == ['supervise', 'disable'] and not exists('session-enabled'), 'module disable arriving after acknowledgement tears down the new session')
reset(); shell(f'echo bixi > {BASE}/device'); p = invoke()
check(p.returncode != 0 and not calls(), 'wrong device is refused')
reset(); shell(f'touch {BASE}/no_package'); p = invoke()
check(p.returncode != 0 and not calls(), 'missing APK is refused')
report = dict(environment='emulator-5554; UID0, storage availability and controller responses stubbed; no physical root proof',
              wrapperSha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              fixtureSha256=hashlib.sha256(local.read_bytes()).hexdigest(),
              pathReplacements=replacements, results=results)
out = ROOT / 'work/qa-final/kernel-su-boot-tests.json'
out.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
