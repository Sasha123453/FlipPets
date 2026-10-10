"""Exact selected 18 Pro port, plan-only unless the parent authorizes --apply.

Original 1.0 catalogue IDs/defaults stay intact. This is source-based adaptation,
not a native MAML-engine transplant. Thumbnails must be actual decoded frames.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import zipfile

WORK = Path(__file__).resolve().parent
ASSETS = WORK / 'app/assets'
EXTRACTED = WORK / 'extracted/hongkong'
BASELINE_SHA256 = 'c55781ef5fe4f119ede203c1eeb96ddb2b8ddc16ce7bbe8f82d0844190eaf8cb'
PRODUCT_SHA256 = 'f63831fadeddfd4b52407ff22e02ac8d17cce6ceb474c951c4fc13c214d09f63'
SYSTEM_EXT_SHA256 = 'bd32916b4010f90ebaa077ef8685b9c6a84b57e0416e4645f6bae3bf072e239d'
APK_SHA256 = '45bfcd3ecae8f7264b083248e88ad2c80bdfde39c9d511ce51b1f62f2649b55c'
CARP_MRC = 'e23e7933-0bd7-4d6e-9165-aae505e389cc.mrc'
CARP_SHA256 = '592059fff600673e02089cc0fc1d7c47cc97ce1310b010d562a0fea1a042ee11'
VORTEX_MRC = '119f090b-b625-4b3e-9ffd-107927c360c6.mrc'
VORTEX_SHA256 = 'c6a45971b17954aae19ff0c230ad75ebf5b5c44743c4dc40d365f7dd0975c138'
SOURCE = 'Xiaomi 18 Pro OS4.0.15.0.XFRCNXM verified product.img'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def verify_partition(name, expected):
    path = WORK / 'images/hongkong' / (name + '.verified-extraction.json')
    proof = json.loads(path.read_text(encoding='utf-8'))
    if proof.get('device') != 'hongkong' or proof.get('partition') != name or proof.get('partitionSha256') != expected or not proof.get('partitionHashVerified') or not proof.get('operationHashesCheckedByPayloadDumper'):
        raise ValueError('Wrong/unverified partition source: ' + name)
    return proof


def original_archive(path, expected):
    if sha(path.read_bytes()) != expected:
        raise ValueError('Source archive SHA mismatch: ' + path.name)
    archive = zipfile.ZipFile(path)
    if archive.testzip() is not None:
        archive.close()
        raise ValueError('Source ZIP CRC mismatch: ' + path.name)
    return archive


def common(identity, name, kind, render_role, source_file, source_sha):
    return {'id': identity, 'name': name, 'kind': kind, 'renderRole': render_role,
            'clips': {}, 'extra': [], 'gradientFrom': '#000000', 'gradientTo': '#000000',
            'timeColor': '#AC2D2E', 'source': SOURCE, 'originalFile': source_file,
            'originalSha256': source_sha}


def prepare():
    product = verify_partition('product', PRODUCT_SHA256)
    system = verify_partition('system_ext', SYSTEM_EXT_SHA256)
    entries, files, origins, manifests = [], {}, [], {}

    def copy(archive, member, target, source_file):
        data = archive.read(member)
        if target in files and files[target] != data:
            raise ValueError('Duplicate destination with different bytes: ' + target)
        files[target] = data
        origins.append({'assetPath': target, 'sourceArchive': source_file, 'sourceMember': member,
                        'bytes': len(data), 'sha256': sha(data), 'byteIdentical': True})

    carp = common('butterfly-carp-hongkong', 'Butterfly carp · 18 Pro', 'ambient', 'pet', CARP_MRC, CARP_SHA256)
    carp.update(clockStyle='carp', playbackPolicy='carp-sequence',
                transitionThresholds={str(i): value for i, value in enumerate([689/719, 689/719, 570/600, 566/596])},
                fadeOutMs=500, fadeDelayMs=100, fadeInMs=300,
                carpSceneCount=4, carpSelectionAttempts=10,
                nativePauseProgress=1, nativeAodPolicy='finish then hold',
                sourceLayoutVariant='pag_456x298', backgroundColor='#000000')
    with original_archive(EXTRACTED / 'rearscreen/content' / CARP_MRC, CARP_SHA256) as archive:
        for index in range(4):
            target = 'pets/' + carp['id'] + '/pag_' + str(index) + '.pag'
            copy(archive, 'assets/pag_456x298/pag_' + str(index) + '.pag', target, CARP_MRC)
            carp['clips'][str(index)] = target
        for member in archive.namelist():
            if member.startswith('assets/digits/desk/') and member.endswith('.png'):
                copy(archive, member, 'pets/' + carp['id'] + '/' + member.removeprefix('assets/digits/'), CARP_MRC)
        manifests['hongkong-maml/' + Path(CARP_MRC).stem + '.xml'] = archive.read('manifest.xml')
    digits = [x['sourceMember'] for x in origins if '/desk/' in x['assetPath']]
    expected_digits = ['assets/digits/desk/' + folder + '/temp_' + str(i) + '.png'
                       for folder, count in [('hour_0', 3), ('hour_1', 10), ('minute_0', 6), ('minute_1', 10)] for i in range(count)]
    if sorted(digits) != sorted(expected_digits):
        raise ValueError('Expected all 29 real HH:mm clock digits; do not fabricate 11 unused glyphs')
    entries.append(carp)

    vortex = common('vortex-hongkong', 'Vortex · анимированный фон', 'video', 'background', VORTEX_MRC, VORTEX_SHA256)
    vortex.update(playbackPolicy='loop-visible', nativeVideoLoop=True, nativeScaleMode=2,
                  adaptationNote='Original animated background; native analogue clock/date/battery layers are not included')
    with original_archive(EXTRACTED / 'rearscreen/content' / VORTEX_MRC, VORTEX_SHA256) as archive:
        target = 'pets/' + vortex['id'] + '/bg.mp4'
        copy(archive, 'assets/hongkong/bg.mp4', target, VORTEX_MRC)
        vortex['clips']['0'] = target
        manifests['hongkong-maml/' + Path(VORTEX_MRC).stem + '.xml'] = archive.read('manifest.xml')
    entries.append(vortex)

    pin = common('pin-hongkong', 'Эффект карточки · 18 Pro', 'finite-preview', 'effect', 'subscreencenter.apk', APK_SHA256)
    pin.update(playbackPolicy='finite-preview', manualOnly=True, nativeRepeatCount=1,
               effectDeadlineMs=3000, nativeScaleMode=1,
               adaptationNote='Manual preview of SmartAssistantPanel card enter animation; no NFC or automatic pin integration')
    with original_archive(EXTRACTED / 'subscreencenter.apk', APK_SHA256) as archive:
        target = 'pets/' + pin['id'] + '/pin_show.pag'
        copy(archive, 'assets/pin_show.pag', target, 'subscreencenter.apk')
        pin['clips']['0'] = target
    entries.append(pin)
    return entries, files, origins, manifests, [product, system]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--thumbnail-carp', type=Path)
    parser.add_argument('--thumbnail-vortex', type=Path)
    parser.add_argument('--thumbnail-pin', type=Path)
    parser.add_argument('--pag-probe', type=Path, default=WORK / 'qa-v03/donor18-pag-probe.json')
    parser.add_argument('--video-probe', type=Path, help='Real decoded Vortex source-frame evidence JSON')
    args = parser.parse_args()
    baseline_bytes = (ASSETS / 'catalog.json').read_bytes()
    if sha(baseline_bytes) != BASELINE_SHA256:
        raise ValueError('Catalogue differs from reviewed 1.0 baseline; review/rebase script before apply')
    baseline = json.loads(baseline_bytes)
    if len(baseline) != 30:
        raise ValueError('Expected intact 30-entry 1.0 catalogue')
    entries, files, origins, manifests, proofs = prepare()
    old_hashes = {sha((ASSETS / path).read_bytes()) for pet in baseline for path in pet.get('clips', {}).values()}
    selected_media = [x for x in origins if x['assetPath'].endswith(('.pag', '.mp4'))]
    if len(selected_media) != 6 or len({x['sha256'] for x in selected_media}) != 6 or any(x['sha256'] in old_hashes for x in selected_media):
        raise ValueError('Selected media are not six distinct additions to baseline')
    pag_probe = json.loads(args.pag_probe.read_text(encoding='utf-8'))
    if pag_probe.get('failed') != 0 or pag_probe.get('tested') != 9 or pag_probe.get('partitionEvidence', {}).get('partitionSha256') != PRODUCT_SHA256:
        raise ValueError('Current successful original-source PAG probe required')
    rows = pag_probe['results']
    for entry in [entries[0], entries[2]]:
        entry['durationMs'] = {}
        for index, asset in entry['clips'].items():
            expected = sha(files[asset])
            row = next((r for r in rows if r.get('sourceSha256') == expected), None)
            if row is None or row.get('error') or not row.get('durationUs'):
                raise ValueError('Source media absent/failed in actual probe: ' + asset)
            entry['durationMs'][index] = (row['durationUs'] + 999) // 1000
    thumbnail_files = {}
    thumbnail_evidence = []
    for entry, path in zip(entries, [args.thumbnail_carp, args.thumbnail_vortex, args.thumbnail_pin]):
        if path is None:
            if args.apply:
                raise ValueError('Actual rendered-frame thumbnail required: ' + entry['id'])
            continue
        from PIL import Image
        data = path.read_bytes()
        source_asset = entry['clips']['0']
        source_sha = sha(files[source_asset])
        if entry['kind'] == 'video':
            if args.video_probe is None:
                raise ValueError('Vortex thumbnail requires --video-probe actual decode evidence')
            source_probe_path = args.video_probe
            source_probe = json.loads(source_probe_path.read_text(encoding='utf-8'))
            if source_probe.get('sourceSha256') != source_sha or source_probe.get('failed') != 0 or source_probe.get('sourceMrcSha256') != VORTEX_SHA256:
                raise ValueError('Video thumbnail/source evidence mismatch')
            video_row = next((r for r in source_probe.get('frames', []) if path.resolve() == (source_probe_path.parent / r.get('screenshot', '')).resolve()), None)
            if video_row is None:
                raise ValueError('Vortex thumbnail must be the actual video-probe frame')
            if 'thumbnailSha256' in source_probe and source_probe['thumbnailSha256'] != sha(data):
                raise ValueError('Video thumbnail hash mismatch')
            entry['durationMs'] = {'0': int(source_probe['durationMs'])}
        else:
            source_probe_path = args.pag_probe
            source_probe = pag_probe
            row = next((r for r in rows if r.get('sourceSha256') == source_sha), None)
            if row is None or path.resolve() != (args.pag_probe.parent / row['screenshot']).resolve():
                raise ValueError('PAG thumbnail must be the actual current source-probe screenshot')
        image = Image.open(io.BytesIO(data)).convert('RGBA')
        original_size = list(image.size)
        expected_size = [video_row['width'], video_row['height']] if entry['kind'] == 'video' else [max(1, row['width']//2), max(1, row['height']//2)]
        if original_size != expected_size:
            raise ValueError('Actual probe thumbnail dimensions mismatch')
        image.thumbnail((384, 384), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, 'WEBP', quality=88)
        target = 'thumbs/' + entry['id'] + '.webp'
        thumbnail_files[target] = buffer.getvalue()
        thumbnail_evidence.append({'pet': entry['id'], 'assetPath': target, 'inputSha256': sha(data),
                                   'inputSize': original_size, 'sha256': sha(buffer.getvalue()),
                                   'sourceMediaSha256': source_sha,
                                   'sourceProbeSha256': sha(source_probe_path.read_bytes()),
                                   'rendererApkSha256': source_probe.get('rendererApkSha256'),
                                   'sourceRequirement': 'Caller-provided actual decoded original donor media frame; not a mockup'})
    if args.apply and len(thumbnail_evidence) != 3:
        raise ValueError('Three actual thumbnails required')
    all_files = {**files, **thumbnail_files}
    for relative, data in all_files.items():
        target = ASSETS / relative
        if target.exists() and target.read_bytes() != data:
            raise ValueError('Would overwrite unrelated asset: ' + relative)
    report = {'schemaVersion': 1, 'baselineCatalogueSha256': BASELINE_SHA256,
              'baselineCatalogueCanonicalSha256': sha(canonical(baseline)),
              'baselineEntriesUnchanged': True, 'baselineEntryCount': 30,
              'addedEntries': len(entries), 'addedMediaReferences': 6, 'addedUniqueMediaSha256': 6,
              'partitionEvidence': proofs, 'entries': entries, 'assets': origins, 'thumbnails': thumbnail_evidence,
              'mamlSha256': {path: sha(data) for path, data in manifests.items()},
              'nativePinEvidence': 'Verified SubscreenCenter SmartAssistantPanel.s creates PAGView, setRepeatCount(1), listener/play and 3000ms cleanup fallback',
              'limits': 'Source import only, not MAML-engine transplant or runtime/device verification. Vortex is background only. Pin is manual card-effect preview. Complete OTA archive unverified.'}
    dump(EXTRACTED / 'selected-port-plan.json', report)
    if args.apply:
        # All source/archive/destination/thumbnail checks finished before mutations.
        for relative, data in all_files.items():
            target = ASSETS / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        for relative, data in manifests.items():
            target = WORK / 'research' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        report['resultCatalogueSha256'] = sha((json.dumps(baseline + entries, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
        dump(ASSETS / 'catalog.json', baseline + entries)
        result = json.loads((ASSETS / 'catalog.json').read_text(encoding='utf-8'))
        if result[:30] != baseline or len(result) != 33:
            raise AssertionError('Original baseline entries altered by append')
        dump(WORK / 'research/hongkong-selected-port-provenance.json', report)
    print(json.dumps({'mode': 'apply' if args.apply else 'plan', 'addedEntries': 3,
                      'addedUniqueMediaSha256': 6, 'originalClockDigits': 29,
                      'actualThumbnailsProvided': len(thumbnail_evidence)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
