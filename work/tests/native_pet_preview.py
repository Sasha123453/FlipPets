"""Guarded EEA Charlie preview only. No Apply, settings write, root, wake or permissions grant."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import shlex
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET
from capture_native_capabilities import validate_identity, EXPECTED_BUILD
from prepare_native_template import ROOT, STAGING_ROOT, verified_resources, validate_template, sha

KEYS = ('current_tiny_keyguard_info', 'all_tiny_keyguard_info')
PACKAGE_HASHES = {'com.miui.aod': '31c6dd09226e24f13f519822425a0b3f2a6d4fb8d6bf565bbd3a0568ee494d5d',
                  'com.android.systemui': 'bbb73370372d95707caa07bc00a6b2674afc5f433e5b074c4f8d6837b74ba757'}
COMPONENT = 'com.miui.aod/com.miui.tinykeyguard.editor.edit.EditActivity'
NATIVE_ROOT = '/data/system/theme_magic/users/0/wallpaper/'
WALLPAPER_METADATA = NATIVE_ROOT + 'data/small_lock.xml'
RESTORE_PROVIDER = 'miui.keyguard.editor.templatefileprovider'
RESTORE_PERMISSION = 'miui.keyguard.editor.WRITE_EDITOR_FILE'


def native_path(value):
    if not isinstance(value, str) or not re.fullmatch(r'/[A-Za-z0-9_./+=~-]+', value):
        raise ValueError('Unknown native resource path')
    if any(x in ('.', '..') for x in value.split('/')):
        raise ValueError('Unsafe native path')
    if not value.startswith((NATIVE_ROOT, '/product/media/wallpaper/', '/system_ext/media/wallpaper/')):
        raise ValueError('Path outside the inspected native resource roots')
    return value


class Phone:
    def __init__(self, serial, adb):
        validate_identity(serial, 'ruyi', EXPECTED_BUILD, '0')
        self.serial, self.adb = serial, adb
        validate_identity(serial, self.text('getprop ro.product.device'),
                          self.text('getprop ro.build.version.incremental'), self.text('getprop ro.kernel.qemu'))
        if self.text('am get-current-user') != '0':
            raise ValueError('Only the inspected primary-user profile is supported')
        for package, expected in PACKAGE_HASHES.items():
            rows = self.text('pm path ' + package).splitlines()
            if len(rows) != 1 or not rows[0].startswith('package:/'):
                raise ValueError('Unexpected native package layout')
            path = rows[0][8:]
            from capture_native_capabilities import validate_apk_path
            validate_apk_path(path)
            if self.text('sha256sum ' + shlex.quote(path)).split()[0] != expected:
                raise ValueError('Native APK differs from the inspected playback profile')

    def call(self, *parts, required=True):
        result = subprocess.run([self.adb, '-s', self.serial, *map(str, parts)],
                                capture_output=True, timeout=60)
        if required and result.returncode:
            raise RuntimeError('Explicit phone operation failed; inspect private diagnostics')
        return result

    def text(self, command):
        return self.call('shell', command).stdout.decode('utf-8').strip()

    def state(self):
        result = {}
        for key in KEYS:
            raw = self.call('exec-out', 'settings --user 0 get secure ' + key).stdout
            if not raw or len(raw) > 2 * 1024 * 1024:
                raise ValueError('Invalid/big native state; no preview started')
            json.loads(raw)  # Accept JSON null but do not invent restoration semantics for it.
            result[key] = raw
        return result


def stable_state(phone):
    first, second = phone.state(), phone.state()
    if first != second:
        raise ValueError('Native selection/history changed while reading; retry after it settles')
    return first


def outer_wallpaper_paths(raw):
    """Parse only the inspected outer target's bounded, absolute resource list."""
    if not raw or len(raw) > 65536 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('Invalid outer-wallpaper metadata')
    try:
        node = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError('Invalid outer-wallpaper XML') from exc
    if node.tag != 'wallpaper_data' or node.get('which') != '8' or len(node):
        raise ValueError('Not the inspected isolated outer-wallpaper target')
    size = node.get('pathSize', '')
    if not size.isdecimal() or not 1 <= int(size) <= 16:
        raise ValueError('Unbounded or empty outer-wallpaper resource list')
    names = {key for key in node.attrib if key.startswith('path') and key != 'pathSize'}
    if names != {'path' + str(i) for i in range(int(size))}:
        raise ValueError('Incomplete outer-wallpaper resource list')
    return [native_path(node.attrib['path' + str(i)]) for i in range(int(size))]


