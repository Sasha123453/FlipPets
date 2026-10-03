import pathlib,subprocess,re,zipfile,json,hashlib,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent
listing=(ROOT/'research'/'pandora-product-list.txt').read_text(encoding='utf-8')
paths=re.findall(r'type=FILE.*?fsConfig=\[(/etc/precust_theme/theme/\.data/(?:content|meta)/rearscreen/[^ ]+) ',listing)
base=ROOT/'original-resources'/'pandora';base.mkdir(parents=True,exist_ok=True)
inventory=[]
for virtual in paths:
    folder='meta' if '/meta/' in virtual else 'content';dest=base/folder/virtual.rsplit('/',1)[-1];dest.parent.mkdir(exist_ok=True)
    with dest.open('wb') as stream:subprocess.run([str(ROOT/'tools'/'erofs'/'dump.erofs.exe'),'--cat','--path='+virtual,str(ROOT/'images'/'pandora'/'product.img')],stdout=stream,check=True)
    entry=dict(path=virtual,file=str(dest.relative_to(ROOT)),size=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
    if dest.suffix=='.mrc':
        with zipfile.ZipFile(dest) as z:
            assert z.testzip() is None
            names=z.namelist();entry['pagFiles']=[n for n in names if n.endswith('.pag')];entry['entries']=len(names)
            manifests=[n for n in names if n.endswith('manifest.xml')]
            if manifests:
                content=z.read(manifests[0]).decode('utf-8');entry['manifest']=manifests[0]
                try:
                    tree=ET.fromstring(content);variables={v.get('name'):v.get('expression','') for v in tree.findall('Var')};entry['variables']=variables
                except Exception as error:entry['xmlError']=str(error)
            entry['names']=names
    else:
        try:entry['meta']=json.loads(dest.read_text(encoding='utf-8'))
        except Exception:entry['metaText']=dest.read_text(encoding='utf-8',errors='replace')[:4096]
    inventory.append(entry)
(ROOT/'research'/'pandora-rearscreen-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
for entry in inventory:
    if 'pagFiles' in entry:print(pathlib.Path(entry['file']).name,'PAG=',len(entry['pagFiles']),'assets=',entry.get('variables',{}).get('assets'),'files=',entry['entries'],flush=True)
print('Extracted',len(inventory),'original files')
