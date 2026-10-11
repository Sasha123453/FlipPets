"""Prepare one validated Charlie TemplateItem and resources. No phone actions or Apply."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import uuid
import zipfile
from native_pet_geometry import editor_position, systemui_translation

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / 'outputs/FlipPets-native-Charlie-proof.zip'
BUNDLE_SHA = 'e78cdfc3597f6592857c405160e59a6f76c110022b30490f8ec5b8aca5cb9842'
PAG_SHA = '3bb7533fd7506cdfcd6b0ad48a7027fe8b37353ee7723547a18a6b7e5518dc14'
STAGING_ROOT = '/sdcard/Download/FlipPetsNative/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_bundle(path=BUNDLE):
    raw = Path(path).read_bytes()
    if sha(raw) != BUNDLE_SHA:
        raise ValueError('Expected the unchanged, independently decoded Charlie proof bundle')
    with zipfile.ZipFile(path) as archive:
        proof = json.loads(archive.read('manifest.json'))
        pag, poster = archive.read('original.pag'), archive.read('poster.png')
        if sha(pag) != PAG_SHA or sha(poster) != proof['poster']['sha256']:
            raise ValueError('Resource identity mismatch')
        if (proof['width'], proof['height'], proof['durationUs']) != (976, 596, 6000000):
            raise ValueError('Unexpected composition')
        if poster != archive.read(proof['frames'][0]['png']):
            raise ValueError('Poster must be the decoded original first frame')
    return proof, pag, poster


def validate_id(biz_id):
    if not isinstance(biz_id, str) or not re.fullmatch(r'flippets-charlie-[0-9a-f]{32}', biz_id):
        raise ValueError('Use a newly generated, app-owned Charlie identity')


def axes(values, width=976, height=596):
    if not isinstance(values, list) or len(values) != 4 or any(type(v) is not int for v in values):
        raise ValueError('Invalid sampled axes')
    left, top, right, bottom = values
    if not 0 <= left < right <= width or not 0 <= top < bottom <= height:
        raise ValueError('Axes are outside the unchanged composition')
    return dict(zip(('leftX', 'leftY', 'rightX', 'rightY'), values))


def make_template(proof, biz_id, variant='original'):
    validate_id(biz_id)
    if variant not in ('original', 'composite'):
        raise ValueError('Unknown native resource variant')
    remote = STAGING_ROOT + biz_id
    width, height = (976, 596) if variant == 'original' else (1208, 1392)
    return dict(clockInfo=dict(templateId='ai_pets', style=1, primaryColor=-1,
                    primaryColor180=-1, aodPrimaryColor=-1, blendColor=0,
                    wallpaperDark=False, blendColor180=0, wallpaperDark180=False),
                pets=dict(petCategory=2, petType=1, romPreset=False, aiPetsData=dict(
                    bizId=biz_id, firstFrameCoordinateAxes=axes(proof['frames'][0]['alphaBounds'], width, height),
                    lastFrameCoordinateAxes=axes(proof['frames'][-1]['alphaBounds'], width, height),
                    resourcePag=remote + ('/original.pag' if variant == 'original' else '/native.pag'), resourcePic=remote + '/poster.png')),
                otherInfoColors=dict(cameraIconColor=-1, cameraIconColor180=-1,
                    cameraIconBgColor=-1209444, cameraIconBgColor180=-1209444,
                    isDeepCameraWallpaper=False, isDeepCameraWallpaper180=False,
                    cameraBlockAreaWallpaperDark=True, isCameraIconBgBlur=True,
                    isDeepFaceWallpaper0=True, isDeepFaceWallpaper180=True),
                templateName=biz_id, supportSubject=False, previewWallpaperInfo={},
                wallpaperInfo0=None, wallpaperInfo180=None)


def validate_template(template, proof, variant='original'):
    biz_id = template['pets']['aiPetsData']['bizId']
    # This is deliberately a single known fixture, not a general arbitrary-path importer.
    if template != make_template(proof, biz_id, variant):
        raise ValueError('Template differs from the known preview-only Charlie schema')
    return biz_id


def verified_resources(variant='original'):
    if variant == 'original':
        return verify_bundle()
    if variant != 'composite':
        raise ValueError('Unknown resource variant')
    from prepare_native_composite import compose
    from PIL import Image
    _, original, _ = verify_bundle()
    target = ROOT / 'outputs/native-pet/charlie-composite'
    pag = (target / 'candidate.pag').read_bytes()
    background = (ROOT / 'work/app/assets/pets/bird-pandora/bg.webp').read_bytes()
    if pag != compose(original, background):
        raise ValueError('Candidate differs from the source-backed wrapper')
    proof = json.loads((target / 'decode.json').read_text(encoding='utf-8'))
    if proof['sourceSha256'] != sha(pag) or proof['fullyOpaqueSamples'] != 8 or len(proof['frames']) != 8:
        raise ValueError('Candidate decode evidence is missing/stale')
    if proof.get('firstPoseMatchesDonorExactly') is not True or proof.get('probeSourceSha256') != sha((ROOT / 'work/tests/NativePetProbe.java').read_bytes()):
        raise ValueError('A fresh decode with a verified bird pose in the poster is required')
    if (proof['width'], proof['height'], proof['durationUs']) != (1208, 1392, 6000000):
        raise ValueError('Unexpected adapted composition')
    for i, frame in enumerate(proof['frames']):
        data = (target / f'frame-{i:02}.png').read_bytes()
        image = Image.open(target / f'frame-{i:02}.png').convert('RGBA')
        if sha(data) != frame['pngSha256'] or sha(image.tobytes()) != frame['rgbaSha256']:
            raise ValueError('Candidate sampled pixels changed')
        if image.size != (1208, 1392) or image.getchannel('A').getextrema() != (255, 255):
            raise ValueError('Adaptation must cover its poster opaquely')
    poster = (target / 'poster.png').read_bytes()
    if poster != (target / 'frame-00.png').read_bytes():
        raise ValueError('Use the exact adapted first frame as poster')
    return proof, pag, poster


def prepare(destination=None, variant='original'):
    proof, pag, poster = verified_resources(variant)
    biz_id = 'flippets-charlie-' + uuid.uuid4().hex
    destination = Path(destination) if destination else ROOT / 'outputs/native-pet' / biz_id
    destination.mkdir(parents=True, exist_ok=False)
    template = make_template(proof, biz_id, variant)
    validate_template(template, proof, variant)
    rendered = (json.dumps(template, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')
    pag_name = 'original.pag' if variant == 'original' else 'native.pag'
    (destination / pag_name).write_bytes(pag)
    (destination / 'poster.png').write_bytes(poster)
    (destination / 'template.json').write_bytes(rendered)
    a = proof['frames'][0]['alphaBounds']
    geometry = []
    for rotation in (0, 2):
        width, height = proof['width'], proof['height']
        branch, point = systemui_translation(template, width, height, rotation)
        geometry.append(dict(rotation=rotation, initialSystemUiBranch=branch,
            initialTranslation=list(point), editorInitialPosition=editor_position(width, height, a, rotation)))
    manifest = dict(schemaVersion=1, variant=variant, bizId=biz_id, device='ruyi', build='OS3.0.303.0.WNIEUXM',
        bundleSha256=BUNDLE_SHA, resourceDecoderApkSha256=proof['rendererApkSha256'],
        resources=[dict(file=name, sha256=sha(data), bytes=len(data))
                   for name, data in ((pag_name, pag), ('poster.png', poster), ('template.json', rendered))],
        geometryModel=geometry, nativeApplyAllowed=False, exactRestoreProven=False,
        nativeMotionProven=False, cameraClearanceProven=False,
        limits=['Axes come from first and near-end samples, not a full animation envelope.',
                'Editor crop may replace both wallpaper position structures; inspect its resulting JSON.',
                'PositionInfo stores negative translation; SystemUI negates it back. No scale is transferred.',
                'Original crest clipping remains; prepared resources are unchanged.'])
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New, non-existing local folder only')
    parser.add_argument('--variant', choices=('original', 'composite'), default='original')
    args = parser.parse_args()
    print(prepare(args.output, args.variant))


if __name__ == '__main__':
    main()
