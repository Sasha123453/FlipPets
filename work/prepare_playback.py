"""Attach playback metadata from original MAML and measured original clip durations."""
import json, pathlib, xml.etree.ElementTree as ET
ROOT = pathlib.Path(__file__).resolve().parent
catalog_path = ROOT / 'app/assets/catalog.json'
catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
qa = json.loads((ROOT / 'qa-v03/device-files/qa.json').read_text(encoding='utf-8'))
durations = {r['path']: (r['durationUs'] + 999) // 1000 for r in qa['results'] if 'durationUs' in r}
inventory = json.loads((ROOT / 'research/compositions/inventory.json').read_text(encoding='utf-8'))
evidence = []
for pet in catalog:
    pet['durationMs'] = {i: durations[p] for i, p in pet.get('clips', {}).items() if p in durations}
    ident = pet['id']
    classic = ident.startswith(('bird-', 'seal-', 'sheep-', 'capybara-', 'otter-'))
    if not classic and pet['kind'] != 'reactive':
        continue
    source = next(x for x in inventory if x['id'].endswith(pathlib.Path(pet['originalFile']).stem))
    path = ROOT / 'research/compositions' / (source['id'] + '.xml')
    tree = ET.parse(path)
    complete = tree.find(".//Function[@name='onComplete']")
    assert complete is not None
    if classic:
        assert complete.find(".//FrameRateCommand[@rate='0']") is not None
        assert complete.find(".//PagCommand[@command='play']") is None
        counts = {'bird': 12, 'seal': 11, 'sheep': 12, 'capybara': 4, 'otter': 4}
        pet['touchSceneCount'] = counts[ident.split('-')[0]]
    else:
        assert complete.find(".//FunctionCommand[@target='switchPag']") is not None
        assert tree.find(".//Variable[@key='animator_duration_scale']") is not None
    evidence.append(dict(id=ident, source=str(path.relative_to(ROOT)).replace('\\', '/'),
        nativePolicy='one cycle then hold until touch/resume' if classic else
        'replay ordinary state while active; finite interaction then return after 1000 ms',
        inferenceLimit='MAML behavior; not a complete observation of 17 Pro system screen service'))
catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(ROOT/'research/native-playback-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Original playback policy verified:', len(evidence), 'presets')
