"""Process CPU/PSS measurements on the x86_64 emulator, not battery estimates."""
from device_qa import *
import json, hashlib, statistics, sys
guard()
duration=float(sys.argv[1]) if len(sys.argv)>1 else 12
hz=int(shell('getconf CLK_TCK').strip())
def clock(pid):
    raw=shell(f'cat /proc/{pid}/stat; cat /proc/uptime')
    lines=raw.strip().splitlines(); fields=lines[0].split(') ',1)[1].split()
    return (int(fields[11])+int(fields[12]))/hz, float(lines[1].split()[0])
results=[]
def sample(label,pid=None):
    pid=pid or shell('pidof org.flippets.app').strip()
    if not pid: results.append(dict(scenario=label,processAbsent=True));return
    before=clock(pid);samples=[]
    for _ in range(4):
        time.sleep(duration/4);now=clock(pid);samples.append(100*(now[0]-before[0])/(now[1]-before[1]));before=now
    mem=memory(pid);(QA/('mem-'+re.sub(r'[^a-z0-9]+','-',label.lower())+'.txt')).write_text(mem.pop('raw'),encoding='utf-8')
    row=dict(scenario=label,pid=int(pid),durationSeconds=duration,cpuPercentOneCore=round(statistics.mean(samples),2),cpuSamples=[round(x,2) for x in samples],**mem)
    results.append(row);print(json.dumps(row),flush=True)
shell('am force-stop org.flippets.app')
shell('settings put global overlay_display_devices ""')
for index,label in [(0,'PAG Bubbles visible'),(19,'Analog clock visible'),(26,'Signature static visible'),(12,'MP4 cartoon visible')]:
    launch(index);time.sleep(4);sample(label)
    shell('am start --display 0 -a android.settings.SETTINGS');time.sleep(3);sample(label+' hidden')
    shell('input -d 0 keyevent KEYCODE_BACK');time.sleep(1)
    shell('input -d 0 keyevent KEYCODE_BACK');time.sleep(1)
launch(0);time.sleep(3);baseline=memory();baseline.pop('raw',None)
cycles=[]
for i in range(20):
    shell('input -d 0 keyevent KEYCODE_BACK');launch([19,26,12,6,0][i%5]);time.sleep(.8)
    if i in (4,9,14,19):
        m=memory();m.pop('raw',None);cycles.append(dict(cycle=i+1,**m));print(json.dumps(cycles[-1]),flush=True)
shell('am start --display 0 -a android.settings.SETTINGS');time.sleep(5);sample('After 20 switches hidden')
for process in ['shizuku_server','org.flippets.app:controller']:
    pid=shell('pidof '+process,check=False).strip()
    if pid: sample(process+' idle',pid)
report=dict(apkSha256=hashlib.sha256((ROOT.parent/'outputs/FlipPets.apk').read_bytes()).hexdigest(),environment='Android 16 API 36 x86_64 emulator, two virtual CPU cores, SwiftShader GPU, PAG software decoding; 100% CPU is one core. No physical MIX Flip or battery measurement.',clockTicksPerSecond=hz,results=results,cycleBaseline=baseline,memoryCycles=cycles)
(QA/'resource-profile.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
