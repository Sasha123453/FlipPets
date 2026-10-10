"""Actual donor video decode on the guarded emulator, no app/device setting changes."""
from device_qa import *
import json,hashlib,zipfile,subprocess
guard()
target=ROOT/'review-check/hongkong-video';target.mkdir(parents=True,exist_ok=True)
mrc=ROOT/'extracted/hongkong/rearscreen/content/119f090b-b625-4b3e-9ffd-107927c360c6.mrc'
with zipfile.ZipFile(mrc) as source:data=source.read('assets/hongkong/bg.mp4')
video=target/'vortex.mp4';video.write_bytes(data)
jdk=ROOT/'tools/jdk/jdk-17.0.20.1+1/bin';bt=ROOT/'tools/sdk/build-tools/android-16';android=ROOT/'tools/sdk/platforms/android-36/android.jar'
classes=target/'classes';dex=target/'dex';classes.mkdir(exist_ok=True);dex.mkdir(exist_ok=True)
subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8','-cp',str(android),'-d',str(classes),str(ROOT/'tests/MediaSourceProbe.java')],check=True)
subprocess.run([str(jdk/'java.exe'),'-cp',str(bt/'lib/d8.jar'),'com.android.tools.r8.D8','--lib',str(android),'--output',str(dex),*map(str,classes.glob('*.class'))],check=True)
adb('push',video,'/data/local/tmp/flip-vortex.mp4');adb('push',dex/'classes.dex','/data/local/tmp/flip-video-probe.dex')
raw=shell('CLASSPATH=/data/local/tmp/flip-video-probe.dex app_process /system/bin MediaSourceProbe /data/local/tmp/flip-vortex.mp4')
report=json.loads(raw);assert int(report['durationMs'])>0 and len(report['frames'])==2 and len({r['pixelHash'] for r in report['frames']})==2
for row in report['frames']:
    assert row['width']>0 and row['height']>0
    name=f"source-vortex-{row['timeUs']}-donor18.png";adb('pull',f"/data/local/tmp/flip-vortex-{row['timeUs']}.png",QA/name);row['screenshot']=name
report.update(environment='Guarded Android16 emulator5554; actual MediaMetadataRetriever frames, not HyperOS layout or continuous player/battery validation',sourceSha256=hashlib.sha256(data).hexdigest(),sourceMember='assets/hongkong/bg.mp4',sourceMrcSha256=hashlib.sha256(mrc.read_bytes()).hexdigest(),tested=2,failed=0)
(QA/'donor18-video-probe.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report,indent=2))
