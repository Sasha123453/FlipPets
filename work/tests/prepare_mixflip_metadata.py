"""Derive fixed stock metadata and thumbnails from verified decoded samples, no phone access."""
import json,hashlib
from pathlib import Path
from PIL import Image
from run_mixflip_source_qa import verify_import
from prepare_native_pet import ROOT,sha


def main():
    imported=verify_import();target=ROOT/'work/qa-final/mixflip-source';report=json.loads((target/'decode.json').read_text(encoding='utf-8'))
    assert len(report['clips'])==19 and report['baseline33Preserved'] is True
    clips={c['source']:c for c in report['clips']};metadata={};evidence=[]
    for pet in imported['pets']:
        stem=pet['id'].removeprefix('mixflip-');scenes=[]
        for index in range(3):
            clip=clips[stem+'-'+str(index)];assert clip['sourceSha256']==sha(ROOT/'work/app/assets'/pet['clips'][str(index)])
            assert len({f['decodedRgbaSha256'] for f in clip['frames']})>=3
            for frame in clip['frames']:assert sha(target/frame['png'])==frame['pngSha256']
            bounds=[f['alphaBounds'] for f in clip['frames'] if f['alphaBounds'] is not None]
            union=[min(b[0] for b in bounds)/clip['renderWidth'],min(b[1] for b in bounds)/clip['renderHeight'],max(b[2] for b in bounds)/clip['renderWidth'],max(b[3] for b in bounds)/clip['renderHeight']]
            scenes.append(dict(index=index,sourceSha256=clip['sourceSha256'],width=clip['width'],height=clip['height'],durationUs=clip['durationUs'],sampledSubjectEnvelope=union,emptyFirstFrame=clip['frames'][0].get('empty',False),emptyLastFrame=clip['frames'][-1].get('empty',False)))
            evidence.append(dict(id=pet['id'],**scenes[-1],decodedSamples=8,distinctSampleHashes=len({f['decodedRgbaSha256'] for f in clip['frames']}),probeSha256=clip['probeSha256'],rendererApkSha256=clip['rendererApkSha256']))
        metadata[pet['id']]=dict(nativePetType=pet['nativePetType'],playback='finite-tap-cycle',rotationTable='PetsPagView 0/180, special action10 retained',scenes=scenes)
        clip=clips[stem+'-0'];frame=next(f for f in clip['frames'] if f['alphaBounds'] is not None)
        original=Image.open(target/frame['png']).convert('RGBA');scale=max(320/original.width,369/original.height)
        original=original.resize((round(original.width*scale),round(original.height*scale)),Image.Resampling.LANCZOS)
        thumb=Image.new('RGBA',(320,369),pet['gradientFrom']);thumb.alpha_composite(original,((320-original.width)//2,(369-original.height)//2))
        thumb.convert('RGB').save(ROOT/'work/app/assets/thumbs'/(pet['id']+'.webp'),quality=90)
    (ROOT/'work/app/assets/mixflip-pets.json').write_text(json.dumps(dict(schemaVersion=1,pets=metadata,rights=imported['rights']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    public=dict(schemaVersion=1,scope=report['scope'],sourceImportSha256=sha(ROOT/'work/research/mixflip-pets-import.json'),baseline33Preserved=True,stockClips=18,stockSamples=144,charlieSourceSamples=8,nativePlaybackProven=False,physicalCameraClearanceProven=False,clips=evidence,thumbnails={pet['id']:sha(ROOT/'work/app/assets/thumbs'/(pet['id']+'.webp')) for pet in imported['pets']})
    (ROOT/'work/research/mixflip-pets-decoding.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('6 source thumbnails and finite scene metadata; 144 stock samples, 8 Charlie samples.')


if __name__=='__main__':main()
