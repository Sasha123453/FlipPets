"""One Charlie native confirmation after explicit acceptance of manual restoration.

This is not an exact Restore implementation. It never installs root, writes secure
settings directly, changes display power, or repeats an uncertain confirmation.
"""
import argparse
import json
import re
import shlex
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from native_pet_preview import (Phone, KEYS, COMPONENT, PACKAGE_HASHES, WALLPAPER_METADATA,
    private_session, stable_state, verified_inventory, require_unlocked, native_path)
from native_pet_transaction_model import atomic_json
from prepare_native_template import verified_resources, validate_template, sha


def check_native_add_quota(raw):
    """Mirror the observed OEM admission limits; do not evict or bypass a slot."""
    history = json.loads(raw)
    if not isinstance(history, list) or any(not isinstance(item, dict) for item in history):
        raise ValueError('Unknown native history format')
    if len(history) >= 9:
        raise ValueError('Native saved-template limit reached; explicit slot choice is required')
    if sum(item.get('pets') is not None for item in history) >= 3:
        raise ValueError('All three native pet slots are occupied; ask which saved pet to replace')


def native_update_index(raw, biz_id):
    """Plan only: OEM resolves AI history by bizId; this is not a verified update operation."""
    if not isinstance(biz_id,str) or not re.fullmatch(r'flippets-charlie-[0-9a-f]{32}',biz_id):
        raise ValueError('Only our explicitly identified Charlie may be replaced')
    history=json.loads(raw)
    if not isinstance(history,list) or len(history)>9 or any(not isinstance(item,dict) for item in history):
        raise ValueError('Unknown native history format')
    matches=[]
    for index,item in enumerate(history):
        pets=item.get('pets') or {}
        if not isinstance(pets,dict):raise ValueError('Unknown pet history')
        ai=pets.get('aiPetsData') or {}
        if not isinstance(ai,dict):raise ValueError('Unknown AI history')
        if ai.get('bizId')==biz_id:
            if pets.get('petCategory')!=2 or (item.get('clockInfo') or {}).get('templateId')!='ai_pets':
                raise ValueError('Owned ID is in an unexpected native template')
            matches.append(index)
    if len(matches)!=1:raise ValueError('Owned Charlie history is missing or ambiguous; never fall back to Add')
    return matches[0]


def readback(phone, session):
    session = private_session(session)
    journal = session / 'native-apply.json'
    plan = json.loads(journal.read_text(encoding='utf-8'))
    receipt = json.loads((session / 'receipt.json').read_text(encoding='utf-8'))
    if plan.get('nativeApkSha256') != PACKAGE_HASHES or plan.get('userAcceptedManualRestoration') is not True:
        raise ValueError('Not a matching authorized native confirmation')
    template = json.loads((session / 'template.json').read_bytes())
    proof, pag, _ = verified_resources('composite')
    owned_id = validate_template(template, proof, 'composite')
    if plan.get('bizId') != owned_id or receipt.get('bizId') != owned_id:
        raise ValueError('Confirmation identity differs')
    after = stable_state(phone)
    current = json.loads(after[KEYS[0]])
    data = (current or {}).get('pets', {}).get('aiPetsData', {})
    if data.get('bizId') != owned_id:
        raise ValueError('Native choice is not this Charlie; preserve it and inspect, never repeat Add')
    copied_pag = native_path(data['resourcePag'])
    if phone.text('sha256sum ' + shlex.quote(copied_pag)).split()[0] != sha(pag):
        raise ValueError('Native PAG copy did not match prepared Charlie')
    for key, raw in after.items():
        (session / (key + '.applied.json')).write_bytes(raw)
    (session / 'small-lock.applied.xml').write_bytes(phone.call('exec-out',
        'cat ' + shlex.quote(WALLPAPER_METADATA)).stdout)
    plan.update(phase='native-selection-and-pag-acknowledged', nativeApplyPerformed=True,
                nativePagCopySha256=sha(pag), afterSettingsSha256={k: sha(v) for k, v in after.items()})
    atomic_json(journal, plan)
    receipt.update(nativeApplyPerformed=True, status=plan['phase'], userAcceptedManualRestoration=True)
    atomic_json(session / 'receipt.json', receipt)
    print('Native Charlie selection and exact PAG copy acknowledged. Manual restoration accepted.')
    print('Folded lockscreen, replay, sleep/wake and reboot still require device checks.')


