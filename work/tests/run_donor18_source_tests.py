"""Current APK-bound source invariants, donor import tests and source MAML provenance."""
from pathlib import Path
import hashlib,json,subprocess,sys
root=Path(__file__).resolve().parents[2];work=root/'work'
apk=root/'outputs/FlipPets.apk'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
binary=sha(apk);results=[]
for name in ['run_cover_geometry_tests.py','run_carp_sequence_tests.py']:
    run=subprocess.run([sys.executable,'-X','utf8',str(work/'tests'/name)],capture_output=True,text=True,encoding='utf-8')
    results.append({'test':name,'ok':run.returncode==0,'detail':run.stdout.strip(),'stderr':run.stderr.strip()})
jdk=work/'tools/jdk/jdk-17.0.20.1+1/bin';classes=work/'review-check/playback-classes';classes.mkdir(parents=True,exist_ok=True)
files=[work/'app/src/org/flippets/app/PlaybackPolicy.java',work/'tests/PlaybackPolicyTest.java']
compile_run=subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8','-d',str(classes),*map(str,files)],capture_output=True,text=True)
run=subprocess.run([str(jdk/'java.exe'),'-cp',str(classes),'PlaybackPolicyTest'],capture_output=True,text=True) if compile_run.returncode==0 else None
results.append({'test':'PlaybackPolicyTest','ok':run is not None and run.returncode==0,'detail':run.stdout.strip() if run else compile_run.stderr})
run=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s',str(work/'tests'),'-p','test_donor18_import.py'],capture_output=True,text=True,encoding='utf-8')
results.append({'test':'DonorImportFilesystem8Cases','ok':run.returncode==0,'detail':run.stderr.strip()})
sources={p.relative_to(root).as_posix():sha(p) for p in files+[work/'tests/test_donor18_import.py',work/'prepare_donor18.py']}
for name in ['cover-geometry-tests.json','carp-sequence-tests.json']:
    record=json.loads((work/'qa-v03'/name).read_text(encoding='utf-8'))
    sources.update(record['sourceSha256'])
    assert record['compilePassed'] and record['testsPassed']
assert all(sha(root/p)==s for p,s in sources.items())
assert binary==sha(apk)
record={'apkSha256':binary,'scope':'Host JVM geometry/playback/carp and8 synthetic filesystem-import cases, source hashes only; no Android/phone/UI proof. Source probes used1.0 renderer separately.','tested':len(results),'failed':sum(not r['ok'] for r in results),'passed':all(r['ok'] for r in results),'source_sha256':sources,'results':results}
(work/'qa-v03/donor18-source-v110.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'tested':len(results),'failed':record['failed'],'apkSha256':binary},indent=2))
raise SystemExit(0 if record['passed'] else 1)
