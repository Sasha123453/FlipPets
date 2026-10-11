"""Host refusal tests for stale/mislabelled launch reports; never contacts ADB."""
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys
from capture_native_launch_context import validate_context, EXPECTED_BUILD

ROOT = Path(__file__).resolve().parents[2]
binary = 'a' * 64
bounds = dict(left=0, top=0, right=809, bottom=1392)
row = dict(activity='MainActivity', event='manual_export', elapsedRealtimeMs=10000,
           densityDpi=520, displayId=0, displayFlags=16515, displayState=2, rotation=0,
           physicalModeWidth=1208, physicalModeHeight=1392,
           currentWindowBounds=bounds, maximumWindowBounds=bounds)
fixture = dict(schemaVersion=1, device='ruyi', build=EXPECTED_BUILD, sdk=36, apkSha256=binary,
               observations=[row], scope='Own Activity fixture', policyGrantPerformed=False,
               nativeApplyPerformed=False)
rows = []


def case(name, change, expected=False, uptime=11000):
    data = copy.deepcopy(fixture)
    change(data)
    try:
        validate_context(data, binary, uptime)
        allowed = True
    except (ValueError, KeyError, TypeError):
        allowed = False
    rows.append(dict(test=name, ok=allowed == expected))


case('fresh_exact_sha', lambda d: None, True)
case('stale_apk', lambda d: d.update(apkSha256='b' * 64))
case('wrong_device', lambda d: d.update(device='other'))
case('updated_build', lambda d: d.update(build='uninspected'))
case('old_export', lambda d: None, uptime=131000)
case('previous_boot_report', lambda d: None, uptime=500)
case('unknown_root_field', lambda d: d.update(serial='fixture-private'))
case('unknown_row_field', lambda d: d['observations'][0].update(photo='fixture-private'))
case('other_app_activity', lambda d: d['observations'][0].update(activity='OtherActivity'))
case('empty_report', lambda d: d.update(observations=[]))
case('unbounded_report', lambda d: d.update(observations=[copy.deepcopy(row) for _ in range(25)]))
case('bounded_report', lambda d: d.update(observations=[copy.deepcopy(row) for _ in range(24)]), True)
case('not_explicit_export', lambda d: d['observations'][0].update(event='main_focus'))
case('unknown_event', lambda d: d['observations'][0].update(event='unreviewed'))
case('invalid_rotation', lambda d: d['observations'][0].update(rotation=4))
case('boolean_display_id', lambda d: d['observations'][0].update(displayId=True))
case('missing_physical_mode', lambda d: d['observations'][0].pop('physicalModeWidth'))
case('negative_window', lambda d: d['observations'][0].update(currentWindowBounds=dict(left=0,top=0,right=-1,bottom=1392)))
case('missing_max_bounds', lambda d: d['observations'][0].pop('maximumWindowBounds'))
case('policy_mutation_not_capture', lambda d: d.update(policyGrantPerformed=True))
case('native_apply_not_capture', lambda d: d.update(nativeApplyPerformed=True))
script = ROOT / 'work/tests/capture_native_launch_context.py'
for name, flags in [('serial_required', ['--label','fixture']),
                    ('emulator_refused', ['--serial','emulator-5554','--label','fixture']),
                    ('invalid_label', ['--serial','fixture-physical','--label','../private'])]:
    p = subprocess.run([sys.executable, '-X', 'utf8', str(script), '--adb', 'nonexistent-native-test-adb', *flags],
                       capture_output=True, text=True, encoding='utf-8')
    rows.append(dict(test=name, ok=p.returncode != 0 and 'FileNotFoundError' not in p.stderr))
assert len(rows) == 24 and all(r['ok'] for r in rows), rows
report = dict(environment='Host-only stale/identity/privacy/CLI fixtures; no phone or ADB contacted',
              sourceSha256=hashlib.sha256(script.read_bytes()).hexdigest(), tested=len(rows), failed=0, results=rows)
(ROOT / 'work/qa-final/native-context-guards.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print('24 native launch-context guards passed; no phone contacted')
