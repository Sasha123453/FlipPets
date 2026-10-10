"""Guarded real WallpaperService preview QA; --execute required. Never presses Apply.

Run only after other emulator QA stops. --crop must be an inspected own-artwork
rectangle inside the stock preview, excluding stock chrome/icons. Raw UI images
and private preferences backups stay in ignored work/wallpaper-check. Root adbd
or debuggable run-as is needed ONLY for exact preference backup/restore, not for
the application's WallpaperService rendering. This script never runs adb root.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import re
import shlex
import subprocess
import tarfile
import time
import zipfile

import device_qa as q

PKG = 'org.flippets.app'
COMPONENT = PKG + '/.PetWallpaper'
WORK = q.ROOT
PRIVATE = WORK / 'wallpaper-check'
REPORT = q.QA / 'wallpaper-preview-v110.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def binary(*args):
    result = subprocess.run([q.ADB, '-s', 'emulator-5554', *args], capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', 'replace'))
    return result.stdout


def safe_preferences(data):
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as archive:
        result = {}
        for member in archive.getmembers():
            if member.isdir():
                if member.name.rstrip('/') != 'shared_prefs':
                    raise ValueError('Unsafe preference backup directory')
                continue
            if not member.isfile() or not re.fullmatch(r'shared_prefs/[A-Za-z0-9_.-]+', member.name):
                raise ValueError('Unsafe/non-preference backup member')
            if member.name in result:
                raise ValueError('Duplicate preference backup member')
            result[member.name] = digest(archive.extractfile(member).read())
        if 'shared_prefs/pets.xml' not in result:
            raise ValueError('Own app preference backup missing pets.xml')
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--crop', help='Reviewed own artwork region: left,top,right,bottom pixels')
    parser.add_argument('--export-crops', action='store_true', help='Publish only the reviewed own-artwork crops, never stock UI screenshots')
    args = parser.parse_args()
    if not args.execute:
        print('Draft/dry run: no ADB. Use --execute --crop L,T,R,B after inspecting the stock preview. No Apply is pressed.')
        return
    if not args.crop:
        parser.error('--execute requires a manually reviewed own-artwork --crop')
    crop = tuple(map(int, args.crop.split(',')))
    if len(crop) != 4 or min(crop) < 0 or crop[2] <= crop[0] or crop[3] <= crop[1]:
        parser.error('Invalid crop bounds')

    q.guard()
    hardware = q.shell('getprop ro.hardware').strip()
    assert 'ranchu' in hardware or 'goldfish' in hardware, 'Emulator hardware required'
    assert q.shell('am get-current-user').strip() == '0', 'Default emulator user only'
    apk = WORK.parent / 'outputs/FlipPets.apk'
    apk_sha = digest(apk.read_bytes())
    paths = q.shell('pm path ' + PKG).strip().splitlines()
    assert len(paths) == 1 and paths[0].startswith('package:')
    installed = paths[0].removeprefix('package:')
    assert q.shell('sha256sum ' + shlex.quote(installed)).split()[0] == apk_sha, 'Installed APK mismatch'
    assert 'isForeground=true' not in q.shell('dumpsys activity services ' + PKG + '/.CoverGuard'), 'Stop owned cover session before this isolated preview test'
    initial_wallpaper = q.shell('dumpsys wallpaper')
    assert 'org.flippets.app.PetWallpaper' not in initial_wallpaper, 'Existing applied PetWallpaper would mix engines; this preview-only test must not replace it'
    initial_components = re.findall(r'mWallpaperComponent=([^\r\n]+)', initial_wallpaper)
    assert initial_components, 'Cannot record original applied wallpaper component'
    PRIVATE.mkdir(parents=True, exist_ok=True)

    root_adbd = q.shell('id -u').strip() == '0'
    prefix = [] if root_adbd else ['run-as', PKG]
    location = '/data/user/0/' + PKG if root_adbd else '.'
    # Fail safely if neither emulator-root nor debuggable run-as can read own prefs.
    def snapshot():
        return binary('exec-out', *prefix, 'tar', '-cf', '-', '-C', location, 'shared_prefs')
    backup = snapshot()
    original_prefs = safe_preferences(backup)
    backup_path = PRIVATE / 'private-preferences-backup.tar'
    backup_path.write_bytes(backup)
    with zipfile.ZipFile(apk) as archive:
        catalogue = json.loads(archive.read('assets/catalog.json'))
        entries = {p['id']: (i, p) for i, p in enumerate(catalogue)}
        source_sha = {identity: {index: digest(archive.read('assets/' + path)) for index, path in entries[identity][1]['clips'].items()}
                      for identity in ['butterfly-carp-hongkong', 'pin-hongkong', 'vortex-hongkong']}
    rows = []
    restored = False
    observed_pid = ''

    def check(name, ok, detail, skipped=False):
        rows.append({'test': name, 'ok': None if skipped else bool(ok), 'skipped': skipped, 'detail': detail})
        print(name, 'SKIP' if skipped else bool(ok), flush=True)
        if not skipped and not ok:
            raise AssertionError(name)

    def own_log():
        nonlocal observed_pid
        pid = q.shell('pidof ' + PKG).strip()
        if pid.isdigit():
            observed_pid = pid
        # The service may exit immediately after its hidden callback. Read the
        # last observed own PID rather than losing that real lifecycle event.
        return q.shell('logcat -d --pid=' + observed_pid + ' -s FlipPets:I') if observed_pid else ''

    def wait_for(predicate, seconds=8):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if predicate():
                return True
            time.sleep(.2)
        return predicate()

    def capture(name):
        from PIL import Image
        raw = binary('exec-out', 'screencap', '-p')
        (PRIVATE / ('raw-stock-preview-' + name + '.png')).write_bytes(raw)
        image = Image.open(io.BytesIO(raw)).convert('RGBA')
        assert crop[2] <= image.width and crop[3] <= image.height
        art = image.crop(crop)
        if args.export_crops:
            art.save(q.QA / ('wallpaper-own-crop-' + name + '-v110.png'))
        return digest(art.tobytes())

    def open_preview(identity):
        nonlocal observed_pid
        q.shell('am force-stop ' + PKG)
        q.launch(entries[identity][0])  # Existing emulator-only selection, no new app extras.
        time.sleep(.8)
        # Kill only our warm-up Activity; the preview then binds the real service.
        q.shell('am force-stop ' + PKG)
        observed_pid = ''
        selection_prefs = safe_preferences(snapshot())
        q.shell('am start -W --display 0 -a android.service.wallpaper.CHANGE_LIVE_WALLPAPER --ecn android.service.wallpaper.extra.LIVE_WALLPAPER_COMPONENT ' + COMPONENT)
        assert wait_for(lambda: 'WALLPAPER_VISIBLE true' in own_log()), 'No true wallpaper visibility callback'
        service = q.shell('dumpsys activity services ' + COMPONENT)
        check(identity + '_real_service_bound', 'ServiceRecord' in service and 'PetWallpaper' in service,
              'Actual Android live-wallpaper preview, real WallpaperService bind and visibility; no Apply')
        return selection_prefs

    def close_preview(identity):
        q.shell('input -d 0 keyevent KEYCODE_BACK')
        stopped = wait_for(lambda: 'WALLPAPER_VISIBLE false' in own_log())
        check(identity + '_real_hidden_callback', stopped, 'Back exits stock preview; own WallpaperService received visible=false')
        q.shell('am force-stop ' + PKG)

    try:
        prefs = open_preview('butterfly-carp-hongkong')
        time.sleep(.5)
        carp_first = capture('carp-early')
        time.sleep(1)
        carp_second = capture('carp-moving')
        check('carp_live_frames_change', carp_first != carp_second, 'Own artwork crop at separated times in actual wallpaper service')
        first_cycle_seconds = max(entries['butterfly-carp-hongkong'][1]['durationMs'].values()) / 1000
        time.sleep(first_cycle_seconds + 1)
        carp_later = capture('carp-after-first-cycle')
        time.sleep(.5)
        check('carp_continues_after_first_cycle', carp_later != capture('carp-later-moving'), 'Visible content still changes after the longest source first-scene duration plus fade/load delay; not proof of internal scene IDs')
        check('carp_does_not_write_preferences_automatically', safe_preferences(snapshot()) == prefs,
              'Exact private preference bytes compared during automatic wallpaper playback; contents not published')
        close_preview('carp')

        open_preview('pin-hongkong')
        time.sleep(1.5)
        held = capture('effect-held')
        time.sleep(.7)
        check('effect_holds_after_finite_clip', held == capture('effect-held-again'), 'Same own crop after one-second native effect completed')
        prefs_before_touch = safe_preferences(snapshot())
        q.shell('input -d 0 tap ' + str((crop[0]+crop[2])//2) + ' ' + str((crop[1]+crop[3])//2))
        time.sleep(.25)
        replay = capture('effect-touch')
        prefs_after_touch = safe_preferences(snapshot())
        forwarded = prefs_before_touch != prefs_after_touch
        check('effect_touch_replays_when_forwarded', replay != held if forwarded else False,
              'Real preview touch forwarded to WallpaperService' if forwarded else 'Stock preview did not forward an observable touch; replay unsupported by this preview UI', skipped=not forwarded)
        close_preview('effect')

        open_preview('vortex-hongkong')
        time.sleep(.5)
        vortex_first = capture('vortex-first')
        time.sleep(1)
        check('vortex_real_video_changes', vortex_first != capture('vortex-second'), 'Real wallpaper MediaPlayer frames, not MediaMetadataRetriever or Activity preview')
        close_preview('vortex')
        current = re.findall(r'mWallpaperComponent=([^\r\n]+)', q.shell('dumpsys wallpaper'))
        check('applied_wallpaper_unchanged', current == initial_components, 'No Set wallpaper/Apply action; original system wallpaper component retained')
    except Exception as error:
        if not rows or rows[-1].get('ok') is not False:
            rows.append({'test': 'unexpected_error', 'ok': False, 'skipped': False, 'detail': str(error)})
        raise
    finally:
        q.shell('input -d 0 keyevent KEYCODE_BACK', check=False)
        q.shell('am force-stop ' + PKG, check=False)
        try:
            current_names = safe_preferences(snapshot())
            for name in current_names.keys() - original_prefs.keys():
                target = ('/data/user/0/' + PKG + '/' if root_adbd else '') + name
                q.shell(' '.join(map(shlex.quote, [*prefix, 'rm', '-f', target])))
            q.adb('push', backup_path, '/data/local/tmp/flippets-wallpaper-prefs.tar')
            q.shell(' '.join(map(shlex.quote, [*prefix, 'tar', '-xf', '/data/local/tmp/flippets-wallpaper-prefs.tar', '-C', location])))
            restored = safe_preferences(snapshot()) == original_prefs
            if restored:
                backup_path.unlink()  # Exactly this verified local backup file; no recursive cleanup.
            q.shell('rm -f /data/local/tmp/flippets-wallpaper-prefs.tar', check=False)
        except Exception as restore_error:
            rows.append({'test': 'preferences_restore', 'ok': False, 'skipped': False, 'detail': str(restore_error)})
        if not restored and not any(r['test'] == 'preferences_restore' for r in rows):
            rows.append({'test': 'preferences_restore', 'ok': False, 'skipped': False, 'detail': 'Exact restore comparison failed; private backup retained ignored'})
        report = {'apkSha256': apk_sha, 'sourceMediaSha256': source_sha,
                  'environment': 'Guarded Android16 emulator5554; actual stock live-wallpaper preview, not HyperOS/native cover/AOD or physical camera validation',
                  'preferencesAccess': 'Emulator root adbd snapshot only' if root_adbd else 'Own debug run-as snapshot only',
                  'preferencesRestored': restored, 'crop': crop,
                  'screenshotPolicy': 'Raw stock preview images ignored; only explicitly reviewed own-artwork crops can be exported, labelled as wallpaper preview crops',
                  'tested': sum(not r['skipped'] for r in rows), 'skipped': sum(r['skipped'] for r in rows),
                  'failed': sum(r['ok'] is False for r in rows), 'results': rows}
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if not restored:
            raise RuntimeError('Own preferences restore failed; see ignored backup and report')


if __name__ == '__main__':
    main()
