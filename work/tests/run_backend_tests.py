"""Real emulator flock/children; stubbed root identity and HyperOS commands."""
from pathlib import Path
import hashlib
import json
import subprocess
import time
import zipfile
from controller_test_support import STAT_STUB

ROOT = Path(__file__).resolve().parents[2]
BASE = '/data/local/tmp/flip-pets-backend-fixture'
ADB = 'C:/platform-tools/adb.exe'


def adb(*args, ok=True):
    p = subprocess.run([ADB, '-s', 'emulator-5554', *args], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=25)
    if ok and p.returncode:
        raise RuntimeError(p.stdout + p.stderr)
    return p


def shell(code, ok=True):
    return adb('shell', 'umask 077\n' + code, ok=ok)


def wait(test, label):
    deadline = time.monotonic() + 10
    while not test():
        assert time.monotonic() < deadline, label
        time.sleep(.05)


def exists(path):
    return shell('test -e ' + path, ok=False).returncode == 0


assert shell('getprop ro.kernel.qemu').stdout.strip() == '1'
shell(f'mkdir -p {BASE}/root {BASE}/shell {BASE}/adb {BASE}/appfiles\nchmod 755 {BASE} {BASE}/root {BASE}/shell\nchmod 700 {BASE}/adb')
replacements = {'/sdcard/Android/data/org.flippets.app/files/': BASE + '/appfiles/',
                '/data/local/tmp/flip-pets-backend.lock': BASE + '/backend.lock'}
for name in ('enabled', 'active', 'supervisor.lock', 'status', 'start-failures.log', 'supervisor.log', 'watch.log', 'watch-ready'):
    replacements['/data/local/tmp/flip-pets-' + name] = BASE + '/shell-' + name


def rebase(text):
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def push(text, name):
    path = ROOT / 'work/ksu-check' / ('backend-' + name.replace('/', '-'))
    path.write_text(text, encoding='utf-8', newline='\n')
    adb('push', str(path), BASE + '/' + name)
    shell('chmod 644 ' + BASE + '/' + name)
    return hashlib.sha256(path.read_bytes()).hexdigest()


canonical = (ROOT / 'outputs/flip-pets-control.sh').read_bytes()
with zipfile.ZipFile(ROOT / 'outputs/FlipPets-KernelSU-experimental.zip') as z:
    generated = z.read('flip-pets-control.sh')
    helper = z.read('module-state.sh').decode('utf-8')
push(helper.replace('/data/adb/flippets-controller', BASE + '/state').replace('/data/adb', BASE + '/adb'), 'root/module-state.sh')
hashes = {}
for backend, source in (('root', generated), ('shell', canonical)):
    hashes[backend] = push(rebase(source.decode('utf-8')), backend + '/control.sh')
    fixture = (ROOT / 'work/tests/controller-fixture.sh').read_text(encoding='utf-8')
    fixture = fixture.replace('/data/local/tmp/flip-pets-fixture', BASE + '/' + backend)
    fixture = fixture.replace('nohup() { :; }', 'sleep() { command sleep 0.1; }')
    fixture = f'''command() {{
 if [ "$1:$2" = '-v:nohup' ] && [ -f '{BASE}/{backend}/missing_nohup' ]; then return 1; fi
 builtin command "$@"
}}
nohup() {{ [ ! -f '{BASE}/{backend}/failed_watcher' ] || return 1; exec /system/bin/nohup "$@" 8>&8; }}
''' + fixture
    if backend == 'root':
        stub = STAT_STUB
        stub = stub.replace("'%u') echo 0", f"'%u') case \"$3\" in {BASE}/shell-*) if [ -f {BASE}/root/fake_root_logs ]; then echo 0; else command stat \"$@\"; fi ;; *) echo 0 ;; esac")
        fixture = stub + fixture
    push(rebase(fixture), backend + '/flip-pets-control.sh')
    adb('push', str(ROOT / 'work/research/ruyi-display_layout_configuration.xml'), BASE + '/' + backend + '/layout')
    shell(f'echo ruyi > {BASE}/{backend}/device\necho 3 > {BASE}/{backend}/state\necho 3 > {BASE}/{backend}/base\necho Awake > {BASE}/{backend}/wake\necho false > {BASE}/{backend}/locked')


def invoke(backend, action, ok=True):
    return shell(f'sh {BASE}/{backend}/flip-pets-control.sh {action}', ok=ok)


def pid_path(backend):
    return BASE + ('/state/runtime/supervisor.lock/pid' if backend == 'root' else '/shell-supervisor.lock/pid')


def stopped(backend):
    watch = BASE + ('/state/runtime/watch-ready' if backend == 'root' else '/shell-watch-ready')
    return not exists(pid_path(backend)) and not exists(watch)


def stop(backend):
    invoke(backend, 'disable', ok=False)
    wait(lambda: stopped(backend), backend + ' cleanup')


results = []


def check(value, label):
    assert value, label
    results.append(dict(case=label, ok=True))


