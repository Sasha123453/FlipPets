"""Run pure placement invariants and validate sampled donor provenance; no ADB/UI."""
from pathlib import Path
import subprocess,json,hashlib,re

root=Path(__file__).resolve().parents[2];work=root/'work'
output=work/'review-check/cover-geometry-classes';output.mkdir(parents=True,exist_ok=True)
jdk=work/'tools/jdk/jdk-17.0.20.1+1/bin'
sources=[work/'app/src/org/flippets/app/CoverGeometry.java',work/'app/src/org/flippets/app/PetLayoutProfile.java',work/'tests/CoverGeometryTest.java']
compile_result=subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8','-d',str(output),*map(str,sources)],capture_output=True,text=True)
test_result=subprocess.run([str(jdk/'java.exe'),'-cp',str(output),'CoverGeometryTest'],capture_output=True,text=True) if compile_result.returncode==0 else None
samples=json.loads((work/'qa-v03/pet-envelope-samples.json').read_text())
matched=all(hashlib.sha256((work/'app/assets'/path).read_bytes()).hexdigest()==sha for path,sha in samples['sourceSha256'].items())
metadata=work/'app/assets/pet-envelopes.json'
record={'scope':'Pre-build source tests: pure aspect/placement invariants and offline donor-asset provenance; not APK/UI or physical camera validation','compilePassed':compile_result.returncode==0,'testsPassed':test_result is not None and test_result.returncode==0,'stdout':None if test_result is None else test_result.stdout.strip(),'sourceSha256':{str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[metadata]},'sampledPAGAssets':len(samples['sourceSha256']),'allSampledSourceHashesMatch':matched}
(work/'qa-v03/cover-geometry-tests.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,indent=2))
raise SystemExit(0 if record['compilePassed'] and record['testsPassed'] and matched else 1)
