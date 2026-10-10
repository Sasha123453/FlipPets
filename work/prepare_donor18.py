"""Import genuinely new hongkong rear-screen media without rebuilding the old catalogue.

Default is a read-only plan. Firmware/MRC/APK extraction stays ignored. --apply
copies only selected compatible artwork and records exact source hashes. This is
an adaptation of MAML evidence, not a claim of running Xiaomi's native engine.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import io
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

WORK = Path(__file__).resolve().parent
ASSETS = WORK / 'app/assets'
FAMILY = 'hongkong'
SOURCE = 'Xiaomi 18 Pro OS4.0.15.0.XFRCNXM product.img'
OFFICIAL = 'https://bigota.d.miui.com/OS4.0.15.0.XFRCNXM/hongkong-ota_full-OS4.0.15.0.XFRCNXM-user-17.0-6aad32ed35.zip'
CLASSIC = {'bird', 'seal', 'sheep', 'capybara', 'otter'}
MEDIA = {'.pag', '.mp4'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024**2), b''):
            digest.update(chunk)
    return digest.hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def safe_member(name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name:
        raise ValueError('Unsafe ZIP member: ' + name)
    return p


def extract_rearscreen(image, listing, destination):
    """Only named rear-screen theme files; no extraction into public assets."""
    paths = sorted(set(re.findall(r'fsConfig=\[(/etc/precust_theme/theme/\.data/[^ ]*/rearscreen/[^ ]+) ', listing.read_text(encoding='utf-8'))))
    found = []
    for virtual in paths:
        p = PurePosixPath(virtual)
        if p.suffix not in {'.mrc', '.mrm', '.png', '.webp', '.jpg', '.jpeg'}:
            continue
        folder = 'content' if '/content/' in virtual else 'meta' if '/meta/' in virtual else 'preview'
        target = destination / folder / p.name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('wb') as out:
            subprocess.run([str(WORK / 'tools/erofs/dump.erofs.exe'), '--cat', '--path=' + virtual, str(image)], stdout=out, check=True)
        found.append({'partitionPath': virtual, 'file': target.relative_to(destination).as_posix(), 'bytes': target.stat().st_size, 'sha256': sha(target.read_bytes())})
    dump(destination / 'extraction.json', found)
    return found


def media_sort(name):
    m = re.search(r'pag_(\d+)\.pag$', name)
    return (0, int(m.group(1))) if m else (1, name)


def playback(tree, family, media):
    """Fail closed on policy patterns not implemented by the present Java player."""
    views = tree.findall('.//PagView')
    loops = [v.get('loop', '-1') for v in views]
    complete = tree.find(".//Function[@name='onComplete']")
    evidence = {'pagLoops': loops, 'completeCommands': [dict(tag=x.tag, **x.attrib) for x in complete.iter()] if complete is not None else []}
    functions = {f.get('name'): f for f in tree.findall('.//Function')}
    def reaches_play(function, visited):
        if function is None:
            return True  # Unknown target cannot prove finite hold.
        name = function.get('name')
        if name in visited:
            return True  # Cyclic completion policy requires manual review.
        visited = visited | {name}
        if function.find(".//PagCommand[@command='play']") is not None:
            return True
        for command in function.findall('.//FunctionCommand'):
            if reaches_play(functions.get(command.get('target')), visited):
                return True
        return False
    if family in CLASSIC and complete is not None and complete.find(".//FrameRateCommand[@rate='0']") is not None and not reaches_play(complete, set()) and loops == ['1']:
        clips = [n for n in media if re.search(r'pag_\d+\.pag$', n)]
        return 'ambient', 'one cycle then hold until touch/resume', len(clips), evidence
    xml = ET.tostring(tree, encoding='unicode')
    if 'level_rule' in xml and 'pag_index' in xml and complete is not None and complete.find(".//FunctionCommand[@target='switchPag']") is not None:
        # State number equality is additionally compared to existing donor below.
        return 'reactive', 'reactive MAML: requires equivalent state mapping', None, evidence
    if views and all(x in ('0', '-1') for x in loops) and not any(n.endswith('.mp4') for n in media):
        return 'ambient', 'explicit looping PAG', None, evidence
    return None, 'unmapped MAML playback; retain in research only', None, evidence


def reactive_contract(tree):
    """Conservative control-flow equality, including actions and dependent constants.

    Matching a few state variable names misses changed event_index assignments,
    IfCommand ancestry, callbacks, delays and play/pause destinations. Keep full
    command trees, external events, triggered variables and callback links. This
    intentionally rejects uncertain equivalents rather than inventing a mapping.
    Layout-only attributes of PagView are left to the separate geometry review.
    """
    def canonical(node):
        return [node.tag, dict(sorted(node.attrib.items())), [canonical(child) for child in node]]

    roots = list(tree.findall('.//Function'))
    roots += [v for v in tree.findall('Var') if v.find('Trigger') is not None]
    roots += list(tree.findall('.//ExternalCommands'))
    roots += [v for v in tree.findall('.//FolmeConfig') if v.get('onComplete')]
    references = {'pag_index', 'level_rule', 'level_event'}
    for root in roots:
        for node in root.iter():
            references.update(re.findall(r'[#@]([A-Za-z_][A-Za-z0-9_]*)', ' '.join(node.attrib.values())))
            if node.tag == 'VariableCommand' and node.get('name'):
                references.add(node.get('name'))
    view_contract = []
    for view in tree.findall('.//PagView'):
        attributes = {k: v for k, v in view.attrib.items() if k not in {'w', 'h', 'x', 'y', 'align', 'alignV', 'layerType', 'scaleMode'}}
        view_contract.append([attributes, [canonical(c) for c in view]])
        references.update(re.findall(r'[#@]([A-Za-z_][A-Za-z0-9_]*)', ' '.join(attributes.values())))
    declarations = {v.get('name'): v for v in tree.findall('Var') if v.get('name')}
    # Follow intermediate variables/arrays as well as directly referenced values.
    while True:
        previous = set(references)
        for name in previous & declarations.keys():
            references.update(re.findall(r'[#@]([A-Za-z_][A-Za-z0-9_]*)', ' '.join(declarations[name].attrib.values())))
        if references == previous:
            break
    return {'schemaVersion': 2,
            'controlRoots': [canonical(node) for node in roots],
            'stateBindings': [canonical(declarations[name]) for name in sorted(references & declarations.keys())],
            'pagActionsAndSources': view_contract}


def native_preview(archive, meta, base):
    candidates = []
    for key in ('builtInThumbnails', 'builtInPreviews'):
        value = meta.get(key, {})
        for names in value.values() if isinstance(value, dict) else []:
            candidates.extend(names if isinstance(names, list) else [])
    for name in candidates:
        if name in archive.namelist():
            return archive.read(name), 'MRC:' + name
        for p in sorted(base.rglob(PurePosixPath(name).name)):
            if p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}:
                return p.read_bytes(), 'partition-preview:' + p.relative_to(base).as_posix()
    return None, None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=WORK / 'extracted/hongkong/rearscreen')
    parser.add_argument('--image', type=Path)
    parser.add_argument('--listing', type=Path)
    parser.add_argument('--proof', type=Path, default=WORK / 'images/hongkong/product.verified-extraction.json')
    parser.add_argument('--select', action='append', default=[], help='MRC UUID to include; repeatable')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--allow-missing-thumbnail', action='store_true', help='Only while a real frame renderer is preparing thumbnails')
    args = parser.parse_args()
    if bool(args.image) != bool(args.listing):
        parser.error('--image and --listing must be supplied together')
    proof = json.loads(args.proof.read_text(encoding='utf-8')) if args.proof.exists() else None
    if args.image:
        if not proof or proof.get('device') != FAMILY or not proof.get('partitionHashVerified'):
            raise ValueError('Verified hongkong partition evidence required before extraction')
        if args.image.stat().st_size != proof.get('partitionBytes') or file_sha(args.image) != proof.get('partitionSha256'):
            raise ValueError('Supplied image differs from the verified partition')
        extract_rearscreen(args.image, args.listing, args.source_root)
    originals = sorted((args.source_root / 'content').glob('*.mrc'))
    if not originals:
        raise ValueError('No extracted rear-screen MRC files: ' + str(args.source_root))
    catalog = json.loads((ASSETS / 'catalog.json').read_text(encoding='utf-8'))
    existing = {}
    signatures = {}
    for pet in catalog:
        signature = []
        for path in pet.get('clips', {}).values():
            data = (ASSETS / path).read_bytes()
            digest = sha(data)
            existing.setdefault(digest, path)
            signature.append(digest)
        if signature:
            signatures.setdefault(tuple(sorted(set(signature))), []).append(pet['id'])
    baseline = set(existing)
    plan = []
    staged = []
    for mrc in originals:
        meta_path = args.source_root / 'meta' / (mrc.stem + '.mrm')
        meta = json.loads(meta_path.read_text(encoding='utf-8')) if meta_path.exists() else {}
        with zipfile.ZipFile(mrc) as z:
            if z.testzip() is not None:
                raise ValueError('Corrupt MRC: ' + mrc.name)
            for member in z.namelist():
                safe_member(member)
            if 'manifest.xml' not in z.namelist():
                plan.append({'originalFile': mrc.name, 'decision': 'no-root-manifest'})
                continue
            manifest = z.read('manifest.xml')
            tree = ET.fromstring(manifest)
            variables = {v.get('name'): v.get('expression', '').strip("'") for v in tree.findall('Var')}
            family = variables.get('assets', mrc.stem)
            identity = re.sub(r'[^a-zA-Z0-9_-]', '-', family) + '-hongkong'
            media = sorted([n for n in z.namelist() if PurePosixPath(n).suffix in MEDIA], key=media_sort)
            if not media:
                plan.append({'originalFile': mrc.name, 'decision': 'no-media'})
                continue
            hashes = {n: sha(z.read(n)) for n in media}
            signature = tuple(sorted(set(hashes.values())))
            kind, policy, count, policy_evidence = playback(tree, family, media)
            entry = {'id': identity, 'originalFile': mrc.name, 'originalSha256': sha(mrc.read_bytes()), 'manifestSha256': sha(manifest), 'family': family, 'media': [{'member': n, 'sha256': hashes[n], 'reusesAsset': existing.get(hashes[n])} for n in media], 'uniqueMediaInMrc': len(signature), 'newMediaVsBaseline': len(set(signature) - baseline), 'playbackPolicy': policy, 'playbackEvidence': policy_evidence}
            if signature in signatures:
                entry.update(decision='exact-media-set-alias', aliases=signatures[signature])
                plan.append(entry)
                continue
            if set(signature) <= baseline:
                entry.update(decision='all-media-already-present',
                             note='Subset/rearrangement of existing bytes; MAML may differ, no new animation SHA')
                plan.append(entry)
                continue
            if not kind:
                entry['decision'] = 'policy-needs-renderer-support'
                plan.append(entry)
                continue
            if kind == 'reactive':
                numbered = sorted(int(re.search(r'pag_(\d+)\.pag$', n).group(1)) for n in media if re.search(r'pag_(\d+)\.pag$', n))
                other = [PurePosixPath(n).name for n in media if not re.search(r'pag_(\d+)\.pag$', n)]
                entry['numberedReactiveStates'] = numbered
                entry['additionalMediaNames'] = other
                if numbered != list(range(16)) or any(n != 'nfc_pin_show.pag' for n in other):
                    entry['decision'] = 'reactive-state-files-unmapped'
                    plan.append(entry)
                    continue
                comparisons = []
                candidate_contract = reactive_contract(tree)
                entry['reactiveContractSha256'] = sha(json.dumps(candidate_contract, ensure_ascii=False, sort_keys=True).encode('utf-8'))
                entry['reactiveContractSchema'] = 2
                for old in catalog:
                    if old.get('kind') != 'reactive':
                        continue
                    source = WORK / 'research/compositions' / (('pandora-' if 'pandora' in old['id'] else 'archived-presets-') + Path(old.get('originalFile', '')).stem + '.xml')
                    if source.exists() and reactive_contract(ET.parse(source).getroot()) == candidate_contract:
                        comparisons.append(old['id'])
                if not comparisons:
                    entry['decision'] = 'reactive-state-mapping-unverified'
                    plan.append(entry)
                    continue
                entry['equivalentReactiveMapping'] = comparisons
            if args.select and mrc.stem not in args.select:
                entry['decision'] = 'not-selected'
                plan.append(entry)
                continue
            if any(p['id'] == identity for p in catalog + [x[0] for x in staged]):
                identity += '-' + mrc.stem[:8]
                entry['id'] = identity
            clips = {}
            payload = {}
            for i, member in enumerate(media):
                matched = re.search(r'pag_(\d+)\.pag$', member)
                index = matched.group(1) if matched else str(i)
                if index in clips:
                    raise ValueError('Ambiguous scene index in ' + mrc.name)
                digest = hashes[member]
                target = existing.get(digest)
                if not target:
                    target = 'pets/' + identity + '/' + PurePosixPath(member).name
                    if target in payload and payload[target] != z.read(member):
                        raise ValueError('Basename collision in ' + mrc.name)
                    payload[target] = z.read(member)
                    existing[digest] = target
                clips[index] = target
            # Support native images/fonts used by the already implemented renderer.
            for member in z.namelist():
                p = PurePosixPath(member)
                if p.name in {'bg.webp', 'bg.png', 'backgroud.png', 'c700_regular.ttf'} or (p.suffix == '.png' and ('/desk/' in member or p.name.startswith('temp_'))):
                    relative = member[member.index('/desk/') + 1:] if '/desk/' in member else ('bg.png' if p.name == 'backgroud.png' else p.name)
                    target = 'pets/' + identity + '/' + relative
                    payload[target] = z.read(member)
            name = meta.get('titles', {}).get('en_US', meta.get('titles', {}).get('fallback', family))
            pet = {'id': identity, 'name': name + ' · 18 Pro', 'kind': kind, 'clips': clips, 'extra': [], 'gradientFrom': variables.get('bgGradientFrom', variables.get('bgColor', '#444E70')), 'gradientTo': variables.get('bgGradientTo', variables.get('bgColor', '#647D98')), 'timeColor': variables.get('timeColor', '#DBFF5A'), 'source': SOURCE, 'originalFile': mrc.name, 'originalSha256': entry['originalSha256']}
            if count is not None:
                pet['touchSceneCount'] = count
            preview, preview_source = native_preview(z, meta, args.source_root)
            entry.update(decision='import-compatible', thumbnailSource=preview_source, thumbnailSourceSha256=sha(preview) if preview else None, assetHashes={k: sha(v) for k, v in payload.items()}, reusedMediaAssetPaths=[p for p in clips.values() if p not in payload])
            staged.append((pet, payload, manifest, preview, entry))
            signatures[signature] = [identity]
            plan.append(entry)
    discovered = {m['sha256'] for e in plan for m in e.get('media', [])} - baseline
    report = {'schemaVersion': 1, 'device': FAMILY, 'officialArchiveUrl': OFFICIAL, 'partitionEvidence': proof, 'limits': 'Partial OTA, not a verified flashable whole archive. Dedup is byte-level; native MAML runtime/phone lifecycle is not transplanted.', 'baselineCatalogueEntries': len(catalog), 'baselineUniqueMedia': len(baseline), 'discoveredNewUniqueMedia': len(discovered), 'discoveredNewMediaReferences': sum(e.get('newMediaVsBaseline', 0) for e in plan), 'newCatalogueEntries': len(staged), 'newUniqueMedia': len(set(existing) - baseline), 'mediaReferencesAfterImport': sum(len(p.get('clips', {})) for p in catalog) + sum(len(p['clips']) for p, *_ in staged), 'decisions': plan}
    dump(args.source_root / 'import-plan.json', report)
    if args.apply:
        if not proof or not proof.get('partitionHashVerified') or proof.get('device') != FAMILY or proof.get('officialArchiveUrl') != OFFICIAL:
            raise ValueError('Exact official hongkong partition proof required for public import')
        thumbnails = {}
        for pet, payload, manifest, preview, entry in staged:
            if preview is None and not args.allow_missing_thumbnail:
                raise ValueError('Real thumbnail missing for ' + pet['id'])
            for relative, data in payload.items():
                target = ASSETS / relative
                if target.exists() and target.read_bytes() != data:
                    raise ValueError('Would overwrite different asset: ' + relative)
            if preview:
                from PIL import Image
                image = Image.open(io.BytesIO(preview)).convert('RGBA')
                image.thumbnail((384, 384), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                image.save(buffer, 'WEBP', quality=88)
                thumbnails[pet['id']] = buffer.getvalue()
                entry['thumbnailGeneratedSha256'] = sha(buffer.getvalue())
        for pet, payload, manifest, preview, entry in staged:
            for relative, data in payload.items():
                target = ASSETS / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() and target.read_bytes() != data:
                    raise ValueError('Would overwrite different asset: ' + relative)
                target.write_bytes(data)
            research = WORK / 'research/hongkong-maml' / (Path(pet['originalFile']).stem + '.xml')
            research.parent.mkdir(parents=True, exist_ok=True)
            research.write_bytes(manifest)
            if preview:
                (ASSETS / 'thumbs' / (pet['id'] + '.webp')).write_bytes(thumbnails[pet['id']])
            catalog.append(pet)
        # Do not sort/remove old entries: stable preferences and unrelated adaptations.
        dump(ASSETS / 'catalog.json', catalog)
        dump(WORK / 'research/hongkong-resource-provenance.json', report)
    print(json.dumps({k: report[k] for k in ('baselineCatalogueEntries', 'baselineUniqueMedia', 'discoveredNewUniqueMedia', 'discoveredNewMediaReferences', 'newCatalogueEntries', 'newUniqueMedia', 'mediaReferencesAfterImport')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
