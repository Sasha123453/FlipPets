"""Build a small, temporary per-display accessibility dumper for physical UI tests."""
from pathlib import Path
import subprocess,zipfile
root=Path(__file__).resolve().parents[1]
build=root/'uiqa-build';(build/'classes').mkdir(parents=True,exist_ok=True);(build/'dex').mkdir(exist_ok=True)
jdk=root/'tools/jdk/jdk-17.0.20.1+1/bin';bt=root/'tools/sdk/build-tools/android-16';android=root/'tools/sdk/platforms/android-36/android.jar'
def run(*args):subprocess.run(list(map(str,args)),check=True)
run(jdk/'javac.exe','-encoding','UTF-8','-classpath',android,'-d',build/'classes',root/'tests/uiqa/DumpUi.java')
with zipfile.ZipFile(build/'classes.jar','w') as z:
    for f in (build/'classes').rglob('*.class'):z.write(f,f.relative_to(build/'classes').as_posix())
run(jdk/'java.exe','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--lib',android,'--min-api','30','--output',build/'dex',build/'classes.jar')
run(bt/'aapt2.exe','link','--manifest',root/'tests/uiqa/AndroidManifest.xml','-I',android,'-o',build/'res.apk')
with zipfile.ZipFile(build/'res.apk') as src,zipfile.ZipFile(build/'unsigned.apk','w') as dst:
    for item in src.infolist():dst.writestr(item,src.read(item.filename))
    dst.write(build/'dex/classes.dex','classes.dex')
run(bt/'zipalign.exe','-f','4',build/'unsigned.apk',build/'aligned.apk')
run(jdk/'java.exe','-jar',bt/'lib/apksigner.jar','sign','--v4-signing-enabled','false','--ks',root/'local-signing.p12','--ks-pass','pass:local-development','--out',build/'uiqa.apk',build/'aligned.apk')
print('Temporary helper built:',build/'uiqa.apk')
