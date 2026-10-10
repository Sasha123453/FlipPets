"""Decode selected verified donor18 PAGs using our real renderer on emulator5554."""
from device_qa import *
import json,hashlib,zipfile,subprocess

guard();assert 'ranchu' in shell('getprop ro.hardware')
target=ROOT/'review-check/hongkong-probe';target.mkdir(parents=True,exist_ok=True)
base=ROOT/'extracted/hongkong/rearscreen/content'
apk=ROOT.parent/'outputs/FlipPets.apk';binary=hashlib.sha256(apk.read_bytes()).hexdigest()
proof=json.loads((ROOT/'images/hongkong/product.verified-extraction.json').read_text())
assert proof['partitionHashVerified'] and proof['device']=='hongkong'
catalog=[];hashes={};sources={}
assets=target/'assets.zip'
with zipfile.ZipFile(assets,'w',zipfile.ZIP_STORED) as out:
    with zipfile.ZipFile(base/'e23e7933-0bd7-4d6e-9165-aae505e389cc.mrc') as mrc:
        for variant in ('456x298','488x298'):
            clips={}
            names=sorted(n for n in mrc.namelist() if f'pag_{variant}/' in n and n.endswith('.pag'))
            assert len(names)==4,names
            for i,n in enumerate(names):
                data=mrc.read(n);path=f'donor18/carp-{variant}/pag_{i}.pag';clips[str(i)]=path
                out.writestr('assets/'+path,data);hashes[path]=hashlib.sha256(data).hexdigest();sources[path]=n
            catalog.append({'id':'carp-'+variant,'kind':'ambient','clips':clips})
    apk_files=list((ROOT/'extracted/hongkong').rglob('subscreencenter.apk'));assert len(apk_files)==1
    with zipfile.ZipFile(apk_files[0]) as donor:
        data=donor.read('assets/pin_show.pag');path='donor18/assistant/pin_show.pag'
        out.writestr('assets/'+path,data);hashes[path]=hashlib.sha256(data).hexdigest();sources[path]='APK:assets/pin_show.pag'
        catalog.append({'id':'assistant','kind':'ambient','clips':{'0':path}})
    out.writestr('assets/catalog.json',json.dumps(catalog))
jdk=ROOT/'tools/jdk/jdk-17.0.20.1+1/bin';bt=ROOT/'tools/sdk/build-tools/android-16'
android=ROOT/'tools/sdk/platforms/android-36/android.jar'
classes=target/'classes';dex=target/'dex';classes.mkdir(exist_ok=True);dex.mkdir(exist_ok=True)
subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8','-cp',str(android),'-d',str(classes),str(ROOT/'tests/AssetEnvelopeProbe.java')],check=True)
subprocess.run([str(jdk/'java.exe'),'-cp',str(bt/'lib/d8.jar'),'com.android.tools.r8.D8','--lib',str(android),'--output',str(dex),str(classes/'AssetEnvelopeProbe.class')],check=True)
libs=target/'libs';libs.mkdir(exist_ok=True)
with zipfile.ZipFile(apk) as z:
    for n in z.namelist():
        if n.startswith('lib/x86_64/') and n.endswith('.so'):(libs/pathlib.Path(n).name).write_bytes(z.read(n))
remote='/data/local/tmp/flip-hongkong-probe'
shell('mkdir -p '+remote+'/lib')
adb('push',apk,remote+'/base.apk');adb('push',assets,remote+'/assets.zip')
adb('push',dex/'classes.dex',remote+'/probe.dex')
for lib in libs.glob('*.so'):adb('push',lib,remote+'/lib/'+lib.name)
proc=subprocess.run([ADB,'-s','emulator-5554','shell',f'CLASSPATH={remote}/probe.dex app_process /system/bin AssetEnvelopeProbe {remote}/base.apk {remote}/lib {remote}/assets.zip'],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=240)
(target/'stderr.txt').write_text(proc.stderr,encoding='utf8')
assert proc.returncode==0,proc.stderr[-2000:]
report=json.loads(proc.stdout);assert len(report['results'])==9
for row in report['results']:
    assert 'error' not in row and row['width']>0 and row['height']>0 and row['durationUs']>0 and len(row['samples'])>=2,row
    row.update(sourceSha256=hashes[row['path']],sourceMember=sources[row['path']],distinctFrameHashes=len({x[5] for x in row['samples']}))
    assert row['distinctFrameHashes']>=2,row
    name=f"source-{row['pet']}-{row['clip']}-donor18.png"
    adb('pull',f"/data/local/tmp/flip-pets-envelope-{row['pet']}-{row['clip']}.png",QA/name)
    row['screenshot']=name
report.update(environment='Guarded Android16 emulator5554; real libpag decoder, raw donor artwork at half resolution; not HyperOS/native layout/physical camera validation',rendererApkSha256=binary,partitionEvidence=proof,tested=9,failed=0)
(QA/'donor18-pag-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps([{k:r[k] for k in ('pet','clip','width','height','durationUs','distinctFrameHashes')} for r in report['results']],indent=2),flush=True)
