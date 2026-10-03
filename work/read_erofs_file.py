"""Extract file bytes without copying Unix ownership/permissions onto Windows directories."""
import pathlib,subprocess,sys,hashlib,zipfile
r=pathlib.Path(__file__).resolve().parent
image,virtual,dest=sys.argv[1:]
out=pathlib.Path(dest).resolve();out.relative_to(r.parent);out.parent.mkdir(parents=True,exist_ok=True)
with out.open('wb') as stream:subprocess.run([str(r/'tools'/'erofs'/'dump.erofs.exe'),'--cat','--path='+virtual,image],stdout=stream,check=True)
if out.suffix in ['.jar','.apk','.mrc']:
    with zipfile.ZipFile(out) as z:
        bad=z.testzip();assert bad is None,bad
print(out.name,out.stat().st_size,hashlib.sha256(out.read_bytes()).hexdigest())
