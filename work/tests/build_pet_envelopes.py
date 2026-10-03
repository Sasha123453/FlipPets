"""Generate stable per-set render envelopes from actual emulator alpha samples.

Sampling bounds describe complete artwork, including decorative/effect layers.
The runtime additionally clips to a camera-safe viewport. No phone data involved.
"""
from pathlib import Path
import hashlib,json

root=Path(__file__).resolve().parents[2]
work=root/'work'
raw=json.loads((work/'review-check/envelope/raw.json').read_text(encoding='utf-8-sig'))
results=raw['results']
assert len(results)==116 and all('error' not in r and 1<=len(r['samples'])<=8 for r in results)
groups={}
for result in results:
    if 'nfc_' in result['path'] or 'pin_show' in result['path']:continue
    groups.setdefault(result['pet'],[]).append(result)
pets={}
for pet,scenes in sorted(groups.items()):
    bounds=[(min if i<2 else max)(r['bounds'][i] for r in scenes) for i in range(4)]
    pets[pet]=[round(max(0,min(1,v+(-.012 if i<2 else .012))),6) for i,v in enumerate(bounds)]
# Canonical subject focus is deliberately distinct from all-alpha artwork.
# Branches, table, ground, flowers and full-canvas reaction effects otherwise
# force tiny animals. Reviewed donor snapshots + stable per-family framing;
# the hard safe viewport clips decoration/gesture spill, never moves per frame.
focus={
    'bird-pandora':[.30,0,.84,1],
    'koala-archived-presets':[.40,.08,.96,.98],
    'roedeer-archived-presets':[.34,.10,.90,1],
    'seal-archived-presets':[.27,.12,.91,.98],
    'seal-pandora':[.27,.12,.91,.98],
    'capybara-archived-presets':[.43,0,.95,1],
    'sheep-archived-presets':[.30,0,.90,1],
    'sheep-pandora':[.30,0,.90,1],
    'otter-archived-presets':[.34,.10,.94,1],
    'q_carp-pandora':[.30,0,1,.97],
}
qa=json.loads((work/'qa-v03/device-files/qa.json').read_text())
videos={r['path']:[int(r['width']),int(r['height'])] for r in qa['results'] if r['path'].endswith('.mp4') and r['ok']}
metadata={'schema':2,'method':'Fixed per-family subject focus reviewed from donor snapshots, independent of decorative branches/ground/effects. Renderer owns placement and background blending; focus metadata does not assert continuous-motion camera clearance. All-artwork alpha union retained separately: 8 attempted samples per scene at half native resolution, alpha >= 8, 1.2% padding. Transparent sample frames omitted. NFC/payment effects use full-source fit. No per-frame focus changes.','pets':{**pets,**focus},'sampledArtworkEnvelopes':pets,'videos':videos}
(work/'app/assets/pet-envelopes.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report={'environment':'emulator-5554 standalone app_process, this app donor assets only; no phone UI/data','scope':'PAG loading and sampled alpha bounds, not continuous motion or physical camera clearance. Canonical subject focus is fixed renderer metadata, not an exact silhouette mask.','attemptedSamplesPerScene':8,'alphaThreshold':8,'tested':len(results),'failed':0,'sourceSha256':{r['path']:hashlib.sha256((work/'app/assets'/r['path']).read_bytes()).hexdigest() for r in results},'sampledArtworkEnvelopes':pets,'runtimeSubjectFocus':focus,'results':results}
(work/'qa-v03/pet-envelope-samples.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'PAG_scenes':len(results),'pet_envelopes':len(pets),'video_sizes':len(videos),'failed':0},indent=2))
