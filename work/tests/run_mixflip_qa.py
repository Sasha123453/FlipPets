"""Observe finite stock scenes in the actual current APK on guarded emulator-5554."""
from pathlib import Path
import hashlib,json,time,subprocess
ROOT=Path(__file__).resolve().parents[2]
SERIAL='emulator-5554'
STEMS=('dewen','shuitun','shuita','bixiong','xianluo','heibao')
NAMES={'native_summary_fixed_labels','native_summary_excludes_private_fields','native_summary_refuses_unknown_history','preferences_restored'}
NAMES.update('charlie_scene'+str(scene)+'_native_geometry' for scene in range(12))
NAMES.update(('charlie_clockless_same_native_size','charlie_manual_relative_to_native','charlie_cancel_native_geometry','charlie_stop_releases'))
for stem in STEMS:
    NAMES.update(stem+'_'+name for name in ('loaded_original_geometry','busy_tap_ignored','stop_releases','restart_plays_saved_scene'))
    NAMES.update(stem+'_scene'+str(scene)+'_'+name for scene in range(3) for name in ('finite_hold','tap_next'))
assert len(NAMES)==80


def validate(data,digest):
    assert data['apkSha256']==digest and data['tested']==80 and data['failed']==0 and data.get('skipped')==[]
    rows=data['results'];assert len(rows)==80 and {r['test'] for r in rows}==NAMES and all(r['ok'] for r in rows)


def main():
    def adb(*args):
        p=subprocess.run(['C:/platform-tools/adb.exe','-s',SERIAL,*map(str,args)],capture_output=True,encoding='utf-8',timeout=120)
        if p.returncode:raise RuntimeError(p.stdout+p.stderr)
        return p.stdout
    assert adb('shell','getprop ro.kernel.qemu').strip()=='1'
    assert any(x in adb('shell','getprop ro.hardware') for x in ('ranchu','goldfish'))
    apk=ROOT/'outputs/FlipPets.apk';digest=hashlib.sha256(apk.read_bytes()).hexdigest()
    print(adb('install','--no-incremental','-r',apk),flush=True)
    remote='/sdcard/Android/data/org.flippets.app/files/mixflip-qa.json'
    adb('shell','am force-stop org.flippets.app');adb('shell','rm -f '+remote)
    adb('shell','am start --display 0 -n org.flippets.app/.MainActivity -f 0x10008000 --ez qaMixFlip true')
    deadline=time.monotonic()+480
    while time.monotonic()<deadline:
        raw=adb('shell','if [ -f '+remote+' ]; then cat '+remote+'; fi')
        if raw.strip():
            data=json.loads(raw);target=ROOT/'work/qa-v03/device-files/mixflip-qa.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');validate(data,digest);print('80 current APK MIX Flip/shared geometry checks passed',digest,flush=True);return
        time.sleep(2)
    raise TimeoutError('MIX Flip QA did not complete')


if __name__=='__main__':main()
