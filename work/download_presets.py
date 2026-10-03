"""Supplement the stock donor's older bundled pets with archived Xiaomi rear-screen presets.
Provenance is kept separate from the verified pandora OTA, never silently attributed to it.
"""
import pathlib,json,urllib.request,hashlib
r=pathlib.Path(__file__).resolve().parent
url='https://api.github.com/repos/NekoStash/REAREye-Preset-Resources/git/trees/main?recursive=1'
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FlipPets-research'}),timeout=60) as stream:tree=json.load(stream)
(r/'research'/'archived-preset-tree.json').write_text(json.dumps(tree,indent=2))
commit=tree['sha'];base=r/'original-resources'/'archived-presets';base.mkdir(parents=True,exist_ok=True)
for entry in tree['tree']:
    path=entry['path']
    if '/rearscreen/' not in path or not path.endswith(('.mrc','.mrm')):continue
    dest=base/('meta' if path.endswith('.mrm') else 'content')/path.rsplit('/',1)[-1];dest.parent.mkdir(exist_ok=True)
    source=f'https://raw.githubusercontent.com/NekoStash/REAREye-Preset-Resources/{commit}/{path}'
    if not dest.exists():
        with urllib.request.urlopen(source,timeout=120) as stream:dest.write_bytes(stream.read())
    assert dest.stat().st_size==entry['size']
    gitsha=hashlib.sha1(b'blob '+str(entry['size']).encode()+b'\0'+dest.read_bytes()).hexdigest();assert gitsha==entry['sha']
    print(dest.name,dest.stat().st_size,gitsha,flush=True)
(base/'provenance.json').write_text(json.dumps(dict(repository='https://github.com/NekoStash/REAREye-Preset-Resources',commit=commit,downloaded=[e for e in tree['tree'] if '/rearscreen/' in e['path'] and e['path'].endswith(('.mrc','.mrm'))]),indent=2))
