"""Guarded existing-record Charlie preview/update, with one authorized OEM tap.

Never Add, delete a saved design, write secure settings, or change display power.
"""
from pathlib import Path,PurePosixPath
from copy import deepcopy
import json,re,shlex,time,uuid,xml.etree.ElementTree as ET
from PIL import Image
from native_pet_preview import (ROOT,Phone,KEYS,COMPONENT,PACKAGE_HASHES,stable_state,
    verified_inventory,require_unlocked,native_path,WALLPAPER_METADATA,outer_wallpaper_paths)
from native_pet_apply import native_update_index
from prepare_native_template import verify_bundle,make_template,sha,STAGING_ROOT
from prepare_native_composite import compose
from native_pet_transaction_model import atomic_json

CANDIDATE_SHA='c9b740fb529fa2b65bb18cbc0fd1a78461eb6b2e20d1308a68a82ae09d8494ce'
TRANSFORM=(2.220779220779221,-663.2727272727275,117.27272727272725)

def calibrated_resources():
    _,original,_=verify_bundle()
    target=ROOT/'outputs/native-pet/charlie-calibrated'
    pag=(target/'candidate.pag').read_bytes()
    background=(ROOT/'work/app/assets/pets/bird-pandora/bg.webp').read_bytes()
    layout=json.loads((ROOT/'work/app/assets/native-pet-layout.json').read_text(encoding='utf-8'))['layouts']['bird-pandora']
    if tuple(layout[k] for k in ('scale','x','y'))!=TRANSFORM or layout['referenceSourceSha256']!=sha(original):
        raise ValueError('App and native source transforms differ')
    if sha(pag)!=CANDIDATE_SHA or pag!=compose(original,background,TRANSFORM):
        raise ValueError('Calibrated composition differs from the decoded source-backed candidate')
    folder=ROOT/'work/qa-final/mixflip-calibrated-full'
    report=json.loads((folder/'decode.json').read_text(encoding='utf-8'))
    if not report.get('fullResolution') or not report.get('calibratedCandidate') or len(report['clips'])!=1:
        raise ValueError('Full-resolution candidate decode required')
    proof=deepcopy(report['clips'][0])
    if (proof['sourceSha256'],proof['width'],proof['height'],proof['durationUs'],proof['renderWidth'],proof['renderHeight'])!=(CANDIDATE_SHA,1208,1392,6000000,1208,1392):
        raise ValueError('Different decoded composition')
    snapshot=folder/('probe-'+proof['probeSha256']+'.java')
    if sha(snapshot.read_bytes())!=proof['probeSha256'] or len(proof['frames'])!=8:
        raise ValueError('Decode/probe evidence changed')
    if {f['png'] for f in proof['frames']}!={'charlie-0-'+str(i)+'.png' for i in range(8)}:
        raise ValueError('Eight different sampled frames required')
    for frame in proof['frames']:
        if not re.fullmatch(r'charlie-0-[0-7]\.png',frame['png']):raise ValueError('Unknown sampled file')
        raw=(folder/frame['png']).read_bytes()
        with Image.open(folder/frame['png']) as image:
            pixels=image.convert('RGBA')
            if image.size!=(1208,1392) or pixels.getchannel('A').getextrema()!=(255,255) or sha(pixels.tobytes())!=frame['decodedRgbaSha256']:
                raise ValueError('Sampled pixels changed/not opaque')
        if sha(raw)!=frame['pngSha256'] or frame['stableSnapshots']<3:
            raise ValueError('Sampled image/readiness differs')
    if len({f['decodedRgbaSha256'] for f in proof['frames']})<3:raise ValueError('Motion evidence missing')
    poster=(target/'poster.png').read_bytes()
    if poster!=(folder/proof['frames'][0]['png']).read_bytes():raise ValueError('Poster is not the actual decoded first pose')
    return proof,pag,poster

def update_template(proof,biz_id,token):
    if not re.fullmatch('[0-9a-f]{32}',token):raise ValueError('Unknown staging token')
    template=make_template(proof,biz_id,'composite')
    remote=STAGING_ROOT+biz_id+'/updates/'+token
    template['pets']['aiPetsData'].update(resourcePag=remote+'/native.pag',resourcePic=remote+'/poster.png')
    return template

def session_path(path):
    path=Path(path).resolve();root=(ROOT/'work/phone-qa').resolve()
    if path.parent!=root or not re.fullmatch('pet-update-[0-9a-f]{32}',path.name):raise ValueError('Use an owned private update session')
    return path

