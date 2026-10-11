"""Prepare one unchanged Charlie PAG and its exact decoded poster; emulator only, no OEM Apply."""
from pathlib import Path
import hashlib
import json
import subprocess
import uuid
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ADB = 'C:/platform-tools/adb.exe'
SERIAL = 'emulator-5554'
SOURCE = 'pets/bird-pandora/pag_0.pag'
EXPECTED = '3bb7533fd7506cdfcd6b0ad48a7027fe8b37353ee7723547a18a6b7e5518dc14'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def adb(*parts, timeout=30):
    return subprocess.run([ADB, '-s', SERIAL, *map(str, parts)], check=True,
                          capture_output=True, text=True, encoding='utf-8', timeout=timeout).stdout


def main():
    assert adb('shell', 'getprop ro.kernel.qemu').strip() == '1', 'Emulator required'
    assert any(x in adb('shell', 'getprop ro.hardware') for x in ('ranchu', 'goldfish'))
    apk = ROOT / 'outputs/FlipPets.apk'
    original = ROOT / 'work/app/assets' / SOURCE
    assert sha(original) == EXPECTED, 'Original verified donor bytes required'
    container = ROOT / 'work/original-resources/pandora/content/26f4a446-8125-407d-a255-3dbcd8c12eae.mrc'
    assert sha(container) == '9147868c42edcec122dfb5c5e497506bc2d7dd487b27110cc8bb32b9a6c6e52e'
    with zipfile.ZipFile(container) as archive:
        source_members = [name for name in archive.namelist() if name.endswith('.pag')
                          and hashlib.sha256(archive.read(name)).hexdigest() == EXPECTED]
    assert source_members, 'PAG must match a verified original container member'
    target = ROOT / 'work/qa-final/native-pet-source'
    target.mkdir(parents=True, exist_ok=True)
    jdk = ROOT / 'work/tools/jdk/jdk-17.0.20.1+1/bin'
    bt = ROOT / 'work/tools/sdk/build-tools/android-16'
    android = ROOT / 'work/tools/sdk/platforms/android-36/android.jar'
    classes, dex, libs = (target / x for x in ('classes', 'dex', 'libs'))
    for directory in (classes, dex, libs):
        directory.mkdir(exist_ok=True)
    subprocess.run([str(jdk / 'javac.exe'), '-encoding', 'UTF-8', '-cp', str(android),
                    '-d', str(classes), str(ROOT / 'work/tests/NativePetProbe.java')], check=True)
    subprocess.run([str(jdk / 'java.exe'), '-cp', str(bt / 'lib/d8.jar'), 'com.android.tools.r8.D8',
                    '--lib', str(android), '--output', str(dex), str(classes / 'NativePetProbe.class')], check=True)
    with zipfile.ZipFile(apk) as archive:
        assert archive.read('assets/' + SOURCE) == original.read_bytes()
        for name in archive.namelist():
            if name.startswith('lib/x86_64/') and name.endswith('.so'):
                (libs / Path(name).name).write_bytes(archive.read(name))
    # Random, app-independent, emulator-only staging. Never an OEM resource path.
    remote = '/data/local/tmp/flippets-native-pet-' + uuid.uuid4().hex
    adb('shell', 'mkdir -p ' + remote + '/lib')
    try:
        adb('push', apk, remote + '/base.apk', timeout=120)
        adb('push', dex / 'classes.dex', remote + '/probe.dex')
        for library in libs.glob('*.so'):
            adb('push', library, remote + '/lib/' + library.name)
        raw = adb('shell', f'CLASSPATH={remote}/probe.dex app_process /system/bin NativePetProbe '
                  f'{remote}/base.apk {remote}/lib {remote}', timeout=120)
        report = json.loads(raw)
        assert report['sourceSha256'] == EXPECTED
        assert (report['width'], report['height'], report['durationUs']) == (976, 596, 6000000)
        assert len(report['frames']) == 8
        assert len({f['rgbaSha256'] for f in report['frames']}) >= 3, 'Distinct source motion required'
        for index, frame in enumerate(report['frames']):
            assert frame['png'] == f'frame-{index:02}.png'
            assert frame['raw'] == f'frame-{index:02}.rgba'
            adb('pull', remote + '/' + frame['raw'], target / frame['raw'])
            rgba=(target / frame['raw']).read_bytes()
            assert len(rgba)==976*596*4 and hashlib.sha256(rgba).hexdigest()==frame['rgbaSha256']
            # Android's PNG encoder can round partially transparent RGB channels.
            # Serialize the actual getPixels RGBA losslessly on the host instead.
            Image.frombytes('RGBA',(976,596),rgba).save(target / frame['png'])
            frame['pngSha256'] = sha(target / frame['png'])
            with Image.open(target / frame['png']) as image:
                assert image.size == (976, 596)
                frame['pngDecodedRgbaSha256'] = hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest()
            assert frame['pngDecodedRgbaSha256'] == frame['rgbaSha256'], 'PNG must preserve decoded frame pixels'
    finally:
        # Fixed prefix + UUID generated above, never caller-provided paths.
        adb('shell', 'rm -rf ' + remote)
    poster = target / 'poster.png'
    poster.write_bytes((target / 'frame-00.png').read_bytes())
    report.update(schemaVersion=1, rendererApkSha256=sha(apk), sourceAsset=SOURCE,
                  originalPag=dict(file='original.pag',sha256=EXPECTED),
                  environment='Identity-verified Android emulator; actual APK libpag decoding at original resolution',
                  nativePlaybackProven=False, nativeApplyAllowed=False, exactRestoreProven=False,
                  poster=dict(file='poster.png', progress=0, sha256=sha(poster),
                              rgbaSha256=report['frames'][0]['rgbaSha256']),
                  nativeAxesCandidate=dict(first=report['frames'][0]['alphaBounds'],
                                           last=report['frames'][-1]['alphaBounds'],
                                           status='Sampled original-pixel bounds only; native placement/camera clearance unverified'),
                  sourceLimit='Original Charlie crest is clipped in intermediate source frames; this export does not repair it',
                  provenance=dict(donor='17 Pro pandora; also byte-identical in inspected 18 Pro resource',
                                  donorBuild='OS3.0.319.0.WBLCNXM',
                                  sourceContainer='26f4a446-8125-407d-a255-3dbcd8c12eae.mrc',
                                  sourceContainerSha256='9147868c42edcec122dfb5c5e497506bc2d7dd487b27110cc8bb32b9a6c6e52e',
                                  matchingSourceMembers=source_members,
                                  rights='Xiaomi artwork retains its owners rights; excluded from MIT code license'),
                  probeSha256=sha(ROOT / 'work/tests/NativePetProbe.java'))
    for frame in report['frames']:
        frame.pop('raw')
        frame['png']='samples/'+frame['png']
    manifest = target / 'manifest.json'
    manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    bundle = ROOT / 'outputs/FlipPets-native-Charlie-proof.zip'
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(original, 'original.pag')
        archive.write(poster, 'poster.png')
        archive.write(manifest, 'manifest.json')
        for frame in report['frames']:
            archive.write(target / Path(frame['png']).name, frame['png'])
    print(json.dumps(dict(bundle=str(bundle), bundleSha256=sha(bundle), rendererApkSha256=sha(apk),
                          originalPagSha256=EXPECTED, posterSha256=sha(poster),
                          sampledFrames=len(report['frames']), nativeApplyAllowed=False), indent=2))


if __name__ == '__main__':
    main()
