"""Fresh mini-app QA and presentation captures, guarded emulator-5554 only."""
from pathlib import Path
import hashlib
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
ADB = 'C:/platform-tools/adb.exe'
DEST = ROOT / 'work/qa-v03/device-files'
NAMES = {'original_water_sha', 'original_words_sha', 'original_focus_sha',
         'off_by_default', 'dialog_browse', 'draft_no_writes', 'cancel_preserves_cover',
         'apply_water', 'hidden_pet_released', 'no_pet_frame_loop', 'offline_restrictions',
         'original_canvas_ready', 'no_native_bridge', 'water_real_touch',
         'water_webview_recreation_persists', 'tab_focus', 'focus_real_start_touch',
         'focus_no_frame_writes', 'focus_pause_touch', 'tab_words', 'original_word_deck',
         'word_unknown_real_touch', 'word_known_real_touch', 'stop_destroys_webview',
         'restart_restores_card', 'return_to_pet', 'preferences_restored'}


def adb(*args, check=True):
    p = subprocess.run([ADB, '-s', 'emulator-5554', *map(str, args)], capture_output=True,
                       text=True, encoding='utf8', errors='replace', timeout=120)
    if check and p.returncode:
        raise RuntimeError(p.stdout + p.stderr)
    return p


def main():
    assert adb('shell', 'getprop ro.kernel.qemu').stdout.strip() == '1'
    assert adb('shell', 'getprop ro.hardware').stdout.strip() in ('ranchu', 'goldfish')
    apk = ROOT / 'outputs/FlipPets.apk'
    binary = hashlib.sha256(apk.read_bytes()).hexdigest()
    print(adb('install', '--no-incremental', '-r', apk).stdout.strip(), flush=True)
    installed = adb('shell', 'pm path org.flippets.app').stdout.strip().removeprefix('package:')
    assert adb('shell', 'sha256sum', installed).stdout.split()[0] == binary
    adb('shell', 'am force-stop org.flippets.app')
    adb('shell', 'wm size 1224x2912')
    adb('shell', 'wm density 520')
    adb('shell', 'settings put system font_scale 1.0')
    remote = '/sdcard/Android/data/org.flippets.app/files/'
    captures = ('mini-focus.png', 'mini-water.png', 'mini-words.png')
    for name in ('mini-apps-qa.json', *captures):
        adb('shell', 'rm -f ' + remote + name)
    adb('shell', 'am start --display 0 -n org.flippets.app/.MainActivity -f 0x10008000 --ez qaMiniApps true')
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        p = adb('shell', 'cat ' + remote + 'mini-apps-qa.json', check=False)
        try:
            report = json.loads(p.stdout)
        except json.JSONDecodeError:
            time.sleep(1)
            continue
        DEST.mkdir(parents=True, exist_ok=True)
        (DEST / 'mini-apps-qa.json').write_text(json.dumps(report, indent=2), encoding='utf8')
        assert report['apkSha256'] == binary
        assert report['tested'] == len(NAMES) and report['failed'] == 0 and report['skipped'] == [], report
        assert {r['test'] for r in report['results']} == NAMES
        assert all(r['ok'] is True for r in report['results'])
        images = []
        for name in captures:
            adb('pull', remote + name, DEST / name)
            images.append({'file': name, 'sha256': hashlib.sha256((DEST / name).read_bytes()).hexdigest()})
        (DEST / 'mini-apps-captures.json').write_text(json.dumps({
            'apkSha256': binary, 'capture': 'Android PixelCopy of composed Main window',
            'mainSize': '1224x2912', 'density': 520, 'images': images,
            'limitation': 'Emulator only; schematic camera overlay does not prove physical clearance'
        }, indent=2), encoding='utf8')
        assert hashlib.sha256(apk.read_bytes()).hexdigest() == binary
        print(f'{len(NAMES)} mini-app checks passed: {binary}', flush=True)
        return
    raise TimeoutError('No completed mini-app report')


if __name__ == '__main__':
    main()
