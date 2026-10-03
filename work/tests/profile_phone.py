"""Read-only, explicitly targeted MIX Flip app CPU/PSS sampler. No UI or settings changes."""
import argparse, hashlib, json, pathlib, re, statistics, subprocess, time

parser=argparse.ArgumentParser()
parser.add_argument('--serial',required=True)
parser.add_argument('--label',required=True)
parser.add_argument('--seconds',type=float,default=12)
parser.add_argument('--output',required=True)
args=parser.parse_args()
if not 4<=args.seconds<=60: parser.error('Use a sample interval between 4 and 60 seconds')
ROOT=pathlib.Path(__file__).resolve().parents[1]
def shell(command):
    return subprocess.run(['C:/platform-tools/adb.exe','-s',args.serial,'shell',command],check=True,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=15).stdout
assert shell('getprop ro.product.device').strip()=='ruyi','Only a physical MIX Flip is supported'
pid=shell('pidof org.flippets.app').strip()
assert pid.isdecimal(),'Expected one own application process'
hz=int(shell('getconf CLK_TCK').strip())
def clock():
    lines=shell(f'cat /proc/{pid}/stat; cat /proc/uptime').strip().splitlines()
    fields=lines[0].split(') ',1)[1].split()
    return (int(fields[11])+int(fields[12]))/hz,float(lines[1].split()[0])
before=clock(); samples=[]
for _ in range(4):
    time.sleep(args.seconds/4);now=clock()
    samples.append(100*(now[0]-before[0])/(now[1]-before[1]));before=now
raw=shell('dumpsys meminfo -s '+pid)
mem=re.search(r'TOTAL PSS:\s*(\d+)\s+TOTAL RSS:\s*(\d+)',raw)
assert mem,'Missing own process memory information'
report=dict(label=args.label,apkSha256=hashlib.sha256((ROOT.parent/'outputs/FlipPets.apk').read_bytes()).hexdigest(),
    durationSeconds=args.seconds,cpuPercentOneCore=round(statistics.mean(samples),2),
    cpuSamples=[round(v,2) for v in samples],pssKiB=int(mem[1]),rssKiB=int(mem[2]),
    scope='Application process only; 100% CPU is one core. Does not measure battery or system decoder/GPU cost.')
path=pathlib.Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report),flush=True)
