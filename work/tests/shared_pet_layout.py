"""Declarative app/native geometry registry. No phone contact or native installer."""
from pathlib import Path
import hashlib,json,math,re

ROOT=Path(__file__).resolve().parents[2]
ASSETS=ROOT/'work/app/assets'
REGISTRY=ASSETS/'native-pet-layout.json'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_registry(value):
    if value.get('schemaVersion')!=1 or value.get('canvas')!=[1208,1392] or not isinstance(value.get('layouts'),dict):
        raise ValueError('Unknown shared layout schema/canvas')
    catalog={p['id']:p for p in json.loads((ASSETS/'catalog.json').read_text(encoding='utf-8'))}
    for pet_id,layout in value['layouts'].items():
        pet=catalog.get(pet_id)
        if pet is None or pet_id.startswith('mixflip-') or pet_id=='system-effects' or pet.get('kind') in ('video','composition') or pet.get('renderRole','pet')!='pet':
            raise ValueError('Only catalogue PAG pets may have an AI composition profile; stock geometry remains OEM-owned')
        paths=pet.get('clips',{})
        if not paths or any(not p.endswith('.pag') for p in paths.values()):raise ValueError('PAG scenes required')
        canvas=layout.get('sourceCanvas')
        if not isinstance(canvas,list) or len(canvas)!=2 or any(type(v)!=int or not 1<=v<=4096 for v in canvas):raise ValueError('Bounded source canvas required')
        if layout.get('referenceSourceSha256')!=digest(ASSETS/paths['0']):raise ValueError('Reference source changed')
        fields=('scale','x','y','subjectRight','subjectBottom')
        if any(type(layout.get(k)) not in (int,float) or not math.isfinite(layout[k]) for k in fields):raise ValueError('Finite transform required')
        if not 0<layout['scale']<=8 or abs(layout['x'])>4096 or abs(layout['y'])>4096 or not 0<layout['subjectRight']<=1208 or not 0<layout['subjectBottom']<=1392:
            raise ValueError('Out-of-bounds transform/subject anchor')
    return value

def propose(pet_id,decoded,guide,reference=(110,366,1140,1392),decoded_folder=None):
    catalog={p['id']:p for p in json.loads((ASSETS/'catalog.json').read_text(encoding='utf-8'))}
    pet=catalog.get(pet_id)
    if pet is None:raise ValueError('Choose an existing catalogue pet')
    by_sha={c['sourceSha256']:c for c in decoded['clips']}
    scenes=[]
    for key,path in pet.get('clips',{}).items():
        source=digest(ASSETS/path);clip=by_sha.get(source)
        if clip is None or len({f['decodedRgbaSha256'] for f in clip['frames']})<3:raise ValueError('Every scene needs actual source-bound moving decode evidence')
        if decoded_folder is None:raise ValueError('Actual sampled PNG files are required')
        from PIL import Image
        folder=Path(decoded_folder).resolve()
        for frame in clip['frames']:
            name=frame.get('png','')
            if not re.fullmatch(r'[A-Za-z0-9_-]+\.png',name) or frame.get('stableSnapshots',0)<3:raise ValueError('Unknown/unready sampled frame')
            image_path=folder/name
            if digest(image_path)!=frame['pngSha256']:raise ValueError('Sampled PNG differs')
            with Image.open(image_path) as image:
                if image.size!=(clip['renderWidth'],clip['renderHeight']) or hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest()!=frame['decodedRgbaSha256']:
                    raise ValueError('Sampled decoded pixels differ')
        scenes.append(dict(scene=key,assetPath=path,sha256=source,width=clip['width'],height=clip['height']))
    canvases={(s['width'],s['height']) for s in scenes}
    if len(canvases)!=1:raise ValueError('Mixed source canvases need separate reviewed scene profiles')
    width,height=next(iter(canvases))
    if len(guide)!=4 or any(not math.isfinite(v) for v in guide):raise ValueError('Fixed body guide required')
    left,top,right,bottom=guide
    if not 0<=left<right<=width or not 0<=top<bottom<=height:raise ValueError('Guide must be inside the decoded source canvas')
    rl,rt,rr,rb=reference
    if not 0<=rl<rr<=1208 or not 0<=rt<rb<=1392:raise ValueError('Reference body must be inside the cover')
    scale=min((rr-rl)/(right-left),(rb-rt)/(bottom-top))
    entry=dict(sourceCanvas=[width,height],referenceSourceSha256=digest(ASSETS/pet['clips']['0']),
        scale=scale,x=rr-right*scale,y=rb-bottom*scale,subjectRight=rr,subjectBottom=rb,
        subjectGuide=list(guide),sourceScenes=scenes)
    validate_registry(dict(schemaVersion=1,canvas=[1208,1392],layouts={pet_id:entry}))
    return entry

def main():
    import argparse,uuid
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pet');p.add_argument('--decode-report',type=Path)
    p.add_argument('--subject-guide',nargs=4,type=float,metavar=('LEFT','TOP','RIGHT','BOTTOM'))
    args=p.parse_args()
    validate_registry(json.loads(REGISTRY.read_text(encoding='utf-8')))
    if args.pet is None:
        print('Shared geometry registry validated; no phone state changed.');return
    if args.decode_report is None or args.subject_guide is None:p.error('A real decoded report and reviewed body guide are required')
    entry=propose(args.pet,json.loads(args.decode_report.read_text(encoding='utf-8')),args.subject_guide,decoded_folder=args.decode_report.parent)
    folder=ROOT/'outputs/native-pet/layout-drafts';folder.mkdir(parents=True,exist_ok=True)
    target=folder/(uuid.uuid4().hex+'.json')
    target.write_text(json.dumps(dict(petId=args.pet,layout=entry,nativeApplyAllowed=False,
        status='Draft only: review sampled pixels/full motion and native format compatibility before adding to registry.'),indent=2)+'\n',encoding='utf-8')
    print(target)

if __name__=='__main__':main()
