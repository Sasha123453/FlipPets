"""Exercise owned cover/Main tasks, foreground stop, and simulated fold on emulator only."""
from device_qa import *
import json, hashlib

guard()
assert shell('getprop ro.hardware').strip() in ('ranchu','goldfish')
binary=hashlib.sha256((ROOT.parent/'outputs/FlipPets.apk').read_bytes()).hexdigest()
installed=shell('pm path org.flippets.app').strip().removeprefix('package:')
assert installed.startswith('/') and len(installed.splitlines())==1
assert shell('sha256sum '+installed).split()[0]==binary,'Installed runtime APK differs'
rows=[]
def check(name, ok, detail):
    rows.append(dict(test=name,ok=bool(ok),detail=detail))
    print(name, bool(ok), flush=True)
    assert ok, name
def stacks(): return shell('am stack list').split('RootTask')
def foreground(): return 'isForeground=true' in shell('dumpsys activity services org.flippets.app/.CoverGuard')
def cover_visible():
    return any(f'displayId={display} ' in b and 'org.flippets.app.PetActivity' in b and 'visible=true' in b for b in stacks())
def wait_for(predicate,timeout=8):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if predicate():return True
        time.sleep(.25)
    return predicate()
try:
    shell('cmd statusbar collapse')
    shell('am force-stop org.flippets.app')
    shell('settings put global overlay_display_devices ""')
    shell('wm size 1224x2912');shell('wm density 520')
    shell('settings put global overlay_display_devices 1208x1392/520')
    display,physical=0,None
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        ids=[int(value) for value in re.findall(r'mDisplayId=\s*(\d+)',shell('dumpsys display')) if int(value)>0]
        surface=re.search(r'Display (\d+) \(Virtual display\): displayName="Overlay #1"',shell('dumpsys SurfaceFlinger --display-id'))
        if ids and surface:
            display,physical=max(ids),surface[1]
            break
        time.sleep(.25)
    assert display>0 and physical,'Emulator virtual display did not become ready within15s'
    shell('rm -f /sdcard/Android/data/org.flippets.app/files/controller-stop')
    shell('am start --display 0 -n org.flippets.app/.MainActivity -f 0x10008000')
    launch(29,display,True)
    check('cover_starts_foreground_service',wait_for(lambda:foreground() and cover_visible()),'Real secondary-display coverSession launch, no qaGuard extra; wait for observed foreground and visible activity, bounded8s')
    shell('input -d 0 keyevent KEYCODE_HOME');time.sleep(1)
    check('main_home_cover_continues',cover_visible() and foreground(),'Virtual cover remains visible after Main goes Home')
    owned=[b for b in stacks() if 'displayId=0 ' in b and 'org.flippets.app.MainActivity' in b]
    assert len(owned)==1
    task=re.search(r'id=(\d+)',owned[0])[1]
    shell('am stack remove '+task)
    def retained_after_removal():return cover_visible() and foreground() and not any('org.flippets.app.MainActivity' in b for b in stacks())
    retained=wait_for(retained_after_removal)
    check('main_task_removed_cover_continues',retained,'Only own Main root task removed through Android task manager; wait up to8s for asynchronous removal, cover/service must survive; observed cover='+str(cover_visible())+' foreground='+str(foreground())+' mainAbsent='+str(not any('org.flippets.app.MainActivity' in b for b in stacks())))
    shell(f'screencap -d {physical} -p /sdcard/flip-cover.png');adb('pull','/sdcard/flip-cover.png',QA/'photo-battery-runtime-v110.png')
    shell('am broadcast -a org.flippets.app.STOP_COVER -n org.flippets.app/.StopCover');time.sleep(1)
    check('fold_close_retains_foreground_session',foreground() and not cover_visible(),'Simulated fold receiver closes owned cover task; no physical hinge claim')
    shell('cmd statusbar expand-notifications');time.sleep(.7)
    tree=ui('guard-notification-v110')
    if not any(n.get('text')=='Выключить' for n in tree.iter('node')):
        title=next(n for n in tree.iter('node') if n.get('text')=='Внешний экран · Flip Pets')
        _,top,_,bottom=map(int,re.findall(r'\d+',title.get('bounds')))
        candidates=[n for n in tree.iter('node') if n.get('resource-id')=='android:id/expand_button' and n.get('content-desc')=='Expand']
        def center(n):
            x,y,x2,y2=map(int,re.findall(r'\d+',n.get('bounds')));return (x+x2)//2,(y+y2)//2
        expander=min(candidates,key=lambda n:abs(center(n)[1]-(top+bottom)/2))
        x,y=center(expander);shell(f'input -d 0 tap {x} {y}');time.sleep(.5)
    tap_text('Выключить');time.sleep(1)
    check('notification_stop_stops_foreground',not foreground(),'Actual SystemUI notification action clicked')
    check('stop_signals_shell_controller',shell('cat /sdcard/Android/data/org.flippets.app/files/controller-stop',check=False).strip()=='stop','Owned stop handshake file is written')
except Exception as error:
    rows.append(dict(test='unexpected_error',ok=False,detail=str(error)))
    raise
finally:
    shell('cmd statusbar collapse',check=False)
    shell('settings put global overlay_display_devices ""',check=False)
    assert hashlib.sha256((ROOT.parent/'outputs/FlipPets.apk').read_bytes()).hexdigest()==binary,'Host APK changed during runtime QA'
    current_installed=shell('pm path org.flippets.app').strip().removeprefix('package:')
    assert current_installed.startswith('/') and len(current_installed.splitlines())==1
    assert shell('sha256sum '+current_installed).split()[0]==binary,'Installed APK changed during runtime QA'
    report=dict(apkSha256=binary,installedApkSha256=binary,environment='Standard Android16 API36 x86_64 emulator; virtual cover1208x1392/520 and Main1224x2912/520, not HyperOS',tested=len(rows),failed=sum(not r['ok'] for r in rows),results=rows)
    (QA/'runtime-v110.json').write_text(json.dumps(report,indent=2),encoding='utf8')
