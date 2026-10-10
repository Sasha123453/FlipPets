"""Real Activity/cards plus host Stop, Back, Home and process recreation; emulator only."""
from pathlib import Path
import hashlib,json,subprocess,time,uuid
ROOT=Path(__file__).resolve().parents[2]
ADB='C:/platform-tools/adb.exe'
DEST=ROOT/'work/qa-final/native-cards'
from native_apps_contract import NAMES
def adb(*args,ok=True):
    p=subprocess.run([ADB,'-s','emulator-5554',*map(str,args)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    if ok and p.returncode:raise RuntimeError(p.stdout+p.stderr)
    return p
def shell(code,ok=True):return adb('shell',code,ok=ok)
def main():
    assert shell('getprop ro.kernel.qemu').stdout.strip()=='1'
    assert shell('getprop ro.hardware').stdout.strip() in ('ranchu','goldfish')
    apk=ROOT/'outputs/FlipPets.apk';binary=hashlib.sha256(apk.read_bytes()).hexdigest();token=str(uuid.uuid4());origin='qa-native-'+token+'.invalid'
    print(adb('install','--no-incremental','-r',apk).stdout.strip(),flush=True)
    installed=shell('pm path org.flippets.app').stdout.strip().removeprefix('package:');assert shell('sha256sum '+installed).stdout.split()[0]==binary
    shell('am force-stop org.flippets.app');shell('wm size 1208x1392');shell('wm density 520');shell('settings put system font_scale 1.0')
    remote='/sdcard/Android/data/org.flippets.app/files/'
    for name in ('native-cards-qa.json','native-cards-qa-pending.json','native-cards-qa-ack.json','native-water.png','native-focus.png','native-words.png'):shell('rm -f '+remote+name)
    def launch(extra=''):
        shell(f'am start --display 0 -n org.flippets.app/.MainActivity -f 0x10000000 --ez qaNativeApps true --es qaToken {token} --es qaOrigin {origin} '+extra)
    def listener_enabled():
        names=shell('settings get secure enabled_notification_listeners').stdout.strip().split(':')
        return any(n in {'org.flippets.app/.PetNotifications','org.flippets.app/org.flippets.app.PetNotifications'} for n in names)
    def wait_listener(expected):
        limit=time.monotonic()+10
        while listener_enabled()!=expected:
            assert time.monotonic()<limit,'notification-listener access readback'
            time.sleep(.1)
    listener_was_enabled=listener_enabled();handled=set();deadline=time.monotonic()+150
    try:
        # A real notification-listener reconnection writes changeRevision after
        # process death. Isolate that independent writer, not the assertion.
        if listener_was_enabled:shell('cmd notification disallow_listener org.flippets.app/.PetNotifications')
        wait_listener(False)
        launch()
        while time.monotonic()<deadline:
            p=shell('cat '+remote+'native-cards-qa.json',ok=False)
            try:report=json.loads(p.stdout)
            except json.JSONDecodeError:report=None
            if report:
                assert report['apkSha256']==binary and report['token']==token
                DEST.mkdir(parents=True,exist_ok=True);(DEST/'native-cards-qa.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
                assert report['tested']==len(NAMES) and report['failed']==0 and report['skipped']==[],report
                assert {r['test'] for r in report['results']}==NAMES and all(r['ok'] is True for r in report['results'])
                assert handled=={'broadcast','settings-intent','settings-back','home','resume','process'},handled
                images=[]
                for name in ('native-water.png','native-focus.png','native-words.png'):
                    adb('pull',remote+name,DEST/name);images.append(dict(file=name,sha256=hashlib.sha256((DEST/name).read_bytes()).hexdigest()))
                (DEST/'captures.json').write_text(json.dumps(dict(apkSha256=binary,capture='Android PixelCopy composed Activity window',images=images,limitation='Emulator only; not physical camera or Xiaomi continuity proof'),indent=2),encoding='utf-8')
                print(str(len(NAMES))+' native card checks passed: '+binary,flush=True);return
            p=shell('cat '+remote+'native-cards-qa-pending.json',ok=False)
            try:pending=json.loads(p.stdout)
            except json.JSONDecodeError:pending={}
            phase=pending.get('phase')
            if phase and phase not in handled:
                assert pending['token']==token and pending['apkSha256']==binary
                if phase=='broadcast':
                    shell('am broadcast --receiver-foreground -n org.flippets.app/.StopCover -a org.flippets.app.STOP_COVER')
                    ack=DEST/'ack.json';DEST.mkdir(parents=True,exist_ok=True);ack.write_text(json.dumps(pending),encoding='utf-8');adb('push',ack,remote+'native-cards-qa-ack.json')
                elif phase=='settings-intent':shell(f'am start -W --display 0 -n org.flippets.app/.MainActivity -f 0x20000000 --es qaIntentProof {token}')
                elif phase=='settings-back':shell('input keyevent 4')
                elif phase=='home':shell('am start -a android.intent.action.MAIN -c android.intent.category.HOME')
                elif phase=='resume':launch('--ez qaReturn true')
                elif phase=='process':shell('am force-stop org.flippets.app');launch('--ez qaPhase2 true')
                else:raise AssertionError('Unexpected phase '+str(phase))
                handled.add(phase);print('Host phase: '+phase,flush=True)
            time.sleep(.3)
        raise TimeoutError('Native card QA did not finish')
    finally:
        shell('am force-stop org.flippets.app',ok=False);shell('wm size 1224x2912',ok=False)
        if listener_was_enabled:shell('cmd notification allow_listener org.flippets.app/.PetNotifications')
        wait_listener(listener_was_enabled)
if __name__=='__main__':main()
