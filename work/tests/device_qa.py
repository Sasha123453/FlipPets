"""Utilities restricted to our emulator. Never select a physical phone implicitly."""
import subprocess, pathlib, time, xml.etree.ElementTree as ET, re
ADB='C:/platform-tools/adb.exe'
ROOT=pathlib.Path(__file__).resolve().parents[1]
QA=ROOT/'qa-v03'; QA.mkdir(exist_ok=True)
def adb(*args,check=True):
    p=subprocess.run([ADB,'-s','emulator-5554',*map(str,args)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    if check and p.returncode: raise RuntimeError(p.stdout+p.stderr)
    return p.stdout
def shell(command,check=True): return adb('shell',command,check=check)
def guard(): assert shell('getprop ro.kernel.qemu').strip()=='1'
def ui(name='ui'):
    shell('uiautomator dump /sdcard/flip-ui.xml')
    adb('pull','/sdcard/flip-ui.xml',QA/(name+'.xml'))
    return ET.parse(QA/(name+'.xml')).getroot()
def tap_text(text,description=False,partial=False):
    tree=ui(); key='content-desc' if description else 'text'
    nodes=[n for n in tree.iter('node') if (text in n.get(key,'') if partial else n.get(key)==text)]
    assert nodes,'UI element absent: '+text
    x,y,x2,y2=map(int,re.findall(r'\d+',nodes[0].get('bounds')))
    shell(f'input -d 0 tap {(x+x2)//2} {(y+y2)//2}')
    time.sleep(.7)
def screenshot(name):
    time.sleep(.8);shell('screencap -p /sdcard/flip-screen.png');adb('pull','/sdcard/flip-screen.png',QA/(name+'.png'))
def launch(pet,display=0,cover=False):
    return shell(f'am start --display {display} -n org.flippets.app/.PetActivity -f 0x18000000 --ei qaPet {pet}'+(' --ez coverSession true' if cover else ''))
def memory(pid=None):
    raw=shell('dumpsys meminfo -s '+(str(pid) if pid else 'org.flippets.app'))
    match=re.search(r'TOTAL PSS:\s*(\d+)\s+TOTAL RSS:\s*(\d+)',raw)
    return dict(pssKiB=int(match[1]),rssKiB=int(match[2]),raw=raw) if match else dict(raw=raw)
