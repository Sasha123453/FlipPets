"""Module boot/Action fixtures on emulator-5554. UID/storage/controller are stubbed.

Execute the actual module wrapper with only its fixed paths/interpreter rebased
to an isolated emulator directory. This proves shell branches, not root/SELinux.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = '/data/local/tmp/flip-pets-ksu-boot-fixture'
ADB = 'C:/platform-tools/adb.exe'


def adb(*args, ok=True):
    p = subprocess.run([ADB, '-s', 'emulator-5554', *args], capture_output=True,
                       text=True, encoding='utf-8', errors='replace', timeout=25)
    if ok and p.returncode:
        raise RuntimeError(p.stdout + p.stderr)
    return p


def private_paths(text):
    for prefix in (BASE, '$TEST'):
        for name in ('session-enabled', 'session-owned', 'session-cancel', 'session-transition'):
            text = text.replace(prefix + '/' + name, prefix + '/state/' + name)
        for old, new in (('supervisor.lock', 'supervisor.lock'), ('runtime', 'enabled'), ('active', 'active')):
            text = text.replace(prefix + '/' + old, prefix + '/state/runtime/' + new)
    return text


def shell(command, ok=True):
    return adb('shell', 'umask 077\n' + private_paths(command), ok=ok)


assert shell('getprop ro.kernel.qemu').stdout.strip() == '1', 'Emulator required'
source = ROOT / 'work/kernel-su/module-control.sh'
raw = source.read_text(encoding='utf-8')
replacements = {
    '/sdcard/Android/data/org.flippets.app/files/controller-stop': BASE + '/appfiles/controller-stop',
    '/data/local/tmp/flip-pets-enabled': BASE + '/legacy-enabled',
    '/data/local/tmp/flip-pets-active': BASE + '/legacy-active',
    '/data/local/tmp/flip-pets-supervisor.lock': BASE + '/legacy-lock',
    '/system/bin/sh "$CONTROLLER"': 'fixture_controller',
}
for old, new in replacements.items():
    assert old in raw, old
    raw = raw.replace(old, new)
preamble = f'''#!/system/bin/sh
TEST={BASE}
FP_FIXTURE_ACTION=$1
id() {{ echo 0; }}
cat() {{
 if [ "$1" = "$TEST/session-cancel" ] && [ "$FP_FIXTURE_ACTION" = boot ] && [ -f "$TEST/stale_boot" ] && [ ! -f "$TEST/snapshot_taken" ]; then
  old=$(command cat "$1"); touch "$TEST/snapshot_taken"
  for i in $(seq 1 250); do [ -f "$TEST/release_snapshot" ] && break; command sleep 0.02; done
  echo "$old"
 else command cat "$@"; fi
}}
stat() {{
 if [ "$1" = -c ] && [ "$2" = '%u' ]; then
  if [ -f "$TEST/wrong_uid" ] && [ "${{3#/proc/}}" != "$3" ]; then echo 2000; else echo 0; fi
 elif [ "$2" = '%u:%a' ]; then command stat "$@" | sed 's/^2000:/0:/'
 else command stat "$@"; fi
}}
getprop() {{ cat "$TEST/device"; }}
pm() {{ [ ! -f "$TEST/no_package" ] && echo package:/fixture/FlipPets.apk; }}
cmd() {{
 [ "$*" = 'user is-user-unlocked 0' ] || return 1
 if [ -f "$TEST/unlocked" ]; then echo true; else echo false; fi
}}
sleep() {{
 [ "$1" = 5 ] || {{ command sleep 0.02; return; }}
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
 if [ "$1" = supervise ] || [ "$1" = resume ]; then
  if [ -f "$TEST/supervisor.lock/pid" ] && kill -0 "$(cat "$TEST/supervisor.lock/pid")" 2>/dev/null; then
   [ -f "$TEST/runtime" ] || return 1
   return 0
  fi
  mkdir -p "$TEST/supervisor.lock"; touch "$TEST/runtime"
  nohup sh "$TEST/flip-pets-control.sh" run > "$TEST/child.log" 2>&1 < /dev/null &
  child=$!; echo "$child" > "$TEST/supervisor.lock/pid"
  for i in $(seq 1 100); do [ -f "$TEST/supervisor.lock/ready" ] && break; command sleep 0.02; done
  [ ! -f "$TEST/slow_controller" ] || command sleep 0.5
  [ ! -f "$TEST/fail_receipt_write" ] || mkdir "$TEST/session-owned.$$"
  if [ -f "$TEST/disable_during_start" ]; then
   nohup sh "$TEST/wrapper.sh" disable > "$TEST/disable.log" 2>&1 < /dev/null &
   echo $! > "$TEST/disabler.pid"
   for i in $(seq 1 100); do [ -f "$TEST/session-cancel" ] && break; command sleep 0.02; done
  fi
 fi
 if [ "$1" = disable ]; then rm -f "$TEST/runtime"; fi
 if [ -f "$TEST/disable_after_ack" ]; then touch "$TEST/disable"; fi
 return 0
}}
'''
local = ROOT / 'work/ksu-check/module-boot-fixture.sh'
local.parent.mkdir(exist_ok=True)
local.write_text(private_paths(preamble) + raw, encoding='utf-8', newline='\n')
shell(f'mkdir -p {BASE}\nchmod 755 {BASE}')
helper = ROOT / 'work/ksu-check/module-state-fixture.sh'
helper.write_text((ROOT/'work/kernel-su/module-state.sh').read_text(encoding='utf-8').replace('/data/adb/flippets-controller', BASE+'/state').replace('/data/adb', BASE+'/adb'), encoding='utf-8', newline='\n')
shell(f'mkdir -p {BASE}/adb\nchmod 700 {BASE}/adb')
adb('push', str(helper), BASE+'/module-state.sh')
shell(f'chmod 644 {BASE}/module-state.sh')
adb('push', str(local), BASE + '/wrapper.sh')
fake_controller = ROOT / 'work/ksu-check/ownership-child.sh'
fake_controller.write_text(private_paths(f'''#!/system/bin/sh
TEST={BASE}
trap 'rm -f "$TEST/runtime" "$TEST/supervisor.lock/pid" "$TEST/supervisor.lock/ready"; rmdir "$TEST/supervisor.lock" 2>/dev/null' EXIT
echo $$ > "$TEST/supervisor.lock/ready"
while [ -f "$TEST/runtime" ] || [ -f "$TEST/hold_child" ]; do sleep 0.02; done
'''), encoding='utf-8', newline='\n')
adb('push', str(fake_controller), BASE + '/flip-pets-control.sh')
results = []


def reset(*, opted=True, ready=True):
    shell(f'rm -f {BASE}/runtime {BASE}/hold_child')
    deadline = time.monotonic() + 5
    while shell(f'test -f {BASE}/supervisor.lock/pid', ok=False).returncode == 0:
        assert time.monotonic() < deadline, 'previous fixture child cleanup'
        time.sleep(.03)
    # All targets are literal children of the dedicated fixture directory.
    shell(f'rm -f {BASE}/session-enabled {BASE}/session-owned {BASE}/disable {BASE}/remove '
          f'{BASE}/unlocked {BASE}/calls {BASE}/sleeps {BASE}/during_wait '
          f'{BASE}/child_failure {BASE}/concurrent_stop {BASE}/no_package {BASE}/disable_after_ack '
          f'{BASE}/session-cancel {BASE}/wrong_uid {BASE}/slow_controller {BASE}/disable_during_start {BASE}/disabler.pid '
          f'{BASE}/stale_boot {BASE}/snapshot_taken {BASE}/release_snapshot {BASE}/fail_receipt_write\n'
          f'mkdir -p {BASE}/appfiles\nrm -f {BASE}/appfiles/controller-stop\necho ruyi > {BASE}/device')
    if opted:
        shell(f'echo none > {BASE}/session-enabled')
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

# Real emulator /proc start times, argv and flock; only UID ownership is stubbed.
reset(opted=False); p = invoke('toggle'); p = invoke('status')
check(p.returncode == 0 and 'Verified owned root supervisor' in p.stdout, 'exact live argv, PID/start time and boot receipt are recognized')
receipt = shell(f'cat {BASE}/session-owned').stdout.strip().split()
check(len(receipt) == 3 and all(receipt[:2]), 'ownership is a process receipt rather than a Boolean marker')
shell(f'echo {receipt[0]} 0 {receipt[2]} > {BASE}/session-owned'); p = invoke('disable')
check(p.returncode != 0 and calls() == ['supervise', 'status'] and exists('runtime') and exists('session-owned'), 'mismatched process start time cannot disable a live process or discard its recovery receipt')
reset(opted=False); invoke('toggle'); shell(f'touch {BASE}/wrong_uid'); p = invoke('disable')
check(p.returncode != 0 and calls() == ['supervise'] and exists('runtime') and exists('session-owned'), 'non-root process identity is never stopped')
reset(opted=False); invoke('toggle'); p = invoke('disable')
check(p.returncode == 0 and not exists('runtime') and not exists('supervisor.lock') and not exists('session-owned'), 'owned disable waits for process cleanup before releasing the transition')
reset(opted=False)
shell(f'mkdir -p {BASE}/supervisor.lock\ntouch {BASE}/runtime\nnohup sh {BASE}/flip-pets-control.sh run extra > {BASE}/child.log 2>&1 < /dev/null &\necho $! > {BASE}/supervisor.lock/pid')
deadline = time.monotonic() + 5
while not exists('supervisor.lock/ready'):
    assert time.monotonic() < deadline, 'lookalike child startup'
    time.sleep(.02)
shell(f'pid=$(cat {BASE}/supervisor.lock/pid); started=$(sed "s/.*) //" /proc/$pid/stat | cut -d " " -f 20); echo "$pid $started $(cat /proc/sys/kernel/random/boot_id)" > {BASE}/session-owned')
p = invoke('disable')
check(p.returncode != 0 and not calls() and exists('runtime'), 'argv with extra arguments is rejected even when the old substring would match')
reset(opted=False)
foreign_pid = shell(f'nohup sleep 60 > {BASE}/foreign.log 2>&1 < /dev/null &\necho $!').stdout.strip()
assert foreign_pid.isdigit()
try:
    shell(f'mkdir -p {BASE}/supervisor.lock\necho {foreign_pid} > {BASE}/supervisor.lock/pid\necho {foreign_pid} > {BASE}/supervisor.lock/ready\necho {foreign_pid} 0 $(cat /proc/sys/kernel/random/boot_id) > {BASE}/session-owned')
    p = invoke('toggle')
    check(p.returncode == 0 and shell(f'kill -0 {foreign_pid}', ok=False).returncode == 0 and shell(f'cat {BASE}/supervisor.lock/pid').stdout.strip() != foreign_pid, 'PID reuse clears receipt-bound stale files without killing the unrelated live process')
finally:
    shell(f'kill {foreign_pid}', ok=False)
reset(opted=False); shell(f'mkdir -p {BASE}/supervisor.lock\necho 999999 > {BASE}/supervisor.lock/pid\necho 999999 > {BASE}/supervisor.lock/ready\necho 999999 1 $(cat /proc/sys/kernel/random/boot_id) > {BASE}/session-owned'); p = invoke('toggle')
check(p.returncode == 0 and calls() == ['supervise'] and exists('session-owned'), 'receipt-bound dead root lock is recovered without killing a process')
reset(opted=False); shell(f'touch {BASE}/runtime\necho owned > {BASE}/session-owned'); p = invoke('toggle')
check(p.returncode != 0 and not calls() and exists('runtime'), 'legacy ownership marker cannot authorize taking over an existing session')
reset(); shell(f'echo enabled > {BASE}/session-enabled'); p = invoke()
check(p.returncode == 0 and not calls() and not exists('session-enabled'), 'legacy opt-in is not silently migrated into consent')
reset(opted=False); shell(f'ln -s {BASE}/device {BASE}/session-owned'); p = invoke('toggle')
check(p.returncode != 0 and not calls() and shell(f'cat {BASE}/device').stdout.strip() == 'ruyi', 'symlinked root control file is refused without touching target')
reset(opted=False); shell(f'chmod 777 {BASE}'); p = invoke('toggle'); shell(f'chmod 755 {BASE}')
check(p.returncode != 0 and not calls(), 'writable-by-others module directory is refused')
reset(); shell(f'chmod 666 {BASE}/session-enabled'); p = invoke('toggle'); shell(f'chmod 600 {BASE}/session-enabled')
check(p.returncode != 0 and not calls(), 'writable-by-others root control file is refused')
reset(opted=False); shell(f'touch {BASE}/slow_controller')
first = subprocess.Popen([ADB, '-s', 'emulator-5554', 'shell', f'sh {BASE}/wrapper.sh toggle'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
deadline = time.monotonic() + 5
while not exists('runtime'):
    assert time.monotonic() < deadline, 'first Action enters startup'
    time.sleep(.02)
second = invoke('toggle'); first.communicate(timeout=15)
check(first.returncode == 0 and second.returncode == 0 and calls() == ['supervise', 'disable'] and not exists('runtime') and not exists('session-enabled'), 'concurrent Actions serialize as Start then Stop; detached child does not inherit flock')
reset(); shell(f'touch {BASE}/slow_controller')
first = subprocess.Popen([ADB, '-s', 'emulator-5554', 'shell', f'sh {BASE}/wrapper.sh boot'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
deadline = time.monotonic() + 5
while not exists('runtime'):
    assert time.monotonic() < deadline, 'boot enters resume'
    time.sleep(.02)
second = invoke('toggle'); first.communicate(timeout=15)
check(first.returncode == 0 and second.returncode == 0 and calls() == ['resume', 'disable'] and not exists('session-enabled'), 'boot resume and Action Stop serialize without a duplicate supervisor')
reset(opted=False); shell(f'touch {BASE}/disable_during_start'); p = invoke('toggle')
deadline = time.monotonic() + 5
while shell(f'test -f {BASE}/disabler.pid && kill -0 "$(cat {BASE}/disabler.pid)"', ok=False).returncode == 0:
    assert time.monotonic() < deadline, 'queued disable completes'
    time.sleep(.03)
check(p.returncode != 0 and exists('session-cancel') and not exists('session-enabled') and not exists('runtime'), 'new disable generation wins over in-progress Start and its queued cleanup completes')
reset(); shell(f'echo none > {BASE}/session-cancel\ntouch {BASE}/stale_boot')
stale_boot = subprocess.Popen([ADB, '-s', 'emulator-5554', 'shell', f'sh {BASE}/wrapper.sh boot'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
deadline = time.monotonic() + 5
while not exists('snapshot_taken'):
    assert time.monotonic() < deadline, 'boot generation snapshot is paused'
    time.sleep(.02)
invoke('disable'); new_start = invoke('toggle'); new_opt_in = shell(f'cat {BASE}/session-enabled').stdout.strip()
shell(f'touch {BASE}/release_snapshot'); stale_boot.communicate(timeout=10)
check(new_start.returncode == 0 and stale_boot.returncode == 0 and exists('runtime') and shell(f'cat {BASE}/session-enabled').stdout.strip() == new_opt_in, 'stale boot preflight cannot delete a newer Action opt-in or session')
reset(opted=False); invoke('toggle'); shell(f'touch {BASE}/hold_child'); p = invoke('disable')
held_receipt = shell(f'cat {BASE}/session-owned').stdout.strip()
check(p.returncode != 0 and not exists('session-enabled') and exists('session-owned') and exists('supervisor.lock/pid'), 'stop timeout retains the receipt of the still-live owned child')
p = invoke('toggle')
check(p.returncode != 0 and shell(f'cat {BASE}/session-owned').stdout.strip() == held_receipt and calls() == ['supervise', 'disable', 'disable'], 'Action retries Stop rather than replacing a timed-out owned child')
shell(f'rm -f {BASE}/hold_child'); p = invoke('disable')
check(p.returncode == 0 and not exists('session-owned'), 'cleanup retry succeeds when the timed-out child is allowed to exit')
reset(opted=False); shell(f'touch {BASE}/fail_receipt_write'); p = invoke('toggle')
check(p.returncode != 0 and not exists('session-enabled') and not exists('runtime') and not exists('supervisor.lock/pid') and calls() == ['supervise', 'disable'], 'receipt write failure after ACK stops only the exactly captured child')
shell(f'rmdir {BASE}/session-owned.[0-9]*', ok=False)
reset(opted=False)
invoke('toggle'); dead_pid = shell(f'cat {BASE}/supervisor.lock/pid').stdout.strip()
shell(f'kill -9 {dead_pid}')
deadline = time.monotonic()+5
while shell(f'kill -0 {dead_pid}', ok=False).returncode == 0:
    assert time.monotonic()<deadline, 'killed fixture child exits'
    time.sleep(.03)
p=invoke('toggle')
check(p.returncode == 0 and not exists('runtime') and not exists('supervisor.lock') and not exists('session-owned') and not exists('session-enabled'), 'Action Stop after process death clears receipt-bound stale runtime before discarding receipt')
p=invoke('toggle')
check(p.returncode == 0 and exists('runtime'), 'explicit Start works after process-death cleanup')
reset(opted=False)
for legacy in ('enabled', 'active', 'lock'):
    shell(f'touch {BASE}/legacy-{legacy}')
    p = invoke('toggle')
    check(p.returncode != 0 and not calls() and exists('legacy-'+legacy), 'Action refuses and preserves legacy shared ' + legacy)
    shell(f'rm -f {BASE}/legacy-{legacy}')
reset(opted=False)
# Module-local markers from an older package are deliberately not durable consent.
# The preceding fixture API maps the canonical state path. Write the old path
# literally through adb to distinguish an update's replaceable module directory.
adb('shell', f'echo enabled > {BASE}/session-enabled')
p = invoke()
check(p.returncode == 0 and not calls() and not exists('session-enabled'), 'legacy module-local opt-in is not migrated into new consent')
adb('shell', f'rm -f {BASE}/session-enabled')
reset(); original_opt_in = shell(f'cat {BASE}/session-enabled').stdout
shell(f'cp {BASE}/wrapper.sh {BASE}/wrapper.next\nmv {BASE}/wrapper.next {BASE}/wrapper.sh')
p = invoke()
check(p.returncode == 0 and calls() == ['resume'] and shell(f'cat {BASE}/session-enabled').stdout == original_opt_in, 'module script replacement preserves durable opt-in outside the module directory')
reset(opted=False); shell(f'echo 99 > {BASE}/state/schema'); p = invoke('toggle')
check(p.returncode != 0 and not calls() and shell(f'cat {BASE}/state/schema').stdout.strip() == '99', 'unknown persistent state schema is neither migrated nor overwritten')
shell(f'echo 1 > {BASE}/state/schema')
reset(opted=False)
report = dict(environment='emulator-5554; UID0, storage availability and controller responses stubbed; no physical root proof',
              wrapperSha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              fixtureSha256=hashlib.sha256(local.read_bytes()).hexdigest(),
              stateHelperSha256=hashlib.sha256((ROOT/'work/kernel-su/module-state.sh').read_bytes()).hexdigest(),
              pathReplacements=replacements, results=results)
out = ROOT / 'work/qa-final/kernel-su-boot-tests.json'
out.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
