"""Decode the Charlie compatibility PAG on the explicitly guarded emulator, never an OEM host."""
from pathlib import Path
import hashlib
import json
import subprocess
import uuid
import zipfile
from PIL import Image
from prepare_native_pet import ROOT, adb, sha, SERIAL
from prepare_native_composite import compose, tags
from prepare_native_template import verify_bundle


def main():
    if adb('shell', 'getprop ro.kernel.qemu').strip() != '1' or not any(
            x in adb('shell', 'getprop ro.hardware') for x in ('ranchu', 'goldfish')):
        raise ValueError('Explicit emulator identity required')
    apk = ROOT / 'outputs/FlipPets.apk'
    target = ROOT / 'outputs/native-pet/charlie-composite'
    candidate = target / 'candidate.pag'
    proof, original, _ = verify_bundle()
    background = (ROOT / 'work/app/assets/pets/bird-pandora/bg.webp').read_bytes()
    if candidate.read_bytes() != compose(original, background):
        raise ValueError('Candidate differs from the inspected composition')
    jdk = ROOT / 'work/tools/jdk/jdk-17.0.20.1+1/bin'
    bt = ROOT / 'work/tools/sdk/build-tools/android-16'
    android = ROOT / 'work/tools/sdk/platforms/android-36/android.jar'
    build = ROOT / 'work/qa-final/native-composite-probe'
    classes, dex, libs = (build / x for x in ('classes', 'dex', 'libs'))
    for directory in (classes, dex, libs):
        directory.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(jdk / 'javac.exe'), '-encoding', 'UTF-8', '-cp', str(android),
                    '-d', str(classes), str(ROOT / 'work/tests/NativePetProbe.java')], check=True)
    subprocess.run([str(jdk / 'java.exe'), '-cp', str(bt / 'lib/d8.jar'), 'com.android.tools.r8.D8',
                    '--lib', str(android), '--output', str(dex), str(classes / 'NativePetProbe.class')], check=True)
    with zipfile.ZipFile(apk) as archive:
        for name in archive.namelist():
            if name.startswith('lib/x86_64/') and name.endswith('.so'):
                (libs / Path(name).name).write_bytes(archive.read(name))
    remote = '/data/local/tmp/flippets-native-pet-' + uuid.uuid4().hex
    adb('shell', 'mkdir -p ' + remote + '/lib')
    try:
        adb('push', apk, remote + '/base.apk', timeout=120)
        adb('push', candidate, remote + '/candidate.pag')
        adb('push', dex / 'classes.dex', remote + '/probe.dex')
        import io
        with zipfile.ZipFile(ROOT / 'outputs/FlipPets-native-Charlie-proof.zip') as archive:
            for i in range(8):
                reference = build / f'reference-{i:02}.rgba'
                reference.write_bytes(Image.open(io.BytesIO(archive.read(f'samples/frame-{i:02}.png'))).convert('RGBA').tobytes())
                adb('push', reference, remote + '/' + reference.name)
        for library in libs.glob('*.so'):
            adb('push', library, remote + '/lib/' + library.name)
        report = json.loads(adb('shell', f'CLASSPATH={remote}/probe.dex app_process /system/bin NativePetProbe '
                    f'{remote}/base.apk {remote}/lib {remote} {remote}/candidate.pag', timeout=120))
        if (report['width'], report['height'], report['durationUs']) != (1208, 1392, 6000000):
            raise ValueError('Incorrect wrapper geometry/duration')
        if report['sourceSha256'] != sha(candidate) or len(report['frames']) != 8:
            raise ValueError('Candidate identity/sample contract mismatch')
        for i, frame in enumerate(report['frames']):
            raw_path = build / f'frame-{i:02}.rgba'
            adb('pull', remote + '/' + frame['raw'], raw_path)
            rgba = raw_path.read_bytes()
            if len(rgba) != 1208*1392*4 or hashlib.sha256(rgba).hexdigest() != frame['rgbaSha256']:
                raise ValueError('Decoded bytes mismatch')
            image = Image.frombytes('RGBA', (1208, 1392), rgba)
            if image.getchannel('A').getextrema() != (255, 255):
                raise ValueError('Native adaptation must cover the static poster opaquely')
            # An opaque background alone also passes alpha checks. Require the real donor pose.
            with zipfile.ZipFile(ROOT / 'outputs/FlipPets-native-Charlie-proof.zip') as archive:
                donor = Image.open(io.BytesIO(archive.read(f'samples/frame-{i:02}.png'))).convert('RGBA')
            placed = image.crop((0, 796, 976, 1392))
            errors = [max(abs(a[k]-b[k]) for k in range(3))
                      for a, b in zip(donor.getdata(), placed.getdata()) if a[3] == 255]
            mismatches = sum(error > 1 for error in errors)
            if len(errors) < 100000 or mismatches > len(errors) * .005 or sum(errors)/len(errors) > .1 or (i == 0 and max(errors) != 0):
                raise ValueError(f'Missing/wrong donor pose in sample {i}: never use a background-only decoded poster')
            frame['donorOpaquePixelsChecked'] = len(errors)
            frame['donorOpaquePixelsOutsideTolerance'] = mismatches
            output = target / f'frame-{i:02}.png'
            image.save(output)
            if Image.open(output).convert('RGBA').tobytes() != rgba:
                raise ValueError('PNG pixels differ from actual decode')
            frame.pop('raw')
            frame['pngSha256'] = sha(output)
        if len({r['rgbaSha256'] for r in report['frames']}) < 3:
            raise ValueError('Candidate must retain motion')
    finally:
        adb('shell', 'rm -rf ' + remote)
    (target / 'poster.png').write_bytes((target / 'frame-00.png').read_bytes())
    report.update(schemaVersion=1, rendererApkSha256=sha(apk), probeSourceSha256=sha(ROOT / 'work/tests/NativePetProbe.java'),
                  fullyOpaqueSamples=8, originalCompositionsPreserved=True, firstPoseMatchesDonorExactly=True,
                  nativePlaybackProven=False, nativeApplyAllowed=False,
                  scope='Emulator decoder samples of the adaptation; not native editor or lockscreen proof')
    (target / 'decode.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Eight opaque 1208x1392 candidate samples decoded; inspect pixels before native preview.')


if __name__ == '__main__':
    main()