def provider_query_status(result):
    """`content` can exit zero on SecurityException; never infer access from exit code."""
    output = result.stdout + result.stderr
    if (b'java.lang.SecurityException: Permission Denial: opening provider ' in output
            and b'com.miui.keyguard.editor.data.template.TemplateFileProvider' in output
            and b'uid=2000' in output and RESTORE_PERMISSION.encode() in output):
        return 'denied-by-permission'
    if result.returncode == 0 and output.strip() == b'No result found.':
        return 'reachable-query-only-writing-unproven'
    return 'unverified-transport-or-provider-result'


def inspect(phone):
    """Read-only private dependency inventory. `test -w` is not an actual restore test."""
    snapshot = stable_state(phone)
    metadata_before = phone.call('exec-out', 'cat ' + shlex.quote(WALLPAPER_METADATA)).stdout
    wallpaper_paths = outer_wallpaper_paths(metadata_before)
    session = ROOT / 'work/phone-qa' / ('pet-inventory-' + uuid.uuid4().hex)
    session.mkdir()
    paths, unknown = set(), 0
    def walk(value):
        nonlocal unknown
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str) and value.startswith('/'):
            try:
                paths.add(native_path(value))
            except ValueError:
                unknown += 1
    for key, data in snapshot.items():
        (session / (key + '.json')).write_bytes(data)
        walk(json.loads(data))
    paths.update(wallpaper_paths)
    paths.add(WALLPAPER_METADATA)
    if len(paths) > 256:
        raise ValueError('Unbounded dependency inventory refused')
    rows = []
    for index, path in enumerate(sorted(paths)):
        quoted = shlex.quote(path)
        metadata = phone.call('shell', 'ls -ldnZ ' + quoted, required=False)
        readable = phone.call('shell', 'test -r ' + quoted, required=False).returncode == 0
        writable = phone.call('shell', 'test -w ' + quoted, required=False).returncode == 0
        row = dict(path=path, readableByShell=readable, writableByShell=writable,
                   metadata=metadata.stdout.decode('utf-8', errors='replace').strip())
        if readable:
            size = phone.text('stat -c %s ' + quoted)
            if size.isdecimal() and int(size) <= 64 * 1024 * 1024:
                result = phone.call('shell', 'sha256sum ' + quoted, required=False)
                tokens = result.stdout.decode('utf-8').split()
                if tokens and re.fullmatch('[0-9a-f]{64}', tokens[0]):
                    local = session / f'resource-{index:03}.bin'
                    # adbd's file-sync domain may deny a pull which shell can read.
                    read_result = phone.call('exec-out', 'cat ' + quoted, required=False)
                    raw = read_result.stdout
                    if read_result.returncode:
                        row['backupReadDenied'] = True
                        rows.append(row)
                        continue
                    if len(raw) != int(size) or sha(raw) != tokens[0]:
                        raise ValueError('Native dependency changed during inventory')
                    local.write_bytes(raw)
                    row.update(backupFile=local.name, sha256=tokens[0], bytes=int(size))
        rows.append(row)
    if (stable_state(phone) != snapshot or phone.call('exec-out',
            'cat ' + shlex.quote(WALLPAPER_METADATA)).stdout != metadata_before):
        raise ValueError('Native choice/wallpaper changed during inventory; snapshot not accepted')
    for row in rows:
        if 'backupFile' in row:
            current_hash = phone.text('sha256sum ' + shlex.quote(row['path'])).split()[0]
            if current_hash != row['sha256']:
                raise ValueError('A native resource changed during inventory; snapshot not accepted')
    access = phone.call('shell', 'content query --uri content://' + RESTORE_PROVIDER
                       + '/template_current/wallpaper --user 0', required=False)
    (session / 'provider-query.txt').write_bytes(access.stdout + access.stderr)
    (session / 'wallpaper-service.txt').write_bytes(phone.call('exec-out',
        'dumpsys activity service com.miui.miwallpaper.server.MiuiWallPaperControllerService').stdout)
    report = dict(schemaVersion=2, nativeApkSha256=PACKAGE_HASHES, resources=rows,
                  unknownPathCount=unknown, outerWallpaperResourceCount=len(wallpaper_paths),
                  providerReadQuery=provider_query_status(access),
                  scope='Read-only dependency/read/write checks, not a native restore proof',
                  exactRestoreProven=False, nativeApplyAllowed=False)
    (session / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Native dependencies inventoried privately:', len(rows),
          '; readable:', sum(row['readableByShell'] for row in rows),
          '; writable checks:', sum(row['writableByShell'] for row in rows),
          '; unknown paths:', unknown)
    print('No native state was changed; a read check/backup does not prove the restore writer.')
    print('Outer-wallpaper images:', len(wallpaper_paths), '; OEM provider:', report['providerReadQuery'])
    print('Private inventory: ' + str(session))


