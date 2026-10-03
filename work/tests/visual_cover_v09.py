"""Own APK visual samples on emulator-5554 only; inspect PNGs before marking review."""
from device_qa import *
import hashlib,json

guard()
expected='3d3618e0dd871cbaea2f8a03959df75ed95038e2d79b14ccef90c4c382eacc06'
apk=ROOT.parent/'outputs/FlipPets.apk'
assert hashlib.sha256(apk.read_bytes()).hexdigest()==expected
installed=shell('pm path org.flippets.app').strip().removeprefix('package:')
assert shell('sha256sum '+installed).split()[0]==expected
catalog=json.loads((ROOT/'app/assets/catalog.json').read_text())
rows=[]
try:
    shell('input -d 0 keyevent KEYCODE_WAKEUP');shell('wm dismiss-keyguard');shell('cmd statusbar collapse');shell('am force-stop org.flippets.app')
    shell('wm size 1224x2912');shell('wm density 520')
    shell('dumpsys battery unplug')
    shell('settings put global overlay_display_devices 1208x1392/520');time.sleep(2)
    display=max(map(int,re.findall(r'mDisplayId=\s*(\d+)',shell('dumpsys display'))))
    physical=re.search(r'Display (\d+) \(Virtual display\): displayName="Overlay #1"',shell('dumpsys SurfaceFlinger --display-id'))[1]
    for index,name in [(3,'charlie'),(0,'bubbles'),(1,'roe'),(7,'jumbo'),(8,'lola'),(12,'mp4-cartoon'),(15,'mp4-lumi')]:
        shell('am force-stop org.flippets.app');launch(index,display);time.sleep(3.3)
        pid=shell('pidof org.flippets.app').strip()
        ownlog=shell(f'logcat -d --pid={pid} -s FlipPets:I')
        loads=re.findall(r'\bLOAD (\S+)',ownlog);geometry=re.findall(r'GEOMETRY (.+)',ownlog)
        filename='cover-'+name+'-v09.png'
        shell(f'screencap -d {physical} -p /sdcard/flip-cover-visual.png');adb('pull','/sdcard/flip-cover-visual.png',QA/filename)
        rows.append({'petIndex':index,'petId':catalog[index]['id'],'pet':catalog[index]['name'],'screenshot':filename,'loadedAsset':loads[-1] if loads else None,'geometry':geometry[-1] if geometry else None,'reviewed':False})
        print(name,'captured',flush=True)
    shell('am force-stop org.flippets.app');launch(3);time.sleep(.5);shell('am force-stop org.flippets.app')
    shell('settings put global overlay_display_devices ""');time.sleep(1)
    shell('am start --display 0 -n org.flippets.app/.MainActivity');time.sleep(2)
    tree=ui('main-cover-preview-v09')
    screenshot('main-charlie-preview-v09')
    stage=next((n for n in tree.iter('node') if n.get('content-desc')=='Анимированный питомец. Коснись для реакции.'),None)
    bounds=None if stage is None else list(map(int,re.findall(r'\d+',stage.get('bounds'))))
    rows.append({'screen':'Main Charlie preview','screenshot':'main-charlie-preview-v09.png','mainDimensions':[1224,2912],'previewAccessibilityBounds':bounds,'reviewed':False})
finally:
    shell('dumpsys battery reset',check=False)
    shell('settings put global overlay_display_devices ""',check=False)
    shell('am force-stop org.flippets.app',check=False)
report={'apkSha256':expected,'environment':'Android16 API36 x86_64 emulator; virtual cover1208x1392/520, Main1224x2912/520; no HyperOS/camera-hole hardware','scope':'Own APK screenshots with stock donor assets, no private photos or other applications. Wallpaper MP4 placement unchanged and excluded.','captured':len(rows),'reviewCompleted':False,'results':rows}
(QA/'visual-v09.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