def verify_previous_files(phone,report):
    for row in report['resources']:
        if phone.text('sha256sum '+shlex.quote(native_path(row['path']))).split()[0]!=row['sha256']:
            raise ValueError('An existing native resource changed; no update/cancel guessed')

def update_control(raw):
    if not raw or len(raw)>2*1024*1024 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('Invalid native controls')
    root=ET.fromstring(raw)
    matches=[n for n in root.iter('node') if n.get('package')=='com.miui.aod' and n.get('resource-id')=='com.miui.aod:id/confirm']
    if len(matches)!=1:raise ValueError('Expected one native confirmation')
    node=matches[0]
    # Verified EEA EditorActionButton.a(1) -> tiny_kg_edit_activity_complete
    # (0x7f120596, ru: Готово); a(0) is the distinct Добавить branch.
    if node.get('text')!='Готово' or node.get('clickable')!='true' or node.get('enabled')!='true':
        raise ValueError('Native editor did not expose an enabled existing-record Done control; never press Add')
    return node

def begin(phone,inventory):
    before=stable_state(phone);report=verified_inventory(inventory,before)
    current=json.loads(before[KEYS[0]])
    biz_id=(current or {}).get('pets',{}).get('aiPetsData',{}).get('bizId')
    index=native_update_index(before[KEYS[1]],biz_id)
    old_owned_resources(before,biz_id)
    proof,pag,poster=calibrated_resources()
    require_unlocked(phone)
    if not re.search(r'mCommittedState=.*name=.?OPENED[\x27,]',phone.text('dumpsys device_state')):
        raise ValueError('Physically unfold and unlock before this native preview')
    verify_previous_files(phone,report)
    token=uuid.uuid4().hex;session=ROOT/'work/phone-qa'/('pet-update-'+token);session.mkdir()
    for key,raw in before.items():(session/(key+'.before.json')).write_bytes(raw)
    template=update_template(proof,biz_id,token);raw=json.dumps(template,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    (session/'template.json').write_bytes(raw)
    remote=STAGING_ROOT+biz_id+'/updates/'+token
    plan=dict(schemaVersion=1,phase='before-stage',bizId=biz_id,token=token,historyIndex=index,
        nativeApkSha256=PACKAGE_HASHES,inventory=str(Path(inventory).resolve()),
        beforeSettingsSha256={k:sha(v) for k,v in before.items()},templateSha256=sha(raw),
        candidateSha256=sha(pag),posterSha256=sha(poster),nativeApplyPerformed=False,
        exactRestoreProven=False,previewUpdateControlVerified=False)
    atomic_json(session/'receipt.json',plan)
    if phone.call('shell','test ! -e '+shlex.quote(remote),required=False).returncode:raise ValueError('Staging directory already exists')
    phone.text('mkdir -p '+shlex.quote(remote))
    for name,data in [('native.pag',pag),('poster.png',poster)]:
        local=session/name;local.write_bytes(data);phone.call('push',local,remote+'/'+name)
        if phone.text('sha256sum '+shlex.quote(remote+'/'+name)).split()[0]!=sha(data):raise ValueError('Staging hash differs')
    if stable_state(phone)!=before:raise ValueError('Native choice/history changed; staged files retained, preview not opened')
    plan['phase']='before-preview';atomic_json(session/'receipt.json',plan)
    command='am start -W -a miui.tinykeyguard.editor.EDIT -n '+COMPONENT+' --es param_template_item_json '+shlex.quote(raw.decode('utf-8'))
    launch=phone.call('shell',command);(session/'launch.txt').write_bytes(launch.stdout+launch.stderr)
    plan['phase']='preview-launched-unverified';atomic_json(session/'receipt.json',plan)
    print('Owned Charlie replacement preview opened; no confirmation was pressed.')
    print('Private session:',session)
    return session

def inspect_preview(phone,path):
    session=session_path(path);plan=json.loads((session/'receipt.json').read_text(encoding='utf-8'))
    if plan['nativeApplyPerformed'] is not False or plan['nativeApkSha256']!=PACKAGE_HASHES:raise ValueError('Not a matching preview session')
    before={k:(session/(k+'.before.json')).read_bytes() for k in KEYS}
    if {k:sha(v) for k,v in before.items()}!=plan['beforeSettingsSha256']:raise ValueError('Baseline changed')
    template=json.loads((session/'template.json').read_bytes());proof,_,_=calibrated_resources()
    if template!=update_template(proof,plan['bizId'],plan['token']):raise ValueError('Unknown replacement input')
    if stable_state(phone)!=before:raise ValueError('Native state changed before confirmation')
    report=verified_inventory(plan['inventory'],before);verify_previous_files(phone,report)
    focus=phone.text('dumpsys window')
    if COMPONENT not in next((x for x in focus.splitlines() if 'mCurrentFocus=' in x),''):raise ValueError('Exact editor is not focused')
    remote='/data/local/tmp/flippets-update-controls-'+plan['token']+'.xml'
    try:
        result=phone.text('uiautomator dump '+remote)
        if 'dumped to:' not in result:raise ValueError('Fresh native controls unavailable')
        raw=phone.call('exec-out','cat '+remote).stdout;(session/'controls.xml').write_bytes(raw)
    finally:phone.call('shell','rm -f '+remote,required=False)
    node=update_control(raw)
    plan.update(phase='update-preview-control-verified',previewUpdateControlVerified=True,
        nativeStateUnchangedInPreview=True,previousResourceHashesUnchangedInPreview=True)
    atomic_json(session/'receipt.json',plan)
    print('Real enabled existing-record Done control verified. Original settings and resource hashes remain unchanged.')
    return node

def unchanged_other_history(before,after,biz_id):
    old=json.loads(before);new=json.loads(after)
    old_index=native_update_index(before,biz_id);new_index=native_update_index(after,biz_id)
    if len(new)!=len(old) or old[:old_index]+old[old_index+1:]!=new[:new_index]+new[new_index+1:]:
        raise ValueError('Other saved designs changed or update added another slot')
    return new[new_index]

def old_owned_resources(before,biz_id):
    current=json.loads(before[KEYS[0]]);history=json.loads(before[KEYS[1]])
    index=native_update_index(before[KEYS[1]],biz_id)
    if current!=history[index]:raise ValueError('Baseline current is not exactly the owned history row')
    pag=native_path(current['pets']['aiPetsData']['resourcePag'])
    parent=PurePosixPath(pag).parent
    from native_pet_preview import NATIVE_ROOT
    try:relative=parent.relative_to(NATIVE_ROOT)
    except ValueError:raise ValueError('Owned resources must be in the native private wallpaper tree')
    if len(relative.parts)<2:raise ValueError('Refuse a broad/shared resource directory')
    def paths(value):
        result=set()
        if isinstance(value,dict):
            for child in value.values():result.update(paths(child))
        elif isinstance(value,list):
            for child in value:result.update(paths(child))
        elif isinstance(value,str) and value.startswith('/'):
            result.add(native_path(value))
        return result
    owned={p for p in paths(current) if PurePosixPath(p).parent==parent}
    others=paths(history[:index]+history[index+1:])
    if owned&others:raise ValueError('Owned resource path is shared by another saved design')
    return owned

def editor_present(activity_dump):
    # ActivityRecord uses the complete class name even when the component is abbreviated.
    name=COMPONENT.split('/')[1]
    return any(name in line and ('ActivityRecord{' in line or 'realActivity=' in line or 'origActivity=' in line)
               for line in activity_dump.splitlines())

def verify_cancelled(phone,path):
    session=session_path(path);plan=json.loads((session/'receipt.json').read_text(encoding='utf-8'))
    if (session/'native-update.json').exists() or plan['nativeApplyPerformed'] is not False:
        raise ValueError('A confirmation may have run; use readback rather than cancellation')
    before={k:(session/(k+'.before.json')).read_bytes() for k in KEYS}
    if {k:sha(v) for k,v in before.items()}!=plan['beforeSettingsSha256'] or stable_state(phone)!=before:
        raise ValueError('Native choice/history changed; no restore guessed')
    activities=phone.text('dumpsys activity activities')
    (session/'activities-after-cancel.txt').write_text(activities,encoding='utf-8')
    if editor_present(activities):raise ValueError('Editor Activity/task still exists; Cancel not complete')
    verify_previous_files(phone,verified_inventory(plan['inventory'],before))
    plan.update(phase='cancelled-editor-absent-state-and-resources-unchanged',editorExited=True)
    atomic_json(session/'receipt.json',plan)
    print('Native Cancel verified: editor Activity/task absent, original settings and all resources unchanged.')

def readback_update(phone,path):
    session=session_path(path);journal=session/'native-update.json'
    record=json.loads(journal.read_text(encoding='utf-8'));plan=json.loads((session/'receipt.json').read_text(encoding='utf-8'))
    if record.get('userAcceptedUpdateAndManualRestoration') is not True or record.get('nativeApkSha256')!=PACKAGE_HASHES:
        raise ValueError('No matching authorized update journal')
    before={k:(session/(k+'.before.json')).read_bytes() for k in KEYS}
    if {k:sha(v) for k,v in before.items()}!=plan['beforeSettingsSha256'] or record['bizId']!=plan['bizId']:
        raise ValueError('Update baseline/identity differs')
    proof,pag,poster=calibrated_resources()
    if json.loads((session/'template.json').read_bytes())!=update_template(proof,plan['bizId'],plan['token']):
        raise ValueError('Replacement input changed')
    after=stable_state(phone);current=json.loads(after[KEYS[0]])
    row=unchanged_other_history(before[KEYS[1]],after[KEYS[1]],plan['bizId'])
    data=(current or {}).get('pets',{}).get('aiPetsData',{})
    if data.get('bizId')!=plan['bizId'] or row!=current:
        raise ValueError('Current/history update has not converged; never confirm again')
    for key,raw in (('resourcePag',pag),('resourcePic',poster)):
        if phone.text('sha256sum '+shlex.quote(native_path(data[key]))).split()[0]!=sha(raw):
            raise ValueError('Native resource copy not acknowledged; never repeat confirmation')
    report=verified_inventory(plan['inventory'],before)
    # OEM deletes the replaced template's source directory, including its preview
    # and crop files. Exempt only exact old-owned references, never another design.
    replaceable={WALLPAPER_METADATA}|old_owned_resources(before,plan['bizId'])
    metadata_row=next(r for r in report['resources'] if r['path']==WALLPAPER_METADATA)
    replaceable.update(outer_wallpaper_paths((Path(plan['inventory'])/metadata_row['backupFile']).read_bytes()))
    retained=[r for r in report['resources'] if r['path'] not in replaceable]
    verify_previous_files(phone,{'resources':retained})
    for key,raw in after.items():(session/(key+'.applied.json')).write_bytes(raw)
    record.update(phase='existing-record-update-and-resource-copies-acknowledged',nativeApplyPerformed=True,
        otherHistoryEntriesUnchanged=True,savedDesignCountUnchanged=True,
        unrelatedResourceHashesUnchanged=True,unrelatedResourcesChecked=len(retained),
        afterSettingsSha256={k:sha(v) for k,v in after.items()},nativePagCopySha256=sha(pag),nativePosterCopySha256=sha(poster))
    atomic_json(journal,record)
    plan.update(nativeApplyPerformed=True,phase=record['phase']);atomic_json(session/'receipt.json',plan)
    print('Existing Charlie updated: exact PAG/poster copies, unchanged slot count and all other saved designs/resources.')
    return record

def apply_update(phone,path,accepted=False):
    if accepted is not True:raise ValueError('User must authorize this reviewed update and manual restoration')
    session=session_path(path);journal=session/'native-update.json'
    if journal.exists():raise ValueError('Confirmation may have run; read back, never tap a second time')
    node=inspect_preview(phone,session)
    plan=json.loads((session/'receipt.json').read_text(encoding='utf-8'))
    before={k:(session/(k+'.before.json')).read_bytes() for k in KEYS}
    proof,pag,poster=calibrated_resources();template=update_template(proof,plan['bizId'],plan['token'])
    old_owned_resources(before,plan['bizId'])
    for key,raw in (('resourcePag',pag),('resourcePic',poster)):
        if phone.text('sha256sum '+shlex.quote(template['pets']['aiPetsData'][key])).split()[0]!=sha(raw):
            raise ValueError('Staged resource differs')
    match=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''))
    if not match:raise ValueError('Invalid confirmation bounds')
    left,top,right,bottom=map(int,match.groups())
    if not 0<=left<right<=1224 or not 0<=top<bottom<=2912:raise ValueError('Unexpected primary display geometry')
    require_unlocked(phone)
    if not re.search(r'mCommittedState=.*name=.?OPENED[\x27,]',phone.text('dumpsys device_state')):
        raise ValueError('Unfold before confirming')
    window=phone.text('dumpsys window')
    if 'mTopFocusedDisplayId=0' not in window or COMPONENT not in next((l for l in window.splitlines() if 'mCurrentFocus=' in l),'') or stable_state(phone)!=before:
        raise ValueError('Preview focus/state changed')
    record=dict(schemaVersion=1,phase='before-native-update-confirm',bizId=plan['bizId'],nativeApkSha256=PACKAGE_HASHES,
        userAcceptedUpdateAndManualRestoration=True,exactRestoreProven=False,nativeApplyPerformed=False)
    atomic_json(journal,record)
    phone.text(f'input -d 0 tap {(left+right)//2} {(top+bottom)//2}')
    record['phase']='native-update-confirm-sent-readback-pending';atomic_json(journal,record)
    deadline=time.monotonic()+20
    while True:
        try:return readback_update(phone,session)
        except ValueError:
            if time.monotonic()>=deadline:raise
            time.sleep(.5)
