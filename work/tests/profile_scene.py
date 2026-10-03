"""Scoped scenery-mask CPU/PSS sample on emulator-5554; no phone or battery estimate."""
from device_qa import *
import json,hashlib

guard()
apk=ROOT.parent/'outputs/FlipPets.apk';sha=hashlib.sha256(apk.read_bytes()).hexdigest()
installed=shell('pm path org.flippets.app').strip().removeprefix('package:')
assert shell('sha256sum '+installed).split()[0]==sha
hz=int(shell('getconf CLK_TCK').strip());rows=[]
def clock(pid):
    lines=shell(f'cat /proc/{pid}/stat; cat /proc/uptime').strip().splitlines();fields=lines[0].split(') ',1)[1].split()
    return (int(fields[11])+int(fields[12]))/hz,float(lines[1].split()[0])
def sample(name):
    pid=shell('pidof org.flippets.app').strip();a=clock(pid);time.sleep(4);b=clock(pid);mem=memory(pid);mem.pop('raw',None)
    row={'scenario':name,'durationSeconds':round(b[1]-a[1],2),'cpuPercentOneCore':round(100*(b[0]-a[0])/(b[1]-a[1]),2),**mem};rows.append(row);print(row,flush=True)
try:
    shell('am force-stop org.flippets.app');shell('settings put global overlay_display_devices ""');shell('wm size 1208x1392');shell('wm density 520')
    launch(8);time.sleep(8)
    pid=shell('pidof org.flippets.app').strip()
    assert 'PLAYBACK_END' in shell(f'logcat -d --pid={pid} -s FlipPets:I'), 'No completed finite animation; held sample would be invalid'
    sample('Lola held scenery frame after observed PLAYBACK_END')
    shell('input -d 0 tap 950 1000');sample('Lola touch reaction interval; may include completed frame')
    shell('am start --display 0 -a android.settings.SETTINGS');time.sleep(2);sample('Lola hidden behind Settings')
    pid=shell('pidof org.flippets.app').strip();log=shell(f'logcat -d --pid={pid} -s FlipPets:I');feathers=re.findall(r'SCENE_FEATHER (.+)',log)
    assert feathers and any('hardware=true' in x for x in feathers)
    report={'apkSha256':sha,'environment':'Standard Android16 x86_64 emulator, software decoding/SwiftShader GPU; 100% CPU is one core. Scoped activity scenery-mask sample, not phone battery cost.','results':rows,'hardwareCanvasObserved':True,'sceneFeather':feathers[-1],'limitations':['4-second samples; no long memory-leak or thermal/battery test.','Main and folded native wallpaper engines excluded.']}
    (QA/'resource-profile-v091.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
finally:
    shell('am force-stop org.flippets.app',check=False);shell('wm size 1224x2912',check=False)
