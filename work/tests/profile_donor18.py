"""Short real activity-player CPU/PSS samples; guarded software emulator only."""
from device_qa import *
import hashlib,json

guard()
binary=hashlib.sha256((ROOT.parent/'outputs/FlipPets.apk').read_bytes()).hexdigest()
installed=shell('pm path org.flippets.app').strip().removeprefix('package:')
assert shell('sha256sum '+installed).split()[0]==binary
hz=int(shell('getconf CLK_TCK').strip());rows=[]
def clock(pid):
    lines=shell(f'cat /proc/{pid}/stat; cat /proc/uptime').strip().splitlines()
    fields=lines[0].split(') ',1)[1].split()
    return (int(fields[11])+int(fields[12]))/hz,float(lines[1].split()[0])
def sample(label,duration):
    pid=shell('pidof org.flippets.app').strip();before=clock(pid);time.sleep(duration);after=clock(pid)
    mem=memory(pid);mem.pop('raw',None)
    row={'scenario':label,'durationSeconds':round(after[1]-before[1],2),'cpuPercentOneCore':round(100*(after[0]-before[0])/(after[1]-before[1]),2),**mem}
    rows.append(row);print(row,flush=True)
try:
    shell('settings put global overlay_display_devices ""');shell('wm size 1208x1392');shell('wm density 520')
    shell('am force-stop org.flippets.app');launch(30);time.sleep(2)
    sample('Butterfly carp18 visible animation/automatic transition',14)
    shell('input -d 0 keyevent KEYCODE_HOME');time.sleep(2)
    pid=shell('pidof org.flippets.app').strip()
    assert 'STAGE_STOP' in shell(f'logcat -d --pid={pid} -s FlipPets:I')
    sample('Carp hidden after observed STAGE_STOP',6)
    launch(31);time.sleep(3);sample('Vortex visible MediaPlayer background',6)
    shell('input -d 0 keyevent KEYCODE_HOME');time.sleep(2);sample('Vortex hidden',6)
    launch(32);time.sleep(3)
    pid=shell('pidof org.flippets.app').strip()
    assert 'PLAYBACK_END' in shell(f'logcat -d --pid={pid} -s FlipPets:I')
    sample('Card effect finite completed frame',6)
    report={'apkSha256':binary,'environment':'Standard Android16/API36 x86_64 emulator; software decoding and SwiftShader. CPU100% is one core; no hardware phone or battery-cost claim.','results':rows,'limitations':['Short6/14-second process samples; decoder/GPU processes and battery not measured.','Not a long memory-leak, heat or HyperOS lifecycle test.']}
    (QA/'resource-profile-v110.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
finally:
    shell('am force-stop org.flippets.app',check=False);shell('wm size 1224x2912',check=False)
