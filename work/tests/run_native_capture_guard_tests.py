"""Host-only refusal tests for the future read-only native capture; never contacts ADB."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from capture_native_capabilities import validate_identity, validate_apk_path, EXPECTED_BUILD

ROOT = Path(__file__).resolve().parents[2]
rows = []
cases = [
    ('verified_profile', ('fixture-physical', 'ruyi', EXPECTED_BUILD, ''), True),
    ('explicit_zero_qemu', ('fixture-physical', 'ruyi', EXPECTED_BUILD, '0'), True),
    ('missing_serial', ('', 'ruyi', EXPECTED_BUILD, ''), False),
    ('emulator_serial', ('emulator-5554', 'ruyi', EXPECTED_BUILD, ''), False),
    ('malformed_serial', ('fixture;command', 'ruyi', EXPECTED_BUILD, ''), False),
    ('option_serial', ('-fixture', 'ruyi', EXPECTED_BUILD, ''), False),
    ('wrong_device', ('fixture-physical', 'bixi', EXPECTED_BUILD, ''), False),
    ('global_build', ('fixture-physical', 'ruyi', 'OS3.0.303.0.WNIMIXM', ''), False),
    ('unknown_build', ('fixture-physical', 'ruyi', 'unknown', ''), False),
    ('emulator_property', ('fixture-physical', 'ruyi', EXPECTED_BUILD, '1'), False),
    ('unknown_qemu_property', ('fixture-physical', 'ruyi', EXPECTED_BUILD, 'unknown'), False),
]
for name, args, expected in cases:
    try:
        validate_identity(*args)
        allowed = True
    except ValueError:
        allowed = False
    rows.append(dict(test=name, ok=allowed == expected))
for name, path, expected in [
    ('system_apk_path', '/product/priv-app/FlipHome/FlipHome.apk', True),
    ('updated_apk_path', '/data/app/~~Random_token==/com.miui.aod-token_xyz==/base.apk', True),
    ('path_traversal', '/data/app/../base.apk', False),
    ('path_semicolon', '/data/app/bad;command/base.apk', False),
    ('path_space', '/data/app/bad command/base.apk', False),
    ('path_substitution', '/data/app/$(command)/base.apk', False),
    ('path_relative', 'base.apk', False),
]:
    try:
        validate_apk_path(path)
        allowed = True
    except ValueError:
        allowed = False
    rows.append(dict(test=name, ok=allowed == expected))
script = ROOT / 'work/tests/capture_native_capabilities.py'
# A nonexistent adb would raise FileNotFoundError if either invalid CLI reached it.
for name, flags in [('cli_serial_required', []), ('cli_emulator_refused', ['--serial', 'emulator-5554'])]:
    proc = subprocess.run([sys.executable, '-X', 'utf8', str(script), '--adb', 'nonexistent-native-test-adb', *flags],
                          capture_output=True, text=True, encoding='utf-8')
    rows.append(dict(test=name, ok=proc.returncode != 0 and 'FileNotFoundError' not in proc.stderr))
assert len(rows) == 20 and all(row['ok'] for row in rows), rows
report = dict(environment='Host-only pure identity/CLI guard fixtures; no ADB or phone operations',
              sourceSha256=hashlib.sha256(script.read_bytes()).hexdigest(), tested=len(rows), failed=0, results=rows)
target = ROOT / 'work/qa-final/native-capture-guards.json'
target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print('20 native capture guard checks passed; no phone targeted')
