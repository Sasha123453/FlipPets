"""Build the optional, unverified-on-phone KernelSU controller. No installation or mounts."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'work/kernel-su'
CONTROLLER = ROOT / 'outputs/flip-pets-control.sh'
EMBEDDED = ROOT / 'work/app/assets/controller.sh'
UID_CHECK = '[ "$(id -u)" = "2000" ] || fail "This rootless controller requires ADB shell UID 2000"'


def main():
    canonical = CONTROLLER.read_bytes()
    assert canonical == EMBEDDED.read_bytes(), 'Embedded controller diverges'
    script = canonical.decode('utf8')
    assert script.count(UID_CHECK) == 1, 'Unexpected controller verify contract'
    script = script.replace(UID_CHECK, '[ "$(id -u)" = "0" ] || fail "This KernelSU controller requires root UID 0"')
    script = script.replace('# Temporary presentation mode, stock Android/Xiaomi commands only. No partition writes.', '# Generated KernelSU variant: same fold/lock/sleep policy; UID 0 instead of shell. No partition writes.')
    # Policy comes from the canonical controller; only identity, private storage
    # and module cancellation inputs differ. No root writes to shell runtime.
    bootstrap = '''[ "$(id -u)" = 0 ] || { echo "Root required" >&2; exit 1; }
FP_MODULE_DIR=${0%/*}
for path in "$FP_MODULE_DIR" "$FP_MODULE_DIR/module-state.sh"; do
  [ ! -L "$path" ] && [ "$(stat -c '%u' "$path")" = 0 ] || exit 1
  mode=$(stat -c '%a' "$path")
  case "$mode" in ''|*[!0-7]*|*[2367][0-7]|*[2367]) exit 1 ;; esac
done
. "$FP_MODULE_DIR/module-state.sh"
FP_CANCEL_PATH=$STATE/session-cancel
FP_EXPECTED_GENERATION=${FP_EXPECTED_GENERATION:-$(cat "$FP_CANCEL_PATH" 2>/dev/null || echo none)}
export FP_MODULE_DIR FP_CANCEL_PATH FP_EXPECTED_GENERATION
'''
    script = script.replace('PKG=org.flippets.app', bootstrap + 'PKG=org.flippets.app', 1)
    for name in ('active', 'enabled', 'supervisor.lock', 'status', 'start-failures.log', 'supervisor.log', 'watch.log', 'watch-ready'):
        old = '/data/local/tmp/flip-pets-' + name
        assert old in script, old
        script = script.replace(old, '$STATE/runtime/' + name)
    # Also protect direct invocation of the generated controller. Old released
    # shell/root controllers do not know about the new shared flock.
    script = script.replace('  flock -n 8 8>&8 || fail "Another controller backend is active; Stop it first"', '''  flock -n 8 8>&8 || fail "Another controller backend is active; Stop it first"
  for legacy in /data/local/tmp/flip-pets-enabled /data/local/tmp/flip-pets-active /data/local/tmp/flip-pets-supervisor.lock; do
    [ ! -e "$legacy" ] && [ ! -L "$legacy" ] || fail "Stop the legacy shared-runtime controller before enabling root"
  done
  # Old module logs alone can obstruct the next UID2000 invocation. With the
  # lifetime lease held and no legacy session markers, unlink only these fixed
  # regular root-owned diagnostic leaves. Never follow a link or reset a display.
  for legacy in /data/local/tmp/flip-pets-status /data/local/tmp/flip-pets-start-failures.log /data/local/tmp/flip-pets-supervisor.log /data/local/tmp/flip-pets-watch.log; do
    if [ -e "$legacy" ] || [ -L "$legacy" ]; then
      [ ! -L "$legacy" ] && [ -f "$legacy" ] || fail "Unsafe legacy diagnostic path"
      if [ "$(stat -c '%u' "$legacy")" = 0 ]; then rm -f "$legacy" || fail "Cannot remove obsolete root diagnostic"; fi
    fi
  done''')
    allowed = {'module.prop', 'customize.sh', 'action.sh', 'boot-completed.sh', 'uninstall.sh', 'module-control.sh', 'module-state.sh'}
    files = {p.name: p.read_bytes().replace(b'\r\n', b'\n') for p in SOURCE.iterdir() if p.name in allowed}
    assert set(files) == allowed
    files['flip-pets-control.sh'] = script.encode('utf8').replace(b'\r\n', b'\n')
    files['skip_mount'] = b''
    proof = dict(scope='Experimental KernelSU script module; not installed or verified on physical MIX Flip',
                 canonicalControllerSha256=hashlib.sha256(canonical).hexdigest(),
                 apkSha256=hashlib.sha256((ROOT/'outputs/FlipPets.apk').read_bytes()).hexdigest(),
                 files={name: hashlib.sha256(data).hexdigest() for name, data in files.items()})
    files['build-evidence.json'] = json.dumps(proof, indent=2).encode('utf8')
    output = ROOT / 'outputs/FlipPets-KernelSU-experimental.zip'
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o100755 if name.endswith('.sh') else 0o100644) << 16
            z.writestr(info, data)
    print(json.dumps(dict(zip=str(output), sha256=hashlib.sha256(output.read_bytes()).hexdigest(), **proof), indent=2))


if __name__ == '__main__':
    main()