def private_session(path):
    path = Path(path).resolve()
    root = (ROOT / 'work/phone-qa').resolve()
    if root not in path.parents or not re.fullmatch('pet-preview-[0-9a-f]{32}', path.name):
        raise ValueError('Use this tool\'s existing ignored private preview session')
    return path


def require_unlocked(phone):
    if 'mWakefulness=Awake' not in phone.text('dumpsys power'):
        raise ValueError('Unlock the phone normally; preview never wakes it')
    if not re.search(r'\bshowing=false\b', phone.text('dumpsys window policy')):
        raise ValueError('Secure keyguard is showing or unknown; unlock normally')


def verified_inventory(path, snapshot):
    path = Path(path).resolve()
    root = (ROOT / 'work/phone-qa').resolve()
    if root not in path.parents or not re.fullmatch('pet-inventory-[0-9a-f]{32}', path.name):
        raise ValueError('Use a fresh private inventory from this tool')
    report = json.loads((path / 'inventory.json').read_text(encoding='utf-8'))
    if (report.get('schemaVersion') != 2 or report.get('nativeApkSha256') != PACKAGE_HASHES
            or report.get('unknownPathCount') != 0 or report.get('nativeApplyAllowed') is not False):
        raise ValueError('Incomplete or different-profile inventory')
    if any((path / (key + '.json')).read_bytes() != snapshot[key] for key in KEYS):
        raise ValueError('Native selection/history changed since the inventory')
    rows = report.get('resources', [])
    if not 1 <= len(rows) <= 256 or len({r['path'] for r in rows}) != len(rows):
        raise ValueError('Invalid resource inventory')
    for row in rows:
        native_path(row['path'])
        name = row.get('backupFile', '')
        if not re.fullmatch(r'resource-[0-9]{3}\.bin', name):
            raise ValueError('Missing resource backup')
        backup = (path / name).resolve()
        if backup.parent != path:
            raise ValueError('Backup escaped its private inventory')
        data = backup.read_bytes()
        if len(data) != row['bytes'] or sha(data) != row['sha256']:
            raise ValueError('Private resource backup changed')
    metadata = next((r for r in rows if r['path'] == WALLPAPER_METADATA), None)
    if metadata is None:
        raise ValueError('Missing outer-wallpaper metadata')
    wallpaper_paths = outer_wallpaper_paths((path / metadata['backupFile']).read_bytes())
    if (set(wallpaper_paths) - {r['path'] for r in rows}
            or report.get('outerWallpaperResourceCount') != len(wallpaper_paths)):
        raise ValueError('Missing actual outer-wallpaper image backups')
    return report


def validate_restore_preview_template(raw):
    if not raw or len(raw) > 32768:
        raise ValueError('Invalid or oversized existing template')
    template = json.loads(raw)
    if not isinstance(template, dict) or template.get('clockInfo', {}).get('templateId') != 'splicing':
        raise ValueError('Only the inspected existing splicing template is supported')
    for key in ('wallpaperInfo0', 'wallpaperInfo180'):
        wallpaper = template.get(key)
        position = wallpaper.get('positionInfo') if isinstance(wallpaper, dict) else None
        matrix = position.get('matrixArr') if isinstance(position, dict) else None
        if (not isinstance(matrix, list) or len(matrix) != 9
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in matrix)
                or matrix[8] != 1 or matrix[6:8] != [0, 0]
                or matrix[0] * matrix[4] - matrix[1] * matrix[3] == 0):
            raise ValueError('Existing native crop lacks a valid matrixArr; direct JSON entry crashes '
                             'EditorImagePreview. Do not invent crop geometry for Restore.')
    return template


