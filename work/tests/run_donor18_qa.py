"""Guarded real-player donor18 QA on emulator-5554; no physical or implicit ADB target."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
SERIAL="emulator-5554"
NAME="donor18-qa.json"
REMOTE=f"/sdcard/Android/data/org.flippets.app/files/{NAME}"
REQUEST="/sdcard/Android/data/org.flippets.app/files/donor18-hide-request.json"
ACK="/sdcard/Android/data/org.flippets.app/files/donor18-home-ack.txt"
EXPECTED=23
EXPECTED_NAMES={
    "carp_native_sequence_loaded","carp_repeat_count_one","carp_desk29_asset_dimensions",
    "carp_two_actual_auto_transitions","carp_fade_out_native_threshold",
    "carp_hidden_delay_alpha_zero","carp_fade_in_alpha_path","carp_next_scene_differs",
    "carp_auto_scene_preferences_unchanged","carp_auto_global_state_unchanged",
    "carp_manual_tap_restarts_saved_scene","carp_clockless_draft_resources_local",
    "carp_clockless_real_matrix_larger","carp_draft_cancel_restores_clock_matrix",
    "vortex_real_media_player_playing","vortex_background_cover_bounds",
    "vortex_no_clock_or_pet_tap_controls","pin_finite_preview_loaded",
    "pin_completes_then_holds","pin_tap_replays_existing_player",
    "actual_activity_hide_stops_active_carp","hidden_releases_players_and_callbacks",
    "donor_preferences_and_selection_restored",
}


def validate(result,binary):
    if result.get('apkSha256')!=binary:
        raise AssertionError('Donor18 report SHA does not match current APK')
    rows=result.get('results',[])
    if result.get('tested')!=EXPECTED or len(rows)!=EXPECTED:
        raise AssertionError(f'Expected exactly{EXPECTED} donor18 checks')
    if result.get('failed')!=0 or result.get('skipped')!=[]:
        raise AssertionError('Donor18 report has failures, skips, or missing skipped list')
    if any(row.get('ok') is not True for row in rows):
        raise AssertionError('At least one donor18 runtime check failed')
    if {row.get('test') for row in rows}!=EXPECTED_NAMES:
        raise AssertionError('Donor18 cases missing, duplicated, or unexpected')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb',default='C:/platform-tools/adb.exe')
    parser.add_argument('--apk',type=Path,default=ROOT/'outputs/FlipPets.apk')
    parser.add_argument('--qa-dir',type=Path,default=ROOT/'work/qa-v03/device-files')
    parser.add_argument('--timeout',type=float,default=120)
    args=parser.parse_args()
    binary=hashlib.sha256(args.apk.read_bytes()).hexdigest()
    args.qa_dir.mkdir(parents=True,exist_ok=True)
    destination=args.qa_dir/NAME

    def adb(*parts,check=True,timeout=30):
        result=subprocess.run([args.adb,'-s',SERIAL,*parts],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
        if check and result.returncode:
            raise RuntimeError(result.stdout+result.stderr)
        return result

    if adb('shell','getprop ro.kernel.qemu').stdout.strip()!='1':
        raise RuntimeError('Target is not an Android emulator')
    hardware=adb('shell','getprop ro.hardware').stdout.strip()
    if not any(value in hardware for value in ('ranchu','goldfish')):
        raise RuntimeError('Unexpected emulator hardware')
    # Restore just this fixture's display overrides when done; no system app UI read.
    size=re.search(r'Override size:\s*(\d+x\d+)',adb('shell','wm size').stdout)
    density=re.search(r'Override density:\s*(\d+)',adb('shell','wm density').stdout)
    old_size=size[1] if size else 'reset'
    old_density=density[1] if density else 'reset'
    listener_names=adb('shell','settings get secure enabled_notification_listeners').stdout.strip().split(':')
    listener_was_enabled=any(name in {'org.flippets.app/.PetNotifications','org.flippets.app/org.flippets.app.PetNotifications'} for name in listener_names)
    completed=False
    try:
        print(adb('install','--no-incremental','-r',str(args.apk),timeout=120).stdout.strip(),flush=True)
        # This suite asserts no automatic global revision writes. Isolate its
        # renderer from real external media/notification events; utility QA
        # separately exercises the real listener and restores its own fixtures.
        if listener_was_enabled:
            adb('shell','cmd notification disallow_listener org.flippets.app/.PetNotifications')
        adb('shell','am force-stop org.flippets.app')
        # Remove only our stale QA tasks, whose old launch extras could resume
        # another instrumentation run. Never remove a root containing other apps.
        stacks=adb('shell','am stack list').stdout
        for block in stacks.split('RootTask'):
            tasks=[line for line in block.splitlines() if 'taskId=' in line]
            identity=re.search(r'^\s+id=(\d+)\b',block)
            if identity and tasks and all('org.flippets.app/' in line for line in tasks):
                adb('shell','am stack remove '+identity[1])
        adb('shell',f'rm -f {REMOTE} {REQUEST} {ACK}')
        if adb('shell',f'test -e {REMOTE}',check=False).returncode==0:
            raise RuntimeError('Could not remove stale donor18 report')
        destination.unlink(missing_ok=True)
        adb('shell','wm size 1208x1392')
        adb('shell','wm density 520')
        adb('shell','input -d 0 keyevent KEYCODE_WAKEUP')
        adb('shell','wm dismiss-keyguard')
        adb('shell','cmd statusbar collapse')
        adb('shell','am start --display 0 -n org.flippets.app/.PetActivity -f 0x18008000 --ez qaDonor18 true')
        deadline=time.monotonic()+args.timeout
        home_token=None
        while time.monotonic()<deadline:
            if home_token is None:
                request=adb('shell',f'cat {REQUEST}',check=False)
                if request.returncode==0:
                    try:
                        handshake=json.loads(request.stdout)
                    except json.JSONDecodeError:
                        pass
                    else:
                        token=handshake.get('runToken','')
                        if handshake.get('apkSha256')!=binary or not isinstance(token,str) or not token.isascii() or not token.isdigit():
                            raise AssertionError('Invalid donor18 hide handshake SHA/token')
                        adb('shell','input -d 0 keyevent KEYCODE_HOME')
                        # Launch the real Home destination as well: input injection
                        # alone can be deferred during a heavy native render frame.
                        adb('shell','am start --display 0 -a android.intent.action.MAIN -c android.intent.category.HOME')
                        # A translucent/animating launcher need not stop the
                        # underlying Activity. Use a real opaque stock Activity
                        # to make this a hidden-surface lifecycle test.
                        adb('shell','am start --display 0 -a android.settings.SETTINGS')
                        adb('shell',f'echo {token} > {ACK}')
                        home_token=token
                        print('Actual KEYCODE_HOME delivered for donor18 hide handshake',flush=True)
            raw=adb('shell',f'cat {REMOTE}',check=False)
            if raw.returncode==0:
                try:
                    json.loads(raw.stdout)
                except json.JSONDecodeError:
                    pass
                else:
                    adb('pull',REMOTE,str(destination))
                    report=json.loads(destination.read_text(encoding='utf-8'))
                    validate(report,binary)
                    report['hostFixture']='Native Home navigation then opaque Android Settings; actual onStop/release required. Owned stale QA tasks removed; listener access isolated/restored.'
                    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                    if hashlib.sha256(args.apk.read_bytes()).hexdigest()!=binary:
                        raise AssertionError('Host APK changed during donor18 QA')
                    completed=True
                    print(f'{EXPECTED} current APK donor18 runtime checks passed: {binary}',flush=True)
                    return
            time.sleep(.1)
        raise TimeoutError(f'No complete donor18 report within{args.timeout:g}s')
    finally:
        if not completed:
            adb('shell','am force-stop org.flippets.app',check=False)
        adb('shell','wm size '+old_size,check=False)
        adb('shell','wm density '+old_density,check=False)
        if listener_was_enabled:
            adb('shell','cmd notification allow_listener org.flippets.app/.PetNotifications',check=False)


if __name__=='__main__':
    main()
