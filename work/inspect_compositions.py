import pathlib,json,zipfile,xml.etree.ElementTree as E,collections
r=pathlib.Path(__file__).resolve().parent;dest=r/'research/compositions';dest.mkdir(exist_ok=True)
rows=[]
for family in ['pandora','archived-presets']:
    for p in (r/'original-resources'/family/'content').glob('*.mrc'):
        with zipfile.ZipFile(p) as z:
            meta=json.loads((p.parent.parent/'meta'/p.with_suffix('.mrm').name).read_text(encoding='utf-8'));name=meta.get('titles',{}).get('en_US',meta.get('titles',{}).get('fallback',p.stem))
            if 'manifest.xml' not in z.namelist():continue
            raw=z.read('manifest.xml');tree=E.fromstring(raw)
            label=family+'-'+p.stem;(dest/(label+'.xml')).write_bytes(raw)
            media=[n for n in z.namelist() if n.endswith(('.png','.webp','.jpg','.ttf','.gif'))]
            row=dict(id=label,name=name,tags=dict(collections.Counter(t.tag for t in tree.iter())),media=media,clips=[n for n in z.namelist() if n.endswith(('.pag','.mp4'))])
            rows.append(row)
(dest/'inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
for row in rows:
    if not row['clips']:print(json.dumps(row,ensure_ascii=True))
