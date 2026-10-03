"""Append distinct offline MAML adaptations, retaining original assets and provenance.
Run prepare_catalog.py first. Colors/layouts are options, not duplicate catalogue entries.
"""
import pathlib,json,zipfile,hashlib,xml.etree.ElementTree as E
r=pathlib.Path(__file__).resolve().parent;assets=r/'app/assets'
cat=json.loads((assets/'catalog.json').read_text(encoding='utf-8'))
cat=[p for p in cat if p.get('kind')!='composition']
inventory=json.loads((r/'research/compositions/inventory.json').read_text(encoding='utf-8'))
selected={
'09cb4aa8-8e8d-4f2c-a6cd-2a7e2648d790':('Силикон · фиолетовый','analog','purple'),
'5cb92fb9-812b-4c3a-ac75-ec203034f03a':('Силикон · зелёный','analog','green'),
'c5b24c5e-716a-445d-bca9-9bc078b50199':('Силикон · красный','analog','red'),
'cc8f8283-037f-4608-a0fd-b4c0a9a7eb34':('Градиент · часы','analog','blue'),
'c9ad6b5a-1462-460d-8033-b6c407db1290':('Волокно дракона · часы','dragon','black'),
'96af4ce9-72b5-451d-aba8-bc3282aeaa34':('Stretch · упругие часы','stretch','blue'),
'3adb17eb-f46b-4270-8a26-670c1e71d08f':('Шагомер','steps',''),
'0714c784-0cc9-440b-8c69-d959adc989db':('Подпись','signature',''),
'a1f032b7-aee9-4af5-a614-c71ee8432c73':('Новогодняя бумага','paper',''),
'26d6b38e-6e11-4573-b449-29bcf5ad1477':('Кинокалендарь · локальный','calendar',''),
'8668591f-a278-4c5f-a5e0-e75539b2168f':('Своя фотография','photo',''),
}
proof=[]
for uid,(name,renderer,color) in selected.items():
 p=r/'original-resources/pandora/content'/f'{uid}.mrc';dest=assets/'compositions'/uid;dest.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  files={}
  for n in z.namelist():
   if not n.endswith(('.png','.webp','.ttf','.otf')):continue
   target=dest/n;target.parent.mkdir(parents=True,exist_ok=True);raw=z.read(n);target.write_bytes(raw);files[n]=hashlib.sha256(raw).hexdigest()
  (dest/'manifest.xml').write_bytes(z.read('manifest.xml'))
 item=dict(id=uid,name=name,kind='composition',renderer=renderer,assetRoot='compositions/'+uid+'/',defaultColor=color,clips={},extra=[],gradientFrom='#182432',gradientTo='#31495D',source='Xiaomi 17 Pro OS3.0.319.0.WBLCNXM product.img',originalFile=p.name,originalSha256=hashlib.sha256(p.read_bytes()).hexdigest())
 cat.append(item);proof.append(dict(**item,assets=files,behavior='Offline Canvas adaptation of original MAML, not Xiaomi runtime'))
(assets/'catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2),encoding='utf-8')
(r/'research/composition-provenance.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
print(len(cat),'sets;',len(proof),'new compositions;',sum(len(x['assets']) for x in proof),'original image assets')
