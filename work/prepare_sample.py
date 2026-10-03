"""Temporary renderer fixture from a public original Xiaomi MRC. Replace after donor-ROM extraction."""
import pathlib,json,shutil,hashlib
r=pathlib.Path(__file__).resolve().parent
source=r/'research'/'sample-Roe'/'assets'/'roedeer'/'pag'
dest=r/'app'/'assets'/'pets'/'roe';dest.mkdir(parents=True,exist_ok=True)
clips={}
for f in source.glob('pag_*.pag'):
    shutil.copy2(f,dest/f.name);clips[f.stem[4:]]='pets/roe/'+f.name
catalog=[dict(name='Roe · оленёнок',id='roe',gradientFrom='#E6A543',gradientTo='#EBC054',clips=clips,source='NekoStash/REAREye-Preset-Resources; donor-ROM attribution pending')]
(r/'app'/'assets'/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
