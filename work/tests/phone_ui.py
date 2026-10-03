"""UI helpers for an explicitly selected MIX Flip. Dumps remain in ignored phone-qa."""
from pathlib import Path
import re, subprocess, time, xml.etree.ElementTree as ET

class Phone:
    def __init__(self,serial):
        self.serial=serial
        self.folder=Path(__file__).resolve().parents[1]/'phone-qa'
        self.folder.mkdir(exist_ok=True)
        assert self.shell('getprop ro.product.device').strip()=='ruyi'
    def adb(self,*args):
        return subprocess.run(['C:/platform-tools/adb.exe','-s',self.serial,*map(str,args)],
            capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30,check=True).stdout
    def shell(self,command):return self.adb('shell',command)
    def ui(self):
        self.shell('uiautomator dump /sdcard/flip-test-ui.xml')
        self.adb('pull','/sdcard/flip-test-ui.xml',self.folder/'last-ui.xml')
        return ET.parse(self.folder/'last-ui.xml')
    def tap(self,text,partial=False,description=False):
        key='content-desc' if description else 'text'
        nodes=[n for n in self.ui().iter('node') if text in n.get(key,'') if partial or text==n.get(key,'')]
        assert nodes,'Missing element: '+text
        node=next((n for n in nodes if n.get('clickable')=='true'),nodes[0])
        x,y,x2,y2=map(int,re.findall(r'\d+',node.get('bounds')))
        assert x2>x and y2>y
        self.shell(f'input -d 0 tap {(x+x2)//2} {(y+y2)//2}')
        time.sleep(.5)
    def text(self):return [(n.get('text'),n.get('bounds')) for n in self.ui().iter('node') if n.get('text')]
    def main(self):self.shell('am start -W --display 0 --activity-clear-top --activity-single-top -n org.flippets.app/.MainActivity');time.sleep(1)
