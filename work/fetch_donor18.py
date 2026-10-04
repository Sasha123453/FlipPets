"""Fetch selected full-OTA partitions from Xiaomi; validate ranges and extraction hashes.

The sparse ZIP is incomplete and must never be presented as a verified flashable ROM.
Firmware bytes/checkpoints/images stay in ignored directories. No device operations.
"""
from pathlib import Path
import argparse, base64, concurrent.futures, hashlib, json, os, struct, subprocess, threading, time, urllib.request, zipfile
from payload_plan import fields

ROOT=Path(__file__).resolve().parent
NAME='hongkong-ota_full-OS4.0.15.0.XFRCNXM-user-17.0-6aad32ed35.zip'
VERSION='OS4.0.15.0.XFRCNXM'; SIZE=12318005426; CHUNK=256*1024
BASE='https://bigota.d.miui.com/'+VERSION+'/'+NAME
parser=argparse.ArgumentParser();parser.add_argument('--partitions',nargs='+',default=['product']);parser.add_argument('--plan-only',action='store_true');parser.add_argument('--workers',type=int,default=32);args=parser.parse_args();assert 1<=args.workers<=64
folder=ROOT/'firmware';folder.mkdir(exist_ok=True)
path=folder/(NAME.removesuffix('.zip')+'.partial.zip');checkpoint=path.with_suffix('.ranges.json')
done=set();lock=threading.Lock();started=time.monotonic()
if checkpoint.exists():
    previous=json.loads(checkpoint.read_text());assert previous['size']==SIZE and previous['url']==BASE
    oldChunk=previous['chunk'];assert oldChunk>=CHUNK and oldChunk%CHUNK==0
    done={i for old in previous['completed'] for i in range(old*oldChunk//CHUNK,min((old+1)*oldChunk,SIZE+CHUNK-1)//CHUNK)}
handle=path.open('r+b' if path.exists() else 'w+b');handle.truncate(SIZE)
def save():
    tmp=checkpoint.with_suffix('.tmp');tmp.write_text(json.dumps({'url':BASE,'size':SIZE,'chunk':CHUNK,'completed':sorted(done),'completeArchiveVerified':False}),encoding='utf-8');os.replace(tmp,checkpoint)
def fetch(start,end):
    for attempt in range(6):
        try:
            host=['cdnorg.d.miui.com','hugeota.d.miui.com','bigota.d.miui.com'][attempt%3]
            url=BASE.replace('bigota.d.miui.com',host)
            if attempt>=3:url+=f'?fp_range={start}-{end}'
            req=urllib.request.Request(url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity','User-Agent':'Mozilla/5.0'})
            began=time.monotonic()
            with urllib.request.urlopen(req,timeout=10) as response:
                assert response.status==206 and response.headers.get('Content-Range')==f'bytes {start}-{end}/{SIZE}', 'Wrong CDN range'
                pieces=[];remaining=end-start+1
                while remaining:
                    data=response.read(min(65536,remaining));assert data, 'Short CDN range'
                    pieces.append(data);remaining-=len(data)
                    if time.monotonic()-began>75:raise TimeoutError('Overall range timeout')
                data=b''.join(pieces);assert len(data)==end-start+1, 'Wrong CDN range size'
            with lock:handle.seek(start);handle.write(data);handle.flush()
            return
        except Exception as error:
            print('Range retry',start,end,attempt+1,type(error).__name__,str(error),flush=True)
            if attempt==5:raise
            time.sleep(min(5,attempt+1))
def chunk(index):
    if index in done:return
    fetch(index*CHUNK,min(SIZE,(index+1)*CHUNK)-1)
    with lock:
        done.add(index)
        if len(done)<5 or len(done)%128==0:save();print('Fetched',len(done),'chunks',round(len(done)*CHUNK/1024**3,2),'GiB',flush=True)
def entry_offset(entry):
    handle.seek(entry.header_offset);head=handle.read(30);n,x=struct.unpack_from('<HH',head,26);return entry.header_offset+30+n+x
try:
    chunk(0)
    if not zipfile.is_zipfile(path):fetch(SIZE-65536,SIZE-1)
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist();payload=archive.getinfo('payload.bin');assert payload.compress_type==zipfile.ZIP_STORED
        for name in ['META-INF/com/android/metadata','payload_properties.txt']:
            entry=archive.getinfo(name);start=entry_offset(entry)
            required=set(range(start//CHUNK,(start+entry.compress_size-1)//CHUNK+1))
            try:value=archive.read(name)
            except (zipfile.BadZipFile, EOFError):
                fetch(entry.header_offset,start+entry.compress_size-1);value=archive.read(name)
            if name.endswith('/metadata'):assert b'pre-device=hongkong\n' in value and b'post-sdk-level=37\n' in value
            (folder/('hongkong-'+name.rsplit('/',1)[-1]+'.txt')).write_bytes(value)
        offset=entry_offset(payload);handle.seek(offset);magic,major,length,sig=struct.unpack('>4sQQI',handle.read(24));assert magic==b'CrAU' and major==2
        for i in range(offset//CHUNK,(offset+24+length+sig-1)//CHUNK+1):chunk(i)
        handle.seek(offset+24);manifest=fields(handle.read(length));blob=offset+24+length+sig
        props=dict(line.split('=',1) for line in (folder/'hongkong-payload_properties.txt.txt').read_text().splitlines())
        handle.seek(offset);metadataBytes=handle.read(int(props['METADATA_SIZE']))
        assert hashlib.sha256(metadataBytes).digest()==base64.b64decode(props['METADATA_HASH']), 'Payload metadata hash mismatch'
        print('Verified payload metadata hash',props['METADATA_HASH'],flush=True)
    partitions={}
    for raw in manifest[13]:
        part=fields(raw);name=part[1][0].decode();indices=set();total=0
        for opraw in part.get(8,[]):
            op=fields(opraw);start=blob+op.get(2,[0])[0];size=op.get(3,[0])[0];total+=size
            if size:indices.update(range(start//CHUNK,(start+size-1)//CHUNK+1))
        info=fields(part[7][0]) if part.get(7) else {}
        partitions[name]={'chunks':sorted(indices),'compressedOperationBytes':total,'imageSize':info.get(1,[None])[0],'imageSha256':info.get(2,[b''])[0].hex()}
    print(json.dumps({n:{k:v for k,v in partitions[n].items() if k!='chunks'} for n in args.partitions},indent=2),flush=True)
    (folder/'hongkong-partition-plan.json').write_text(json.dumps(partitions,indent=2),encoding='utf-8')
    assert all(n in partitions for n in args.partitions)
    if not args.plan_only:
        wanted=set().union(*(set(partitions[n]['chunks']) for n in args.partitions));print('Required',len(wanted),'chunks; remaining',len(wanted-done),flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:list(pool.map(chunk,sorted(wanted-done)))
        save();handle.flush()
        output=ROOT/'images'/'hongkong';output.mkdir(parents=True,exist_ok=True)
        for name in args.partitions:
            dest=output/(name+'.img');assert output.resolve().is_relative_to(ROOT.resolve())
            expected=partitions[name];assert expected['imageSha256']
            def sha(p):
                h=hashlib.sha256()
                with p.open('rb') as stream:
                    for data in iter(lambda:stream.read(8*1024**2),b''):h.update(data)
                return h.hexdigest()
            if not dest.exists() or dest.stat().st_size!=expected['imageSize'] or sha(dest)!=expected['imageSha256']:
                subprocess.run([str(ROOT/'tools/payload-dumper-go.exe'),'-p',name,'-c','4','-o',str(output),str(path)],check=True)
            assert dest.stat().st_size==expected['imageSize'] and sha(dest)==expected['imageSha256'], 'Extracted partition mismatch'
            evidence={'device':'hongkong','publicVersion':VERSION,'officialArchiveUrl':BASE,'archiveSize':SIZE,'completeArchiveVerified':False,'partition':name,'partitionBytes':dest.stat().st_size,'partitionSha256':expected['imageSha256'],'operationHashesCheckedByPayloadDumper':True,'partitionHashVerified':True}
            (output/(name+'.verified-extraction.json')).write_text(json.dumps(evidence,indent=2),encoding='utf-8')
            print('Verified partition',name,expected['imageSha256'],flush=True)
finally:
    with lock:save();handle.close()
