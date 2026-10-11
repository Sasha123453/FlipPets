"""Verify stock import and decode original PAG pixels on explicit emulator-5554 only."""
from pathlib import Path
import argparse, hashlib, json, subprocess, uuid, zipfile
from PIL import Image, ImageDraw
from prepare_native_pet import ROOT, adb, sha


def verify_import():
    catalog = json.loads((ROOT/'work/app/assets/catalog.json').read_text(encoding='utf-8'))
    baseline = json.loads(subprocess.run(['git','show','HEAD:work/app/assets/catalog.json'],cwd=ROOT,check=True,capture_output=True,encoding='utf-8').stdout)
    assert len(baseline)>=33 and catalog[:33]==baseline[:33], 'Baseline metadata changed'
    canonical=json.dumps(catalog[:33],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    assert hashlib.sha256(canonical).hexdigest()=='cd49314203ab83a08263af0bf7fab17b714e267fdfbe526440cbf33d6f0a5b80', 'Reviewed baseline33 changed'
    report = json.loads((ROOT/'work/research/mixflip-pets-import.json').read_text(encoding='utf-8'))
    assert len(catalog)==39 and catalog[33:]==report['pets']
    assert len(report['assets'])==30
    for record in report['assets']:
        path = ROOT/'work/app'/record['resourcePath'] if 'resourcePath' in record else ROOT/'work/app/assets'/record['assetPath']
        assert sha(path)==record['sha256'], str(path)
        if 'bytes' in record: assert path.stat().st_size==record['bytes']
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--resume',action='store_true');parser.add_argument('--calibrated',action='store_true');parser.add_argument('--full',action='store_true');args=parser.parse_args()
    provenance=verify_import()
    assert adb('shell','getprop ro.kernel.qemu').strip()=='1'
    assert any(s in adb('shell','getprop ro.hardware') for s in ('ranchu','goldfish'))
    apk=ROOT/'outputs/FlipPets.apk'
    target=ROOT/'work/qa-final'/(('mixflip-calibrated-full' if args.full else 'mixflip-calibrated') if args.calibrated else 'mixflip-source');target.mkdir(parents=True,exist_ok=True)
    classes,dex,libs=(target/x for x in ('classes','dex','libs'))
    for p in (classes,dex,libs):p.mkdir(exist_ok=True)
    jdk=ROOT/'work/tools/jdk/jdk-17.0.20.1+1/bin';bt=ROOT/'work/tools/sdk/build-tools/android-16';android=ROOT/'work/tools/sdk/platforms/android-36/android.jar'
    source=ROOT/'work/tests/MixFlipPetProbe.java'
    subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8','-cp',str(android),'-d',str(classes),str(source)],check=True)
    subprocess.run([str(jdk/'java.exe'),'-cp',str(bt/'lib/d8.jar'),'com.android.tools.r8.D8','--lib',str(android),'--output',str(dex),str(classes/'MixFlipPetProbe.class')],check=True)
    with zipfile.ZipFile(apk) as z:
        for name in z.namelist():
            if name.startswith('lib/x86_64/') and name.endswith('.so'):(libs/Path(name).name).write_bytes(z.read(name))
    remote='/data/local/tmp/flippets-mixflip-'+uuid.uuid4().hex
    adb('shell','mkdir -p '+remote+'/lib')
    sources={}
    try:
        adb('push',apk,remote+'/base.apk',timeout=120);adb('push',dex/'classes.dex',remote+'/probe.dex')
        for p in libs.glob('*.so'):adb('push',p,remote+'/lib/'+p.name)
        for record in provenance['assets']:
            if 'assetPath' not in record:continue
            p=ROOT/'work/app/assets'/record['assetPath'];stem=p.parent.name.removeprefix('mixflip-')+'-'+p.stem.removeprefix('pag_');sources[stem]=p
        sources['charlie-0']=ROOT/'work/app/assets/pets/bird-pandora/pag_0.pag'
        if args.calibrated:
            candidate=ROOT/'outputs/native-pet/charlie-calibrated/candidate.pag'
            plan=json.loads(candidate.with_name('calibration.json').read_text(encoding='utf-8'))
            assert sha(candidate)==plan['candidateSha256'] and plan['originalCompositionPayloadsPreserved'] is True
            sources={'charlie-0':candidate}
        for stem,p in sources.items():adb('push',p,remote+'/'+stem+'.pag')
        report=json.loads((target/'decode-partial.json').read_text(encoding='utf-8')) if args.resume else {'clips':[]}
        completed={c['source']:c for c in report['clips']}
        for c in completed.values():
            assert c['sourceSha256']==sha(sources[c['source']]) and c['rendererApkSha256']==sha(apk)
            snapshot=target/('probe-'+c['probeSha256']+'.java');assert sha(snapshot)==c['probeSha256']
            for frame in c['frames']:assert sha(target/frame['png'])==frame['pngSha256']
        (target/('probe-'+sha(source)+'.java')).write_bytes(source.read_bytes())
        sheet=Image.new('RGB',(8*220,19*280),'#282b38');draw=ImageDraw.Draw(sheet)
        ordered=sorted(sources,key=lambda x:(not x.startswith('shuitun'),x))
        for row,stem in enumerate(ordered):
            if stem in completed:continue
            print('Decoding '+stem,flush=True)
            clip=None
            for sample in range(8):
                try:decoded=json.loads(adb('shell',f'CLASSPATH={remote}/probe.dex app_process /system/bin MixFlipPetProbe {remote}/base.apk {remote}/lib {remote} {stem} {sample}'+(' full' if args.full else ''),timeout=90))
                except subprocess.CalledProcessError as error:
                    (target/'decode-failure.txt').write_text(str(error)+'\n'+str(error.stdout)+'\n'+str(error.stderr),encoding='utf-8');raise
                assert len(decoded['clips'])==1 and len(decoded['clips'][0]['frames'])==1
                part=decoded['clips'][0]
                if clip is None:clip=part
                else:
                    assert {k:v for k,v in clip.items() if k!='frames'}=={k:v for k,v in part.items() if k!='frames'}
                    clip['frames'].extend(part['frames'])
            clip.update(probeSha256=sha(source),rendererApkSha256=sha(apk));report['clips'].append(clip)
            assert clip['sourceSha256']==sha(sources[clip['source']])
            assert len(clip['frames'])==8 and clip['durationUs']>0
            assert len({f['decodedRgbaSha256'] for f in clip['frames']})>=3, 'Motion missing '+clip['source']
            for col,frame in enumerate(clip['frames']):
                output=target/frame['png'];adb('pull',remote+'/'+frame['png'],output)
                frame['pngSha256']=sha(output)
                with Image.open(output) as im:
                    assert im.size==(clip['renderWidth'],clip['renderHeight'])
                    small=im.convert('RGBA');small.thumbnail((220,245));sheet.paste(small,(col*220,row*280+30),small)
                draw.text((col*220+4,row*280+4),clip['source']+' '+str(frame['progress']),fill='white')
            print(clip['source'],clip['width'],clip['height'],clip['durationUs'],flush=True)
            (target/'decode-partial.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        for row,clip in enumerate(report['clips']):
            for col,frame in enumerate(clip['frames']):
                with Image.open(target/frame['png']) as im:
                    small=im.convert('RGBA');small.thumbnail((220,245));sheet.paste(small,(col*220,row*280+30),small)
                draw.text((col*220+4,row*280+4),clip['source']+' '+str(frame['progress']),fill='white')
        sheet.save(target/'contact-sheet.jpg')
    finally:adb('shell','rm -rf '+remote)
    report.update(schemaVersion=1,rendererApkSha256=sha(apk),probeSha256=sha(source),provenanceSha256=sha(ROOT/'work/research/mixflip-pets-import.json'),baseline33Preserved=True,nativePlaybackProven=False,calibratedCandidate=args.calibrated,fullResolution=args.full,scope='Actual decode '+('at original resolution' if args.full else 'at max696px surface; source dimensions separate')+'. APK supplies libpag, not current-source APK QA or OEM playback proof')
    (target/'decode.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Verified import and '+str(len(report['clips']))+' clips / '+str(len(report['clips'])*8)+' decoded samples; no phone changes.')


if __name__=='__main__':main()
