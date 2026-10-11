"""Host guards for original catalogue/resource preservation and stock transforms."""
import copy,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'work'))
import package_release as package
catalog=package.read(package.WORK/'app/assets/catalog.json');package.validate_mixflip_import(catalog)
for change in (lambda c:c[0].update(name='changed'),lambda c:c.pop(),lambda c:c[33]['clips'].update({'0':'pets/foreign.pag'}),lambda c:c[33].update(nativePetType=99)):
    data=copy.deepcopy(catalog);change(data)
    try:package.validate_mixflip_import(data)
    except ValueError:pass
    else:raise AssertionError('Changed catalogue accepted')
target=ROOT/'work/qa-final/mixflip-classes';target.mkdir(exist_ok=True)
jdk=ROOT/'work/tools/jdk/jdk-17.0.20.1+1/bin';src=ROOT/'work/app/src/org/flippets/app'
subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8','-d',str(target),str(src/'MixFlipGeometry.java'),str(src/'PlaybackPolicy.java'),str(ROOT/'work/tests/MixFlipGeometryTest.java')],check=True)
subprocess.run([str(jdk/'java.exe'),'-cp',str(target),'org.flippets.app.MixFlipGeometryTest'],check=True)
print('5 catalogue/provenance guard cases passed')
