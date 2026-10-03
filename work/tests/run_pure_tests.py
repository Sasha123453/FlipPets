from pathlib import Path
import subprocess, json, hashlib, datetime, re

root=Path(__file__).resolve().parents[2]
work=root/'work'; target=root/'outputs'/'FlipPets.apk'
output=work/'review-check'/'classes';output.mkdir(parents=True,exist_ok=True)
jdk=work/'tools'/'jdk'/'jdk-17.0.20.1+1'/'bin'
files=[work/'app'/'src'/'org'/'flippets'/'app'/'TimerState.java',work/'app'/'src'/'org'/'flippets'/'app'/'HingeOpacity.java',work/'tests'/'TimerStateTest.java',work/'tests'/'HingeOpacityTest.java']
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sha=digest(target)
compile_result=subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8','-d',str(output),*map(str,files)],capture_output=True,text=True,encoding='utf-8',errors='replace')
tests=[]
if compile_result.returncode==0:
    for name in ['TimerStateTest','HingeOpacityTest']:
        r=subprocess.run([str(jdk/'java.exe'),'-cp',str(output),name],capture_output=True,text=True,encoding='utf-8',errors='replace')
        case={'suite':name,'passed':r.returncode==0,'exit_code':r.returncode,'stdout':r.stdout.strip(),'stderr':r.stderr.strip()}
        match=re.search(r'(\d+) assertions passed',r.stdout)
        if match:case['assertions']=int(match.group(1))
        tests.append(case)
same=sha==digest(target)
result={'artifact':'FlipPets.apk','apk_version':'0.9.1','apk_sha256':sha,'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Host JVM pure timer and hinge-opacity logic only; no Android lifecycle, display hardware, or UI automation','compile':{'passed':compile_result.returncode==0,'exit_code':compile_result.returncode,'stdout':compile_result.stdout.strip(),'stderr':compile_result.stderr.strip()},'source_sha256':{str(p.relative_to(root)).replace('\\','/'):digest(p) for p in files},'suites':tests,'total_suites':2,'passed_suites':sum(t['passed'] for t in tests),'apk_unchanged_during_run':same,'passed':compile_result.returncode==0 and len(tests)==2 and all(t['passed'] for t in tests) and same}
path=work/'qa-v03'/'pure-tests-v091.json';path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if result['passed'] else 1)
