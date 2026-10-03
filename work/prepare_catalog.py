import pathlib,json,zipfile,re,xml.etree.ElementTree as ET,hashlib,shutil
r=pathlib.Path(__file__).resolve().parent;assets=r/'app'/'assets';assets.mkdir(exist_ok=True)
catalog=[];provenance=[];seen=set()
families=[('archived-presets','Archive of Xiaomi presets'),('pandora','Xiaomi 17 Pro OS3.0.319.0.WBLCNXM product.img')]
for family,label in families:
    base=r/'original-resources'/family
    for file in (base/'content').glob('*.mrc'):
        meta=json.loads((base/'meta'/(file.stem+'.mrm')).read_text(encoding='utf-8'));name=meta.get('titles',{}).get('en_US',meta.get('titles',{}).get('fallback',file.stem))
        with zipfile.ZipFile(file) as z:
            assert z.testzip() is None
            if 'manifest.xml' not in z.namelist():continue
            xml=z.read('manifest.xml').decode('utf-8');tree=ET.fromstring(xml);vars={v.get('name'):v.get('expression','').strip("'") for v in tree.findall('Var')}
            pag=[n for n in z.namelist() if n.endswith('.pag')];videos=[n for n in z.namelist() if n.endswith('.mp4')]
            if not pag and not videos:continue
            identifier=vars.get('assets',file.stem)
            identity=identifier+'-'+family
            signature=tuple(sorted(hashlib.sha256(z.read(n)).hexdigest() for n in pag+videos))
            if signature in seen:continue
            seen.add(signature)
            dest=assets/'pets'/identity;dest.mkdir(parents=True,exist_ok=True)
            clips={};extra=[];kind='reactive' if 'level_rule' in xml and 'pag_index' in xml else 'ambient'
            pag.sort(key=lambda n:(0,int(re.search(r'pag_(\d+)\.pag$',n).group(1))) if re.search(r'pag_(\d+)\.pag$',n) else (1,n))
            for n in pag:
                match=re.search(r'pag_(\d+)\.pag$',n);index=match.group(1) if match else str(len(clips));target=dest/pathlib.PurePosixPath(n).name;target.write_bytes(z.read(n));clips[index]=target.relative_to(assets).as_posix()
            if videos:
                kind='video';priority=['idle_0.mp4','idle_1.mp4','idle_2.mp4']
                videos.sort(key=lambda n:(priority.index(pathlib.PurePosixPath(n).name) if pathlib.PurePosixPath(n).name in priority else 100,n))
                for i,n in enumerate(videos):
                    target=dest/pathlib.PurePosixPath(n).name;target.write_bytes(z.read(n));clips[str(i)]=target.relative_to(assets).as_posix();extra.append(dict(index=i,label=target.stem))
            for n in z.namelist():
                pure=pathlib.PurePosixPath(n)
                if pure.name.startswith('temp_') and pure.suffix=='.png' and '/desk/' not in n and '/aod/' not in n: (dest/pure.name).write_bytes(z.read(n))
                if pure.name=='c700_regular.ttf':(dest/pure.name).write_bytes(z.read(n))
                if pure.name=='bg.webp':(dest/pure.name).write_bytes(z.read(n))
                if pure.name=='bg.png':(dest/pure.name).write_bytes(z.read(n))
                if pure.name=='backgroud.png':(dest/'bg.png').write_bytes(z.read(n))
                if '/desk/' in n and pure.suffix=='.png':
                    relative=n[n.index('/desk/')+1:];p=dest/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
            p=dict(id=identity,name=name,kind=kind,clips=clips,extra=extra,gradientFrom=vars.get('bgGradientFrom',vars.get('bgColor','#444E70')),gradientTo=vars.get('bgGradientTo',vars.get('bgColor','#647D98')),timeColor=vars.get('timeColor','#DBFF5A'),source=label,originalFile=file.name,originalSha256=hashlib.sha256(file.read_bytes()).hexdigest())
            catalog.append(p);provenance.append(dict(**p,manifestVariables=vars))
apk=r/'jars'/'pandora-subscreencenter.apk'
with zipfile.ZipFile(apk) as z:
    clips={};dest=assets/'pets'/'system-effects';dest.mkdir(exist_ok=True)
    for i,n in enumerate(['assets/pin_show_pandora.pag','assets/pin_show_popsicle.pag']):
        target=dest/pathlib.PurePosixPath(n).name;target.write_bytes(z.read(n));clips[str(i)]=target.relative_to(assets).as_posix()
    p=dict(id='system-effects',name='Системные эффекты',kind='ambient',clips=clips,extra=[],gradientFrom='#444E70',gradientTo='#647D98',timeColor='#DBFF5A',source='Xiaomi 17 Pro SubScreenCenter APK',originalFile=apk.name,originalSha256=hashlib.sha256(apk.read_bytes()).hexdigest());catalog.append(p);provenance.append(p)
for p in catalog:
    if p['source'].startswith('Xiaomi 17 Pro OS') and sum(x['name']==p['name'] for x in catalog)>1:p['name']+=' · классический'
catalog.sort(key=lambda p:({'reactive':0,'ambient':1,'video':2}[p['kind']],p['name']))
(assets/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
(r/'research'/'portable-resource-provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
for pet in catalog:print(pet['name'],pet['kind'],len(pet['clips']),pet['source'])
print('TOTAL',len(catalog),'sets',sum(len(p['clips']) for p in catalog),'clips')
