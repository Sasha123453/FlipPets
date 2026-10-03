"""Minimal protobuf wire reader for payload manifests, using the documented AOSP field numbers.
Only metadata planning; actual extraction and SHA-256 validation uses payload-dumper-go.
"""
import json,pathlib,struct,zipfile
from download_firmware import FILES,ROOT,CHUNK
def varint(data,pos):
    value=shift=0
    while True:
        b=data[pos];pos+=1;value|=(b&127)<<shift
        if not b&128:return value,pos
        shift+=7
def fields(data):
    pos=0;out={}
    while pos<len(data):
        tag,pos=varint(data,pos);field,wire=tag>>3,tag&7
        if wire==0:value,pos=varint(data,pos)
        elif wire==2:n,pos=varint(data,pos);value=data[pos:pos+n];pos+=n
        elif wire in (1,5):n=8 if wire==1 else 4;value=data[pos:pos+n];pos+=n
        else:raise ValueError(wire)
        out.setdefault(field,[]).append(value)
    return out
def plan(info):
    file=ROOT/'firmware'/info['name'];state=json.loads(file.with_suffix('.download.json').read_text());done=set(state['completed'])
    with zipfile.ZipFile(file) as z:
        entry=z.getinfo('payload.bin')
        with file.open('rb') as stream:
            stream.seek(entry.header_offset);head=stream.read(30);_,_,_,_,_,_,_,_,_,n,x=struct.unpack('<IHHHHHIIIHH',head);offset=entry.header_offset+30+n+x
            stream.seek(offset);header=stream.read(24);magic,major,length,sig=struct.unpack('>4sQQI',header);assert magic==b'CrAU' and major==2
            manifest=fields(stream.read(length));blob=offset+24+length+sig
    result=[]
    for part in manifest[13]:
        f=fields(part);name=f[1][0].decode();chunks=set();ranges=[]
        for operation in f.get(8,[]):
            op=fields(operation);start=op.get(2,[0])[0]+blob;size=op.get(3,[0])[0]
            if size:chunks.update(range(start//CHUNK,(start+size-1)//CHUNK+1));ranges.append((start,size))
        result.append(dict(name=name,requiredChunks=len(chunks),missingChunks=len(chunks-done),minOffset=min((x[0] for x in ranges),default=0),maxOffset=max((x[0]+x[1] for x in ranges),default=0),ready=not bool(chunks-done)))
    return result
if __name__=='__main__':
    for info in FILES:
        report=plan(info);(ROOT/'research'/f"{info['device']}-payload-plan.json").write_text(json.dumps(report,indent=2))
        print(info['device'],*[x for x in report if x['name'] in ['system','system_ext','vendor','odm','product','mi_ext']],sep='\n')
