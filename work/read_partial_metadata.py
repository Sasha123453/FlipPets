"""Read the ZIP central directory early. Does not mark the whole download verified."""
import pathlib,json,urllib.request,zipfile
from download_firmware import FILES,ROOT
for info in FILES:
    file=ROOT/'firmware'/info['name'];start=info['size']-1024*1024
    for host in ['bigota.d.miui.com','hugeota.d.miui.com','bn.d.miui.com']:
        try:
            req=urllib.request.Request(f"https://{host}/{info['version']}/{info['name']}",headers={'Range':f"bytes={start}-{info['size']-1}",'Accept-Encoding':'identity'})
            with urllib.request.urlopen(req,timeout=20) as response:
                if response.status!=206 or not response.headers.get('Content-Range','').startswith(f'bytes {start}-'):raise ValueError('Bad tail range')
                tail=response.read()
            if len(tail)!=1024*1024:raise ValueError('Short tail')
            with file.open('r+b') as out:out.seek(start);out.write(tail)
            break
        except Exception as e: print(info['device'],host,type(e).__name__,flush=True)
    else:continue
    with zipfile.ZipFile(file) as z:
        listing=[dict(name=x.filename,size=x.file_size,compressed=x.compress_size,offset=x.header_offset,method=x.compress_type) for x in z.infolist()]
        (ROOT/'research'/f"{info['device']}-zip-list.json").write_text(json.dumps(listing,indent=2))
        for name in ['META-INF/com/android/metadata','payload_properties.txt']:
            try:(ROOT/'research'/f"{info['device']}-{name.split('/')[-1]}.txt").write_bytes(z.read(name))
            except Exception as e:print('metadata',name,e,flush=True)
        print(info['device'],listing,flush=True)
