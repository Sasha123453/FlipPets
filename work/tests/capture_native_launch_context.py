"""Read only an explicitly exported, fresh own-Activity report on the exact MIX Flip EEA profile."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import uuid
from capture_native_capabilities import validate_identity, validate_apk_path, EXPECTED_BUILD

ROOT = Path(__file__).resolve().parents[2]
REPORT_KEYS = {'schemaVersion', 'device', 'build', 'sdk', 'apkSha256', 'observations', 'scope',
               'policyGrantPerformed', 'nativeApplyPerformed'}
ROW_KEYS = {'activity', 'event', 'elapsedRealtimeMs', 'densityDpi', 'focused', 'nativeRoutingEnabled',
            'settingsBypass', 'awake', 'locked', 'nativePolicyDeclarations', 'displayId', 'displayFlags',
            'displayState', 'displayValid', 'rotation', 'physicalModeWidth', 'physicalModeHeight',
            'currentWindowBounds', 'maximumWindowBounds', 'currentWindowInsets', 'maximumWindowInsets',
            'decorInsets', 'routeMatches'}


def validate_context(data, binary, uptime_ms):
    if set(data) != REPORT_KEYS or data['schemaVersion'] != 1:
        raise ValueError('Unknown report schema; do not publish unreviewed fields')
    if data['device'] != 'ruyi' or data['build'] != EXPECTED_BUILD or data['apkSha256'] != binary:
        raise ValueError('Report identity or APK SHA is stale')
    if data['policyGrantPerformed'] is not False or data['nativeApplyPerformed'] is not False:
        raise ValueError('Report is outside read-only launch-context scope')
    rows = data['observations']
    if not isinstance(rows, list) or not 1 <= len(rows) <= 24:
        raise ValueError('Missing or unbounded observations')
    for row in rows:
        if set(row) - ROW_KEYS or row.get('activity') not in ('MainActivity', 'CoverAppsActivity'):
            raise ValueError('Unexpected fields or other Activity data')
        if row.get('event') not in ('main_route_check', 'main_focus', 'cards_focus', 'cards_configuration', 'manual_export'):
            raise ValueError('Unexpected observation event')
        for key in ('elapsedRealtimeMs', 'densityDpi', 'displayId', 'displayFlags', 'displayState',
                    'rotation', 'physicalModeWidth', 'physicalModeHeight'):
            if type(row.get(key)) is not int or row[key] < 0:
                raise ValueError('Missing or invalid measured display fields')
        if row['rotation'] not in range(4):
            raise ValueError('Invalid rotation')
        for key in ('currentWindowBounds', 'maximumWindowBounds'):
            bounds = row.get(key)
            if bounds is None and key == 'maximumWindowBounds' and data['sdk'] == 29:
                continue
            if not isinstance(bounds, dict) or set(bounds) != {'left', 'top', 'right', 'bottom'}:
                raise ValueError('Missing window bounds')
            if any(type(v) is not int for v in bounds.values()) or bounds['right'] <= bounds['left'] or bounds['bottom'] <= bounds['top']:
                raise ValueError('Invalid window bounds')
    age = uptime_ms - rows[-1]['elapsedRealtimeMs']
    if rows[-1]['event'] != 'manual_export' or not 0 <= age <= 120000:
        raise ValueError('Export is stale or belongs to a previous boot; export again within two minutes')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--adb', default='C:/platform-tools/adb.exe')
    parser.add_argument('--label', required=True, help='Human observation label; not an automatic fold/full-screen assertion')
    args = parser.parse_args()
    validate_identity(args.serial, 'ruyi', EXPECTED_BUILD, '0')
    if not re.fullmatch('[a-z0-9][a-z0-9-]{0,47}', args.label):
        raise ValueError('Use a simple private capture label')

    def adb(*parts):
        try:
            p = subprocess.run([args.adb, '-s', args.serial, *parts], capture_output=True,
                               text=True, encoding='utf-8', timeout=40)
        except subprocess.TimeoutExpired:
            raise RuntimeError('Read-only ADB timed out') from None
        if p.returncode:
            raise RuntimeError('Read-only ADB failed; inspect the phone privately')
        return p.stdout.strip()

    validate_identity(args.serial, adb('shell', 'getprop ro.product.device'),
                      adb('shell', 'getprop ro.build.version.incremental'), adb('shell', 'getprop ro.kernel.qemu'))
    paths = adb('shell', 'pm path org.flippets.app').splitlines()
    if len(paths) != 1 or not paths[0].startswith('package:/'):
        raise ValueError('Expected one installed Flip Pets APK')
    path = paths[0].removeprefix('package:')
    validate_apk_path(path)
    binary = hashlib.sha256((ROOT / 'outputs/FlipPets.apk').read_bytes()).hexdigest()
    if adb('shell', 'sha256sum ' + path).split()[0] != binary:
        raise ValueError('Installed APK does not match the current candidate')
    raw = adb('shell', 'cat /sdcard/Android/data/org.flippets.app/files/native-launch-context.json')
    if len(raw) > 131072:
        raise ValueError('Oversized report')
    data = json.loads(raw)
    uptime_ms = int(float(adb('shell', 'cat /proc/uptime').split()[0]) * 1000)
    validate_context(data, binary, uptime_ms)
    if adb('shell', 'sha256sum ' + path).split()[0] != binary:
        raise ValueError('Installed APK changed during capture')
    destination = ROOT / 'work/phone-qa' / ('native-context-' + uuid.uuid4().hex)
    destination.mkdir(parents=True)
    (destination / (args.label + '.json')).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print('Fresh current-SHA own-Activity report saved under ignored work/phone-qa. Label is not a physical acceptance result.')


if __name__ == '__main__':
    main()