def apply(phone, session, inventory, accepted):
    if accepted is not True:
        raise ValueError('Explicit user acceptance of manual restoration is required')
    session = private_session(session)
    journal = session / 'native-apply.json'
    if journal.exists():
        raise ValueError('An earlier confirmation may have run. Inspect its readback; never repeat blindly.')
    receipt = json.loads((session / 'receipt.json').read_text(encoding='utf-8'))
    if (receipt.get('nativeApplyPerformed') is not False
            or receipt.get('nativeApkSha256') != PACKAGE_HASHES
            or receipt.get('previewKind') is not None):
        raise ValueError('Only a matching Charlie preview session is accepted')
    template = json.loads((session / 'template.json').read_bytes())
    proof, pag, poster = verified_resources('composite')
    owned_id = validate_template(template, proof, 'composite')
    if receipt['bizId'] != owned_id:
        raise ValueError('Preview identity changed')
    before = {k: (session / (k + '.before.json')).read_bytes() for k in KEYS}
    if {k: sha(v) for k, v in before.items()} != receipt['beforeSettingsSha256']:
        raise ValueError('Preview baseline changed')
    check_native_add_quota(before[KEYS[1]])
    report = verified_inventory(inventory, before)
    if stable_state(phone) != before:
        raise ValueError('A later native choice/history exists; no confirmation performed')
    for row in report['resources']:
        tokens = phone.text('sha256sum ' + shlex.quote(row['path'])).split()
        if not tokens or tokens[0] != row['sha256']:
            raise ValueError('Previous native resources changed since backup')
    for key, raw in (('resourcePag', pag), ('resourcePic', poster)):
        path = template['pets']['aiPetsData'][key]
        if phone.text('sha256sum ' + shlex.quote(path)).split()[0] != sha(raw):
            raise ValueError('Staged Charlie resource changed')
    require_unlocked(phone)
    hinge = phone.text('dumpsys device_state')
    if not re.search(r'mCommittedState=.*identifier=3, name=.?OPENED', hinge):
        raise ValueError('Phone must be physically unfolded for native confirmation')
    windows = phone.text('dumpsys window')
    focus = [line for line in windows.splitlines() if 'mCurrentFocus=' in line]
    if len(focus) != 1 or COMPONENT not in focus[0] or 'mTopFocusedDisplayId=0' not in windows:
        raise ValueError('Exact native editor must have focus on the main display')
    remote = '/data/local/tmp/flippets-native-confirm-' + uuid.uuid4().hex + '.xml'
    try:
        result = phone.text('uiautomator dump ' + remote)
        if 'dumped to:' not in result:
            raise ValueError('Fresh native controls unavailable')
        root = ET.fromstring(phone.call('exec-out', 'cat ' + remote).stdout)
        matches = [n for n in root.iter('node') if n.get('package') == 'com.miui.aod'
                   and n.get('resource-id') == 'com.miui.aod:id/confirm'
                   and n.get('text') == 'Добавить' and n.get('clickable') == 'true']
        if len(matches) != 1:
            raise ValueError('Expected one real native Add control')
        bounds = re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', matches[0].get('bounds', ''))
        if not bounds:
            raise ValueError('Invalid native control bounds')
        left, top, right, bottom = map(int, bounds.groups())
        if not (0 <= left < right <= 1224 and 0 <= top < bottom <= 2912):
            raise ValueError('Unexpected native main-window geometry')
        # Last state/focus checks precede the journal and exactly one native tap.
        require_unlocked(phone)
        if stable_state(phone) != before or COMPONENT not in next(
                (l for l in phone.text('dumpsys window').splitlines() if 'mCurrentFocus=' in l), ''):
            raise ValueError('Native state/focus changed before confirmation')
        plan = dict(schemaVersion=1, phase='before-native-confirm', bizId=owned_id,
                    userAcceptedManualRestoration=True, exactRestoreProven=False,
                    nativeApplyPerformed=False, nativeApkSha256=PACKAGE_HASHES,
                    beforeSettingsSha256={k: sha(v) for k, v in before.items()},
                    backedUpResources=len(report['resources']))
        atomic_json(journal, plan)
        phone.text(f'input -d 0 tap {(left + right) // 2} {(top + bottom) // 2}')
        plan['phase'] = 'native-confirm-sent-readback-pending'
        atomic_json(journal, plan)
        deadline = time.monotonic() + 20
        while True:
            try:
                after = stable_state(phone)
            except ValueError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.3)
                continue
            current = json.loads(after[KEYS[0]])
            data = (current or {}).get('pets', {}).get('aiPetsData', {})
            if data.get('bizId') == owned_id:
                break
            if time.monotonic() >= deadline:
                raise ValueError('Native selection not acknowledged; inspect journal/UI, do not repeat Add')
            time.sleep(.3)
        time.sleep(1)
        readback(phone, session)
    finally:
        phone.call('shell', 'rm -f ' + remote, required=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--adb', default='C:/platform-tools/adb.exe')
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--accept-manual-restore', action='store_true')
    parser.add_argument('--readback-only', action='store_true')
    args = parser.parse_args()
    if args.readback_only:
        readback(Phone(args.serial, args.adb), args.session)
        return
    if not args.accept_manual_restore or args.inventory is None:
        parser.error('Explicit acceptance is required before any phone contact')
    apply(Phone(args.serial, args.adb), args.session, args.inventory, args.accept_manual_restore)


if __name__ == '__main__':
    main()