try:
    for backend in ('root', 'shell'):
        stop(backend)
    shell(f'rm -f {BASE}/appfiles/controller-stop {BASE}/root/disable {BASE}/root/remove')
    for first, second in (('root', 'shell'), ('shell', 'root')):
        invoke(first, 'supervise')
        original = shell('cat ' + pid_path(first)).stdout.strip()
        refused = invoke(second, 'supervise', ok=False)
        check(refused.returncode != 0 and shell('cat ' + pid_path(first)).stdout.strip() == original and stopped(second),
              first + ' lifetime flock prevents concurrent ' + second + ' startup')
        stop(first)
        invoke(second, 'supervise')
        check(not stopped(second), first + ' cleanup releases flock for ' + second)
        stop(second)
    for backend, other in (('root', 'shell'), ('shell', 'root')):
        for failure in ('missing_nohup', 'failed_watcher'):
            shell(f'touch {BASE}/{backend}/{failure}')
            refused = invoke(backend, 'start', ok=False)
            check(refused.returncode != 0 and shell(f'cat {BASE}/{backend}/state').stdout.strip() == '3', backend + ' manual Start rolls back on ' + failure)
            shell(f'rm -f {BASE}/{backend}/{failure}')
            stop(backend)
        invoke(backend, 'start')
        refused = invoke(other, 'supervise', ok=False)
        check(refused.returncode != 0 and not stopped(backend), backend + ' manual watcher inherits and holds the lifetime lease')
        stop(backend)
        invoke(other, 'supervise')
        check(not stopped(other), backend + ' manual watcher releases the lifetime lease on Stop')
        stop(other)
        invoke(backend, 'start')
        watch_path = BASE + ('/state/runtime/watch-ready' if backend == 'root' else '/shell-watch-ready')
        watcher = shell('cat ' + watch_path).stdout.strip()
        shell('kill -9 ' + watcher)
        wait(lambda: shell('kill -0 ' + watcher, ok=False).returncode != 0, 'manual watcher death')
        refused = invoke(backend, 'start', ok=False)
        check(refused.returncode != 0 and shell(f'cat {BASE}/{backend}/state').stdout.strip() == '3', backend + ' stale manual request after watcher death restores stock instead of false success')
        shell('rm -f ' + watch_path)
        invoke(backend, 'start'); stop(backend)
        check(True, backend + ' manual Start recovers after watcher death cleanup')
    shell(f'echo shell-diagnostics > {BASE}/shell-status')
    invoke('root', 'supervise'); stop('root')
    check(shell(f'cat {BASE}/shell-status').stdout.strip() == 'shell-diagnostics', 'legacy cleanup preserves shell-owned diagnostics')
    shell(f'touch {BASE}/root/fake_root_logs')
    invoke('root', 'supervise'); stop('root')
    check(not exists(BASE+'/shell-status'), 'legacy cleanup unlinks fixed obsolete root-owned diagnostics')
    shell(f'rm -f {BASE}/root/fake_root_logs\necho untouched > {BASE}/diagnostic-target\nln -s {BASE}/diagnostic-target {BASE}/shell-status')
    refused = invoke('root', 'supervise', ok=False)
    check(refused.returncode != 0 and shell(f'cat {BASE}/diagnostic-target').stdout.strip() == 'untouched' and shell(f'cat {BASE}/root/state').stdout.strip() == '3', 'legacy diagnostic symlink is refused without target writes or display reset')
    shell(f'rm -f {BASE}/shell-status')
    for flag in ('disable', 'remove'):
        invoke('root', 'supervise')
        shell(f'touch {BASE}/root/{flag}')
        wait(lambda: stopped('root'), flag + ' observed by live controller')
        check(shell(f'cat {BASE}/root/state').stdout.strip() == '3', flag + ' after startup stops root and restores stock request')
        shell(f'rm -f {BASE}/root/{flag}')
    invoke('root', 'supervise')
    shell(f'cat /proc/sys/kernel/random/uuid > {BASE}/state/session-cancel')
    wait(lambda: stopped('root'), 'generation cancellation')
    check(True, 'new cancellation generation stops an already acknowledged root session')
    for name in ('enabled', 'active', 'supervisor.lock'):
        path = BASE + '/shell-' + name
        shell(('mkdir ' if name.endswith('lock') else 'touch ') + path)
        refused = invoke('root', 'supervise', ok=False)
        check(refused.returncode != 0 and exists(path) and stopped('root'), 'direct root Start preserves/refuses legacy ' + name)
        shell(('rmdir ' if name.endswith('lock') else 'rm -f ') + path)
    shell(f'echo 99 > {BASE}/state/schema')
    refused = invoke('root', 'status', ok=False)
    check(refused.returncode != 0 and shell(f'cat {BASE}/state/schema').stdout.strip() == '99', 'unknown durable schema fails closed without rewriting it')
    shell(f'echo 1 > {BASE}/state/schema\nchmod 755 {BASE}/state')
    refused = invoke('root', 'status', ok=False)
    check(refused.returncode != 0, 'root persistent directory requires mode 0700')
    shell(f'chmod 700 {BASE}/state')
    check(shell(f'stat -c %a {BASE}/backend.lock').stdout.strip() == '644', 'shared lease remains read-only for the other UID and survives Stop')
    check(not any(exists(BASE + '/shell-' + name) for name in ('enabled', 'active', 'supervisor.lock')),
          'root teardown leaves no shell runtime markers')
finally:
    shell(f'echo 1 > {BASE}/state/schema\nchmod 700 {BASE}/state\nrm -f {BASE}/root/disable {BASE}/root/remove', ok=False)
    for backend in ('root', 'shell'):
        stop(backend)
record = dict(environment='emulator-5554; real flock and child processes, UID0 and HyperOS command responses stubbed; no physical root/SELinux proof',
              canonicalControllerSha256=hashlib.sha256(canonical).hexdigest(), generatedControllerSha256=hashlib.sha256(generated).hexdigest(),
              adaptedControllerSha256=hashes, pathReplacements=replacements, results=results)
(ROOT / 'work/qa-final/backend-tests.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
