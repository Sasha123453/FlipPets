"""Pure display-profile routing checks; Android SDK constants, no physical claim."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[2]
source=R/'work/app/src/org/flippets/app/NativeCoverRoute.java'
dest=R/'work/qa-final/native-route-classes';dest.mkdir(exist_ok=True)
jdk=R/'work/tools/jdk/jdk-17.0.20.1+1/bin';android=R/'work/tools/sdk/platforms/android-36/android.jar'
subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8','-classpath',str(android),'-d',str(dest),str(source),str(R/'work/tests/NativeCoverRouteTest.java')],check=True)
p=subprocess.run([str(jdk/'java.exe'),'-classpath',os.pathsep.join([str(dest),str(android)]),'org.flippets.app.NativeCoverRouteTest'],check=True,capture_output=True,text=True,encoding='utf-8')
names=p.stdout.splitlines();assert len(names)==14 and len(set(names))==14
report=dict(environment='Host JVM; pure observed-profile predicate with Android SDK constants, not Xiaomi native admission proof',sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),results=[dict(case=n,ok=True) for n in names])
(R/'work/qa-final/native-route-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
