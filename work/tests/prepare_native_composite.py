"""Charlie-only PAG wrapper: unchanged donor compositions over its verified MAML background.

Small PAG tag writer based on Tencent's documented Apache-2.0 codec format:
https://github.com/Tencent/libpag/tree/main/src/codec
This is an adaptation, not a byte-identical donor file or general PAG editor.
"""
from pathlib import Path
import hashlib
import json
import struct
import zipfile
from prepare_native_template import ROOT, PAG_SHA, verify_bundle, sha
BACKGROUND_SHA = '9a0572efba4be4ecd6a2b6db21f088333ea7c5cdfb49ee69bce0471efd826dfb'


def uint(value):
    if not 0 <= value <= 0xffffffff:
        raise ValueError('Unsigned 32-bit value required')
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return bytes(result)


def tag(code, data=b''):
    if not 0 <= code < 1024:
        raise ValueError('Invalid tag')
    n = len(data)
    return struct.pack('<H', code * 64 + min(n, 63)) + (struct.pack('<I', n) if n >= 63 else b'') + data


def tags(data, offset=0):
    while offset + 2 <= len(data):
        header, = struct.unpack_from('<H', data, offset)
        offset += 2
        code, length = header >> 6, header & 63
        if length == 63:
            if offset + 4 > len(data):
                raise ValueError('Truncated extended tag length')
            length, = struct.unpack_from('<I', data, offset)
            offset += 4
        if offset + length > len(data):
            raise ValueError('Truncated PAG tag')
        yield code, data[offset:offset+length]
        offset += length
        if code == 0:
            if length or offset != len(data):
                raise ValueError('Unexpected trailing bytes')
            return
    raise ValueError('Missing end tag')


def layer(kind, identity, transform, reference):
    # Active layer, all optional attributes default, fixed duration 180 frames.
    return tag(5, bytes([kind]) + uint(identity) + tag(6, b'\x01' + uint(180))
               + tag(13, transform) + reference + tag(0))


def compose(original, background, subject_transform=None):
    if sha(original) != PAG_SHA:
        raise ValueError('Only the verified original Charlie can be wrapped')
    if sha(background) != BACKGROUND_SHA:
        raise ValueError('Only the verified MAML Charlie background can be embedded')
    if original[:4] != b'PAG\x01' or original[8] != 85 or struct.unpack_from('<I', original, 4)[0] != len(original)-9:
        raise ValueError('Unexpected PAG header/profile')
    source = list(tags(original, 9))
    if [code for code, _ in source] != [31, 32, 50, 2, 0]:
        raise ValueError('Unexpected Charlie composition graph')
    # Existing main composition 16 remains byte-for-byte intact; new root 17 references it.
    if source[3][1][0] != 16:
        raise ValueError('Unexpected original main composition identity')
    attrs = uint(1208 * 2) + uint(1392 * 2) + uint(180) + struct.pack('<f', 30) + b'\0\0\0'
    transform = b'\x02' + struct.pack('<ff', 0, 796)
    if subject_transform is not None:
        import math
        scale, x, y = subject_transform
        if not all(math.isfinite(v) for v in (scale,x,y)) or not 1 <= scale <= 3 or not -1208 <= x <= 1208 or not -1392 <= y <= 1392:
            raise ValueError('Bounded constant subject transform required')
        transform = b'\x22\x00' + struct.pack('<ffff',x,y,scale,scale)
    bird = layer(6, 2001, transform, tag(12, uint(16) + uint(0)))
    # One pixel beyond each edge avoids GPU antialiasing exposing the underlying poster.
    bg = layer(5, 2002, b'\x22\x00' + struct.pack('<ffff', -1, -1, 1210 / 976, 1394 / 596), tag(11, uint(1)))
    # PAG layer order is top first. The background is opaque and covers the static poster during motion.
    root = tag(2, uint(17) + tag(3, attrs) + bird + bg + tag(0))
    image = tag(47, uint(1) + uint(len(background)) + background)
    body = b''.join(tag(c, payload) for c, payload in source[:2]) + image
    body += b''.join(tag(c, payload) for c, payload in source[2:-1]) + root + tag(0)
    return b'PAG\x01' + struct.pack('<I', len(body)) + bytes([85]) + body


def prepare():
    proof, original, _ = verify_bundle()
    container = ROOT / 'work/original-resources/pandora/content/26f4a446-8125-407d-a255-3dbcd8c12eae.mrc'
    if sha(container.read_bytes()) != proof['provenance']['sourceContainerSha256']:
        raise ValueError('Original donor container changed')
    background = (ROOT / 'work/app/assets/pets/bird-pandora/bg.webp').read_bytes()
    with zipfile.ZipFile(container) as archive:
        members = [name for name in archive.namelist() if name.endswith('assets/bird/bg.webp')]
        if len(members) != 1 or archive.read(members[0]) != background:
            raise ValueError('Background does not match the verified donor container')
    candidate = compose(original, background)
    destination = ROOT / 'outputs/native-pet/charlie-composite'
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'candidate.pag').write_bytes(candidate)
    manifest = dict(schemaVersion=1, scope='Native compatibility adaptation, not unchanged donor PAG',
                    originalPagSha256=sha(original), backgroundSha256=sha(background),
                    backgroundSourceMember=members[0], pagSha256=sha(candidate),
                    width=1208, height=1392, birdTranslation=[0, 796],
                    backgroundTransform='MAML full-canvas stretch, with 1px background overscan to cover antialiased edges',
                    nativeApplyAllowed=False, decodedCandidateVerified=False)
    (destination / 'composition.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(destination)


if __name__ == '__main__':
    prepare()