def restore_preview(phone, inventory):
    """Reopen the unchanged built-in selection; this exercises no restore/write path."""
    before = stable_state(phone)
    report = verified_inventory(inventory, before)
    template_raw = before[KEYS[0]]
    validate_restore_preview_template(template_raw)
    require_unlocked(phone)
    for row in report['resources']:
        tokens = phone.text('sha256sum ' + shlex.quote(row['path'])).split()
        if not tokens or tokens[0] != row['sha256']:
            raise ValueError('A native resource changed since backup; no preview opened')
    session = ROOT / 'work/phone-qa' / ('pet-preview-' + uuid.uuid4().hex)
    session.mkdir()
    for key, data in before.items():
        (session / (key + '.before.json')).write_bytes(data)
    (session / 'template.json').write_bytes(template_raw)
    receipt = dict(schemaVersion=1, previewKind='existing-splicing-template',
                   build=EXPECTED_BUILD, nativeApkSha256=PACKAGE_HASHES,
                   nativeApplyPerformed=False, exactRestoreProven=False, status='prepared',
                   beforeSettingsSha256={k: sha(v) for k, v in before.items()},
                   templateSha256=sha(template_raw), backedUpResourceCount=len(report['resources']))
    (session / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    if stable_state(phone) != before:
        raise ValueError('Native choice changed before launch; no preview opened')
    command = 'am start -W -a miui.tinykeyguard.editor.EDIT -n ' + COMPONENT
    command += ' --es param_template_item_json ' + shlex.quote(template_raw.decode('utf-8').strip())
    (session / 'launch.txt').write_bytes(phone.call('shell', command).stdout)
    receipt['status'] = 'existing-template-preview-launched-unverified'
    (session / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('Private preview session: ' + str(session))
    print('Existing template preview only. Do not press Apply; this does not prove restoration.')


def begin(phone, prepared):
    prepared = Path(prepared).resolve()
    manifest = json.loads((prepared / 'manifest.json').read_text(encoding='utf-8'))
    variant = manifest.get('variant', 'original')
    proof, pag, poster = verified_resources(variant)
    pag_name = 'original.pag' if variant == 'original' else 'native.pag'
    template_raw = (prepared / 'template.json').read_bytes()
    template = json.loads(template_raw)
    biz_id = validate_template(template, proof, variant)
    if (prepared / pag_name).read_bytes() != pag or (prepared / 'poster.png').read_bytes() != poster:
        raise ValueError('Prepared resources changed')
    if manifest['bizId'] != biz_id or manifest['nativeApplyAllowed'] is not False:
        raise ValueError('Unknown prepared manifest')
    if len(manifest['resources']) != 3 or {r['file'] for r in manifest['resources']} != {pag_name, 'poster.png', 'template.json'}:
        raise ValueError('Expected exactly three matching prepared inputs')
    for row in manifest['resources']:
        if row['file'] not in (pag_name, 'poster.png', 'template.json'):
            raise ValueError('Unknown input resource')
        data = (prepared / row['file']).read_bytes()
        if sha(data) != row['sha256'] or len(data) != row['bytes']:
            raise ValueError('Prepared manifest does not match resources')
    require_unlocked(phone)
    before = stable_state(phone)
    session = ROOT / 'work/phone-qa' / ('pet-preview-' + uuid.uuid4().hex)
    session.mkdir()
    for key, data in before.items():
        (session / (key + '.before.json')).write_bytes(data)
    # Private diagnostic only. Opaque wallpaper-service snapshot is NOT a restorable backup.
    (session / 'wallpaper.before.txt').write_bytes(phone.call('exec-out', 'dumpsys wallpaper').stdout)
    remote = STAGING_ROOT + biz_id
    if phone.call('shell', 'test ! -e ' + shlex.quote(remote), required=False).returncode:
        raise ValueError('Staging identity already exists; never overwrite it')
    phone.text('mkdir -p ' + shlex.quote(remote))
    for name in (pag_name, 'poster.png'):
        phone.call('push', prepared / name, remote + '/' + name)
        if phone.text('sha256sum ' + remote + '/' + name).split()[0] != sha((prepared / name).read_bytes()):
            raise ValueError('Staged resource hash mismatch')
    (session / 'template.json').write_bytes(template_raw)
    receipt = dict(schemaVersion=1, bizId=biz_id, build=EXPECTED_BUILD,
                   nativeApkSha256=PACKAGE_HASHES, nativeApplyPerformed=False,
                   exactRestoreProven=False, status='staged',
                   beforeSettingsSha256={k: sha(v) for k, v in before.items()})
    (session / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    if stable_state(phone) != before:
        raise ValueError('Native choice changed before launch; staged resources retained, no preview opened')
    command = 'am start -W -a miui.tinykeyguard.editor.EDIT -n ' + COMPONENT
    command += ' --es param_template_item_json ' + shlex.quote(template_raw.decode('utf-8').strip())
    (session / 'launch.txt').write_bytes(phone.call('shell', command).stdout)
    receipt['status'] = 'preview-launched-unverified'
    (session / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('Private preview session: ' + str(session))
    print('Preview only: do not press Apply. Native load/motion and rollback remain unproven.')


def finish(phone, session):
    session = private_session(session)
    receipt = json.loads((session / 'receipt.json').read_text(encoding='utf-8'))
    from prepare_native_template import validate_id
    if receipt.get('previewKind') == 'existing-splicing-template':
        raw = (session / 'template.json').read_bytes()
        if (raw != (session / (KEYS[0] + '.before.json')).read_bytes()
                or sha(raw) != receipt['templateSha256']):
            raise ValueError('Existing-template preview receipt changed')
    else:
        validate_id(receipt['bizId'])
    if receipt['nativeApplyPerformed'] is not False or receipt['nativeApkSha256'] != PACKAGE_HASHES:
        raise ValueError('Not a matching preview-only session')
    # Never send Back into an unrelated screen or automate an Apply/cancel confirmation.
    focus = phone.text('dumpsys window')
    focused = [line for line in focus.splitlines() if 'mCurrentFocus=' in line]
    if len(focused) != 1 or COMPONENT not in focused[0]:
        raise ValueError('The exact native editor must be focused before sending Back')
    phone.text('input keyevent KEYCODE_BACK')
    time.sleep(.3)
    after = stable_state(phone)
    before = {k: (session / (k + '.before.json')).read_bytes() for k in KEYS}
    if {k: sha(v) for k, v in before.items()} != receipt['beforeSettingsSha256']:
        raise ValueError('Private baseline changed; no restoration guessed')
    for key, data in after.items():
        (session / (key + '.after.json')).write_bytes(data)
    (session / 'wallpaper.after.txt').write_bytes(phone.call('exec-out', 'dumpsys wallpaper').stdout)
    receipt['settingsUnchangedAfterBack'] = before == after
    receipt['editorExited'] = not any(COMPONENT in line for line in phone.text('dumpsys window').splitlines() if 'mCurrentFocus=' in line)
    receipt['status'] = ('preview-exited-settings-unchanged' if receipt['editorExited'] else 'back-confirmation-pending') if before == after else 'state-changed-stop'
    (session / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    if before != after:
        raise ValueError('Native settings changed: stop and inspect private state; no guessed restore')
    if not receipt['editorExited']:
        raise ValueError('Back did not exit the editor; inspect its Cancel confirmation, never press Apply')
    print('Back sent; both native settings are byte-identical. Wallpaper/cache restore is not proven.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--adb', default='C:/platform-tools/adb.exe')
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('begin').add_argument('--prepared', required=True, type=Path)
    sub.add_parser('finish').add_argument('--session', required=True, type=Path)
    sub.add_parser('restore-preview').add_argument('--inventory', required=True, type=Path)
    sub.add_parser('inspect')
    args = parser.parse_args()
    phone = Phone(args.serial, args.adb)
    if args.action == 'begin':
        begin(phone, args.prepared)
    elif args.action == 'finish':
        finish(phone, args.session)
    elif args.action == 'restore-preview':
        restore_preview(phone, args.inventory)
    else:
        inspect(phone)


if __name__ == '__main__':
    main()
