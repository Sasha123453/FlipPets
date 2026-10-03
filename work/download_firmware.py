"""Resumable ranged downloads. Only writes inside this chat's work directory."""
import concurrent.futures as cf
import hashlib, json, os, pathlib, sys, threading, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
FILES = [
    dict(device='pandora', name='pandora-ota_full-OS3.0.319.0.WBLCNXM-user-16.0-2d01cf4d66.zip', version='OS3.0.319.0.WBLCNXM', size=8782889002, md5='2d01cf4d668c034e7be94b4772595d70'),
    dict(device='ruyi', name='ruyi_global-ota_full-OS3.0.303.0.WNIMIXM-user-16.0-0200f61ca8.zip', version='OS3.0.303.0.WNIMIXM', size=7144283082, md5='0200f61ca8f28dcdf5a4b31e08e05c41'),
]
CHUNK = 1024 * 1024
def download(info):
    dest = ROOT / 'firmware' / info['name']
    statepath = dest.with_suffix('.download.json')
    done = set()
    if statepath.exists():
        saved = json.loads(statepath.read_text())
        if saved.get('chunk_size') == CHUNK and saved.get('size') == info['size']:
            done = set(saved['completed'])
    lock = threading.Lock()
    handle = open(dest, 'r+b' if dest.exists() else 'w+b')
    handle.truncate(info['size'])
    total = (info['size'] + CHUNK - 1) // CHUNK
    started = time.monotonic()
    initial = len(done)
    def save():
        temp = statepath.with_suffix('.tmp')
        temp.write_text(json.dumps(dict(**info, chunk_size=CHUNK, completed=sorted(done))), encoding='utf-8')
        os.replace(temp, statepath)
    def one(index):
        start, end = index*CHUNK, min((index+1)*CHUNK, info['size'])-1
        for attempt in range(20):
            host = ['bn.d.miui.com', 'bigota.d.miui.com', 'hugeota.d.miui.com'][attempt % 3]
            url = f"https://{host}/{info['version']}/{info['name']}"
            req = urllib.request.Request(url, headers={'Range':f'bytes={start}-{end}', 'Accept-Encoding':'identity', 'User-Agent':'firmware-resource-research/1.0'})
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    content_range = response.headers.get('Content-Range', '')
                    if response.status != 206 or not content_range.startswith(f'bytes {start}-{end}/'):
                        raise ValueError(f'Unexpected range response {response.status}: {content_range}')
                    data = response.read(end-start+2)
                if len(data) != end-start+1: raise ValueError(f'Short range: {len(data)}')
                with lock:
                    handle.seek(start); handle.write(data); handle.flush()
                    done.add(index)
                    if len(done) % 16 == 0 or len(done) == total:
                        save()
                        elapsed = max(1, time.monotonic()-started)
                        speed = (len(done)-initial)*CHUNK/elapsed/1024**2
                        print(f"{info['device']}: {len(done)}/{total} chunks ({len(done)/total:.1%}), {speed:.2f} MiB/s", flush=True)
                return
            except Exception as error:
                if attempt in [0,5,10,19]: print(f"{info['device']} chunk {index} attempt {attempt+1}: {error}", flush=True)
                time.sleep(min(15, 1+attempt))
        raise RuntimeError(f"Failed chunk {info['device']} {index}")
    try:
        with cf.ThreadPoolExecutor(max_workers=16) as pool:
            for result in pool.map(one, (i for i in range(total) if i not in done)): pass
    finally:
        with lock: save(); handle.close()
    md5, sha = hashlib.md5(), hashlib.sha256()
    with open(dest,'rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2), b''): md5.update(block); sha.update(block)
    if md5.hexdigest() != info['md5']: raise RuntimeError(f"MD5 mismatch: {md5.hexdigest()}")
    verified = dict(**info, path=str(dest), verified_md5=md5.hexdigest(), sha256=sha.hexdigest())
    dest.with_suffix('.verified.json').write_text(json.dumps(verified, indent=2),encoding='utf-8')
    print(f"VERIFIED {info['device']}: MD5 {md5.hexdigest()} SHA256 {sha.hexdigest()}",flush=True)

if __name__ == '__main__':
    selected = [x for x in FILES if len(sys.argv)<2 or x['device']==sys.argv[1]]
    with cf.ThreadPoolExecutor(max_workers=len(selected)) as pool:
        for x in pool.map(download, selected): pass
