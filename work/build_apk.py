"""Build with the verified portable JDK/Android SDK in work/tools. No Gradle/network needed."""
import pathlib,subprocess,zipfile,hashlib,json,os,shutil
ROOT=pathlib.Path(__file__).resolve().parent
APP=ROOT/'app';BUILD=ROOT/'build';TOOLS=ROOT/'tools'
JDK=TOOLS/'jdk'/'jdk-17.0.20.1+1'/'bin';SDK=TOOLS/'sdk';BT=SDK/'build-tools'/'android-16';ANDROID=SDK/'platforms'/'android-36'/'android.jar'
LIB=TOOLS/'libpag';SHIZUKU=list((TOOLS/'shizuku').glob('*.jar'));OUT=ROOT.parent/'outputs';OUT.mkdir(exist_ok=True)
def run(*args):
    print('RUN',str(args[0]),flush=True);subprocess.run([str(x) for x in args],check=True,cwd=ROOT)
def build():
    for sub in ['res','classes','dex']:
        folder=(BUILD/sub).resolve()
        assert folder.parent==BUILD.resolve() and BUILD.resolve().is_relative_to(ROOT.resolve())
        if folder.exists():shutil.rmtree(folder)
        folder.mkdir(parents=True)
    run(BT/'aapt2.exe','compile','--dir',APP/'res','-o',BUILD/'compiled.zip')
    run(BT/'aapt2.exe','link',BUILD/'compiled.zip','-o',BUILD/'resources.apk','--manifest',APP/'AndroidManifest.xml','-I',ANDROID,'--java',BUILD/'res','-A',APP/'assets','-0','mp4','--version-code','5','--version-name','0.5')
    source=list((APP/'src').rglob('*.java'))+list((BUILD/'res').rglob('*.java'))
    run(JDK/'javac.exe','-encoding','UTF-8','-source','8','-target','8','-classpath',os.pathsep.join(str(x) for x in [ANDROID,LIB/'classes.jar',*SHIZUKU]),'-d',BUILD/'classes',*source)
    with zipfile.ZipFile(BUILD/'app-classes.jar','w') as z:
        for f in (BUILD/'classes').rglob('*.class'):z.write(f,f.relative_to(BUILD/'classes').as_posix())
    run(JDK/'java.exe','-cp',BT/'lib'/'d8.jar','com.android.tools.r8.D8','--lib',ANDROID,'--min-api','29','--output',BUILD/'dex',BUILD/'app-classes.jar',LIB/'classes.jar',*SHIZUKU)
    with zipfile.ZipFile(BUILD/'resources.apk') as src,zipfile.ZipFile(BUILD/'unsigned.apk','w',compression=zipfile.ZIP_DEFLATED) as dst:
        for entry in src.infolist():dst.writestr(entry,src.read(entry.filename))
        for f in (BUILD/'dex').glob('*.dex'):dst.write(f,f.name)
        for abi in ['arm64-v8a','x86_64']:
            for f in (LIB/'jni'/abi).glob('*.so'):dst.write(f,f'lib/{abi}/{f.name}')
    run(BT/'zipalign.exe','-f','-P','16','4',BUILD/'unsigned.apk',BUILD/'aligned.apk')
    key=ROOT/'local-signing.p12'
    if not key.exists():run(JDK/'keytool.exe','-genkeypair','-keystore',key,'-storetype','PKCS12','-storepass','local-development','-keypass','local-development','-alias','flippets','-keyalg','RSA','-keysize','3072','-validity','3650','-dname','CN=Flip Pets Local Development')
    target=OUT/'FlipPets.apk'
    run(JDK/'java.exe','-jar',BT/'lib'/'apksigner.jar','sign','--v4-signing-enabled','false','--ks',key,'--ks-key-alias','flippets','--ks-pass','pass:local-development','--out',target,BUILD/'aligned.apk')
    run(JDK/'java.exe','-jar',BT/'lib'/'apksigner.jar','verify','--verbose','--print-certs',target)
    run(BT/'zipalign.exe','-c','-P','16','4',target)
    (OUT/'FlipPets.sha256.txt').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  FlipPets.apk\n')
if __name__=='__main__':build()
