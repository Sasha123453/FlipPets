"""Future read-only MIX Flip capture. Explicit serial and exact EEA build required; no grants/Apply/root."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_BUILD = 'OS3.0.303.0.WNIEUXM'


def validate_identity(serial, device, build, qemu):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', serial) or serial.startswith('emulator-'):
        raise ValueError('Explicit physical serial required')
    if device != 'ruyi' or build != EXPECTED_BUILD or qemu not in ('', '0'):
        raise ValueError('Only the explicitly verified MIX Flip EEA build is supported')


def validate_apk_path(path):
    if not re.fullmatch(r'/[A-Za-z0-9_./+=~-]+\.apk', path) or any(x in ('.', '..') for x in path.split('/')):
        raise ValueError('Unsafe native APK path')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--adb', default='C:/platform-tools/adb.exe')
    args = parser.parse_args()
    # Reject malformed targets before any ADB call; identity checks precede pulls.
    validate_identity(args.serial, 'ruyi', EXPECTED_BUILD, '0')

    def adb(*parts):
        try:
            result = subprocess.run([args.adb, '-s', args.serial, *parts], check=False,
                                    capture_output=True, text=True, encoding='utf-8', timeout=60)
        except subprocess.TimeoutExpired:
            raise RuntimeError('Read-only ADB operation timed out; no device identifiers printed') from None
        if result.returncode:
            raise RuntimeError('Read-only ADB operation failed; inspect the connected device privately')
        return result.stdout.strip()

    device = adb('shell', 'getprop ro.product.device')
    build = adb('shell', 'getprop ro.build.version.incremental')
    validate_identity(args.serial, device, build, adb('shell', 'getprop ro.kernel.qemu'))
    destination = ROOT / 'work/phone-qa' / ('native-capabilities-' + uuid.uuid4().hex)
    destination.mkdir(parents=True)
    rows = []
    for package in ('com.miui.fliphome', 'com.miui.aod', 'com.android.systemui'):
        paths = adb('shell', 'pm path ' + package).splitlines()
        if not paths or any(not row.startswith('package:/') for row in paths):
            raise RuntimeError('Required native package missing: ' + package)
        files = []
        for index, row in enumerate(paths):
            path = row.removeprefix('package:')
            validate_apk_path(path)
            expected = adb('shell', 'sha256sum ' + path).split()[0]
            if not re.fullmatch('[0-9a-f]{64}', expected):
                raise RuntimeError('Invalid source hash')
            local = destination / f'{package}-{index}.apk'
            adb('pull', path, str(local))
            if hashlib.sha256(local.read_bytes()).hexdigest() != expected:
                raise RuntimeError('Native APK changed during read-only capture')
            files.append(dict(file=local.name, sha256=expected, bytes=local.stat().st_size))
        rows.append(dict(package=package, files=files))
    # The policy implementation is split across these JARs on the exact EEA build.
    for name in ('miui-services.jar', 'miui-appcompat.jar', 'miui-appcompat.appcontinuity.jar'):
        framework = '/system_ext/framework/' + name
        expected = adb('shell', 'sha256sum ' + framework).split()[0]
        if not re.fullmatch('[0-9a-f]{64}', expected):
            raise RuntimeError('Framework hash unavailable; do not assume Global policy reader matches')
        local = destination / name
        adb('pull', framework, str(local))
        if hashlib.sha256(local.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Framework changed during capture')
        rows.append(dict(framework=name, sha256=expected, bytes=local.stat().st_size))
    report = dict(schemaVersion=1, device=device, build=build, artifacts=rows,
                  scope='Read-only package/framework identities; not policy, admission, playback or restore proof',
                  policyGrantPerformed=False, nativeApplyPerformed=False)
    (destination / 'identities.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Read-only artifacts saved under ignored work/phone-qa; inspect before publishing sanitized evidence.')


if __name__ == '__main__':
    main()
