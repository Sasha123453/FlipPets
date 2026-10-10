"""Host JVM source-only native carp timeline tests; no APK build, ADB or preferences."""
from pathlib import Path
import hashlib
import json
import subprocess

root=Path(__file__).resolve().parents[2]
work=root/'work'
jdk=work/'tools/jdk/jdk-17.0.20.1+1/bin'
sources=[work/'app/src/org/flippets/app/CarpSequence.java',work/'tests/CarpSequenceTest.java']
classes=work/'review-check/carp-sequence-classes'
classes.mkdir(parents=True,exist_ok=True)
compiled=subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8','-d',str(classes),*map(str,sources)],capture_output=True,text=True,encoding='utf-8',errors='replace')
tested=subprocess.run([str(jdk/'java.exe'),'-cp',str(classes),'CarpSequenceTest'],capture_output=True,text=True,encoding='utf-8',errors='replace') if compiled.returncode==0 else None
maml=work/'review-check/hongkong-maml/e23e7933-0bd7-4d6e-9165-aae505e389cc.xml'
evidence=None
if maml.exists():
    source=maml.read_text(encoding='utf-8')
    expressions=['((719 - 30) / 719)','((600 - 30) / 600)','((596 - 30) / 596)','ease="1,500"','ease="1,300" delay="100"']
    evidence={'sha256':hashlib.sha256(maml.read_bytes()).hexdigest(),'expectedThresholdAndFadeExpressionsPresent':all(value in source for value in expressions)}
result={'scope':'Pre-build pure Java source tests; threshold/Folme timing adaptation and renderer isolation only, not native engine or APK/phone behavior','compilePassed':compiled.returncode==0,'testsPassed':tested is not None and tested.returncode==0,'stdout':None if tested is None else tested.stdout.strip(),'stderr':compiled.stderr.strip()+("\n"+tested.stderr.strip() if tested else ''),'sourceSha256':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'localVerifiedMaml':evidence}
result['passed']=result['compilePassed'] and result['testsPassed'] and (evidence is None or evidence['expectedThresholdAndFadeExpressionsPresent'])
target=work/'qa-v03/carp-sequence-tests.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['passed'] else 1)
