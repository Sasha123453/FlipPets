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
    allowed = {'module.prop', 'customize.sh', 'action.sh', 'boot-completed.sh', 'uninstall.sh', 'module-control.sh'}
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
