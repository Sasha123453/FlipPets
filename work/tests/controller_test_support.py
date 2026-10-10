"""Mechanical private-path rebasing for emulator UID0 fixtures, never a root proof."""
from pathlib import Path
import zipfile

BASE = '/data/local/tmp/flip-pets-fixture'
STAT_STUB = '''id() { [ "$1" = "-u" ] && echo 0; }
stat() {
 case "$2" in
 '%u') echo 0 ;;
 '%u:%a') command stat "$@" | sed 's/^2000:/0:/' ;;
 *) command stat "$@" ;;
 esac
}
'''


def root_paths(text):
    for name in ('active', 'enabled', 'supervisor.lock', 'status', 'start-failures.log', 'supervisor.log', 'watch.log', 'watch-ready'):
        text = text.replace('/data/local/tmp/flip-pets-' + name, BASE + '/rootstate/runtime/' + name)
    return text


def prepare_root(r, call, shell):
    with zipfile.ZipFile(r.parent / 'outputs/FlipPets-KernelSU-experimental.zip') as archive:
        helper = archive.read('module-state.sh').decode('utf-8')
    helper = helper.replace('/data/adb/flippets-controller', BASE + '/rootstate').replace('/data/adb', BASE + '/adb')
    local = r / 'qa-final/root-state-fixture.sh'
    local.write_text(helper, encoding='utf-8', newline='\n')
    shell('mkdir -p ' + BASE + '/adb\nchmod 700 ' + BASE + '/adb')
    call('push', str(local), BASE + '/module-state.sh')
    shell('chmod 644 ' + BASE + '/module-state.sh\nchmod 755 ' + BASE)
