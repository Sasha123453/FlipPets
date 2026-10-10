"""Install only on the guarded emulator; collect fresh SHA-bound renderer and UI evidence."""
from device_qa import *
import json,hashlib,argparse

guard()
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--resume-render',action='store_true',help='Collect the still-running exact installed APK render suites, then run fresh UI/utility suites')
args=parser.parse_args()
binary=hashlib.sha256((ROOT.parent/'outputs/FlipPets.apk').read_bytes()).hexdigest()
if args.resume_render:
    installed=shell('pm path org.flippets.app').strip().removeprefix('package:')
    assert shell('sha256sum '+installed).split()[0]==binary,'Resume target APK differs'
else:
    print(adb('install','--no-incremental','-r',ROOT.parent/'outputs/FlipPets.apk'),flush=True)
    shell('settings put global overlay_display_devices ""')
    shell('wm size 1208x1392');shell('wm density 520')
    shell('settings put system font_scale 1.0')
    shell('cmd notification allow_listener org.flippets.app/.PetNotifications')
    shell('pm grant org.flippets.app android.permission.POST_NOTIFICATIONS')

def fresh(names):
    shell('am force-stop org.flippets.app')
    for name in names:shell('rm -f /sdcard/Android/data/org.flippets.app/files/'+name)

def collect(name,count,timeout=600):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        raw=shell('cat /sdcard/Android/data/org.flippets.app/files/'+name,check=False)
        try:
            result=json.loads(raw)
            if result.get('apkSha256')==binary:
                assert result['tested']==count and result['failed']==0 and not result.get('skipped'),result
                assert len(result['results'])==count and all(x['ok'] for x in result['results'])
                (QA/'device-files').mkdir(exist_ok=True)
                (QA/'device-files'/name).write_text(json.dumps(result,indent=2),encoding='utf8')
                print(name,count,'passed',flush=True);return
        except json.JSONDecodeError:pass
        time.sleep(2)
    raise TimeoutError(name)

if not args.resume_render:
    fresh(['qa.json','composition-qa.json'])
    shell('am start -n org.flippets.app/.PetActivity --ei qaPet 26 --ez qa true --ez qaComposition true')
collect('qa.json',176);collect('composition-qa.json',68)
for name,count,extra in [('ui-switch-qa.json',15,'qaSwitch'),('utility-qa.json',15,'qaUtilities')]:
    fresh([name]);shell(f'am start -n org.flippets.app/.PetActivity --ei qaPet 26 --ez {extra} true');collect(name,count)
print('274 current APK checks passed',binary,flush=True)
