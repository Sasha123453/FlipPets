"""Registry, extension-draft and shared native/app transform guards; no ADB."""
from copy import deepcopy
import json,subprocess,unittest
from shared_pet_layout import ROOT,REGISTRY,validate_registry,propose

class SharedLayouts(unittest.TestCase):
    def setUp(self):self.value=json.loads(REGISTRY.read_text(encoding='utf-8'))
    def test_active_registry(self):validate_registry(self.value)
    def test_source_and_schema_changes_rejected(self):
        for key,value in (('sourceCanvas',[0,596]),('referenceSourceSha256','0'*64),('scale',float('nan')),('x',9999),('subjectRight',0)):
            data=deepcopy(self.value);data['layouts']['bird-pandora'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_registry(data)
    def test_stock_and_unsupported_pets_cannot_be_overridden(self):
        for pet_id in ('mixflip-dewen','unknown','system-effects','vortex-hongkong'):
            data=deepcopy(self.value);data['layouts'][pet_id]=data['layouts'].pop('bird-pandora')
            with self.subTest(pet_id=pet_id),self.assertRaises(ValueError):validate_registry(data)
    def test_new_candidate_requires_every_scene_decode(self):
        with self.assertRaises(ValueError):propose('bird-pandora',{'clips':[]},[365,112,812,574])
    def test_java_native_anchor_and_manual_profiles(self):
        target=ROOT/'work/qa-final/shared-geometry-classes';target.mkdir(exist_ok=True)
        jdk=ROOT/'work/tools/jdk/jdk-17.0.20.1+1/bin';src=ROOT/'work/app/src/org/flippets/app'
        subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8','-d',str(target),str(src/'CoverGeometry.java'),str(src/'PetLayoutProfile.java'),str(ROOT/'work/tests/SharedPetGeometryTest.java')],check=True)
        p=self.value['layouts']['bird-pandora']
        subprocess.run([str(jdk/'java.exe'),'-cp',str(target),'org.flippets.app.SharedPetGeometryTest',*[str(p[k]) for k in ('scale','x','y')]],check=True)

if __name__=='__main__':unittest.main(verbosity=2)
