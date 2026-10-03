"""Extract a partition only after all its bytes were checkpointed, verifying operation and final hashes."""
import pathlib,subprocess,time,json
from payload_plan import plan
from download_firmware import FILES,ROOT
todo={'ruyi':['odm','product','system_ext','vendor','system','mi_ext'],'pandora':['odm','product','system_ext','system','mi_ext']}
remaining=sum(map(len,todo.values()))
while remaining:
    progress=False
    for info in FILES[::-1]:
        ready={x['name']:x['ready'] for x in plan(info)}
        for name in list(todo[info['device']]):
            if not ready[name]:continue
            out=ROOT/'images'/info['device'];out.mkdir(parents=True,exist_ok=True)
            print('EXTRACTING',info['device'],name,flush=True)
            subprocess.run([str(ROOT/'tools'/'payload-dumper-go.exe'),'-p',name,'-c','4','-o',str(out),str(ROOT/'firmware'/info['name'])],check=True)
            (out/(name+'.verified-extraction.json')).write_text(json.dumps(dict(device=info['device'],partition=name,tool='payload-dumper-go 2.1.0',operation_hash_checks=True,partition_hash_check=True)))
            todo[info['device']].remove(name);remaining-=1;progress=True
            print('EXTRACTED VERIFIED',info['device'],name,'remaining',remaining,flush=True)
    if not progress:time.sleep(10)
