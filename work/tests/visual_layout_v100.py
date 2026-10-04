"""Capture actual clock/clockless UI and virtual cover on our guarded emulator only."""
from device_qa import *
import hashlib,json

guard()
binary=hashlib.sha256((ROOT.parent/'outputs/FlipPets.apk').read_bytes()).hexdigest()
installed=shell('pm path org.flippets.app').strip().removeprefix('package:')
assert shell('sha256sum '+installed).split()[0]==binary
rows=[]
originalMode=None
def main():
    # Clear only this app's Main task, including stale emulator QA launch extras.
    shell('am start --display 0 -n org.flippets.app/.MainActivity -f 0x10008000');time.sleep(1.5)
def tap(label,partial=False):
    tree=ui('layout-v100')
    found=[n for n in tree.iter('node') if (label.casefold() in n.get('text','').casefold() if partial else label.casefold()==n.get('text','').casefold())]
    assert found,'Missing control: '+label
    x,y,x2,y2=map(int,re.findall(r'\d+',found[0].get('bounds')))
    shell(f'input -d 0 tap {(x+x2)//2} {(y+y2)//2}');time.sleep(.8)
def capture(name):
    screenshot(name);rows.append({'screenshot':name+'.png','reviewed':False})
try:
    shell('input -d 0 keyevent KEYCODE_WAKEUP');shell('wm dismiss-keyguard')
    shell('cmd statusbar collapse');shell('am force-stop org.flippets.app')
    shell('wm size 1224x2912');shell('wm density 520')
    shell('settings put global overlay_display_devices ""')
    launch(3);time.sleep(.8);shell('am force-stop org.flippets.app')
    for clockless in (False,True):
        main()
        tap('Вариант и положение',True)
        if originalMode is None:
            originalMode=any(n.get('text')=='Без часов · крупнее справа' and n.get('checked')=='true' for n in ui('layout-original-v100').iter('node'))
        tap('Без часов · крупнее справа' if clockless else 'С часами · нынешний размер')
        name='layout-charlie-'+('clockless' if clockless else 'clock')+'-v100'
        capture(name)
        if clockless:
            shell('input -d 0 swipe 1060 2330 1060 1100 500');capture('layout-controls-v100')
        tap('Применить');time.sleep(.7)
        # Force-stop/reopen reads persisted settings rather than a preview draft.
        shell('am force-stop org.flippets.app')
        main()
        tree=ui('layout-persist-v100')
        expected='Вариант и положение · '+('без часов' if clockless else 'с часами')
        assert any(n.get('text')==expected for n in tree.iter('node')),'Mode did not persist'
        shell('settings put global overlay_display_devices 1208x1392/520');time.sleep(2)
        display=max(map(int,re.findall(r'mDisplayId=\s*(\d+)',shell('dumpsys display'))))
        physical=re.search(r'Display (\d+) \(Virtual display\): displayName="Overlay #1"',shell('dumpsys SurfaceFlinger --display-id'))[1]
        launch(3,display);time.sleep(7)
        file='cover-charlie-'+('clockless' if clockless else 'clock')+'-v100.png'
        shell(f'screencap -d {physical} -p /sdcard/flip-cover-layout.png');adb('pull','/sdcard/flip-cover-layout.png',QA/file)
        rows.append({'screenshot':file,'reviewed':False,'modePersistedAfterProcessRestart':True})
        shell('am force-stop org.flippets.app');shell('settings put global overlay_display_devices ""');time.sleep(1)
finally:
    shell('am force-stop org.flippets.app',check=False)
    shell('settings put global overlay_display_devices ""',check=False)
    if originalMode is not None:
        main();tap('Вариант и положение',True)
        tap('Без часов · крупнее справа' if originalMode else 'С часами · нынешний размер');tap('Применить')
    shell('am force-stop org.flippets.app',check=False)
report={'apkSha256':binary,'environment':'Standard Android16 emulator; Main1224x2912/520, virtual cover1208x1392/520; no physical camera-clearance claim','scope':'Real UI controls, explicit Apply, process-restart persistence and owned APK screenshots; Charlie donor crest remains truncated in intermediate frames','tested':2,'failed':0,'reviewCompleted':False,'results':rows}
(QA/'visual-layout-v100.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Captured',len(rows),'screenshots; both modes persisted after process restart',flush=True)
