"""Prepare a separate native-size candidate, never stage, Apply or replace an existing bundle."""
import json
from pathlib import Path
from PIL import Image
from prepare_native_composite import compose, tags
from prepare_native_template import ROOT, verify_bundle, sha


def main():
    proof,original,_=verify_bundle()
    decode=json.loads((ROOT/'work/qa-final/mixflip-source/decode-partial.json').read_text(encoding='utf-8'))
    capy=next(c for c in decode['clips'] if c['source']=='shuitun-0')
    imported=json.loads((ROOT/'work/research/mixflip-pets-import.json').read_text(encoding='utf-8'))
    reference=next(a for a in imported['assets'] if a.get('assetPath')=='pets/mixflip-shuitun/pag_0.pag')
    assert capy['sourceSha256']==reference['sha256'] and (capy['width'],capy['height'])==(1208,1392)
    frame=capy['frames'][0];assert frame['progress']==0 and frame['stableSnapshots']>=3
    ratio=capy['width']/capy['renderWidth'];left,top,right,bottom=[v*ratio for v in frame['alphaBounds']]
    # Fixed visual guide around Charlie's body/head/feet, excluding the branch and flowers.
    # First-pose guide only: movement/physical cameras still require separate review.
    body=[365,112,812,574]
    scale=min((right-left)/(body[2]-body[0]),(bottom-top)/(body[3]-body[1]))
    x=right-body[2]*scale;y=bottom-body[3]*scale
    # Runtime and native export consume the exact same placement; the guide is
    # reviewed once, independent of frame-to-frame alpha and decoration.
    layout=dict(schemaVersion=1,canvas=[1208,1392],layouts={'bird-pandora':dict(
        sourceCanvas=[976,596],referenceSourceSha256=sha(original),scale=scale,x=x,y=y,
        subjectRight=right,subjectBottom=bottom)})
    (ROOT/'work/app/assets/native-pet-layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
    background=(ROOT/'work/app/assets/pets/bird-pandora/bg.webp').read_bytes()
    candidate=compose(original,background,(scale,x,y))
    original_compositions=[p for c,p in tags(original,9) if c==2]
    assert all(p in [v for c,v in tags(candidate,9) if c==2] for p in original_compositions)
    target=ROOT/'outputs/native-pet/charlie-calibrated';target.mkdir(parents=True,exist_ok=True)
    (target/'candidate.pag').write_bytes(candidate)
    plan=dict(schemaVersion=1,sourcePagSha256=sha(original),referencePagSha256=reference['sha256'],reference='Stock capybara action1 first decoded pose',referenceSourceBounds=[left,top,right,bottom],charlieSubjectGuide=body,guideBasis='Manually inspected original first pose; excludes branch/flowers; fixed across animation',transform=dict(scale=scale,x=x,y=y),candidateSha256=sha(candidate),originalCompositionPayloadsPreserved=True,nativePlaybackProven=False,nativeUpdateProven=False,physicalCameraClearanceProven=False,sourceCrestRepaired=False,scope='Local calibration candidate only. Does not change installed Charlie or old authorized Apply bundle.')
    (target/'calibration.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # A schematic guide for review, not the actual candidate poster or decode proof.
    bg=Image.open(ROOT/'work/app/assets/pets/bird-pandora/bg.webp').convert('RGBA').resize((1208,1392))
    bird=Image.open(ROOT/'work/qa-final/native-pet-source/frame-00.png').convert('RGBA')
    bird=bird.resize((round(bird.width*scale),round(bird.height*scale)))
    bg.alpha_composite(bird,(round(x),round(y)));bg.save(target/'first-pose-schematic.png')
    print(json.dumps(plan,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
