"""Offline guards for the existing-record Charlie preview; no phone operations."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch
from native_pet_update import (ROOT,calibrated_resources,update_template,session_path,
    update_control,verify_previous_files,CANDIDATE_SHA,unchanged_other_history,editor_present,apply_update)
from native_pet_apply import native_update_index
from prepare_native_template import make_template,STAGING_ROOT,sha

class UpdatePreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof,cls.pag,cls.poster=calibrated_resources()
        cls.biz='flippets-charlie-'+'a'*32
        cls.token='b'*32

    def test_exact_decoded_candidate(self):
        self.assertEqual(sha(self.pag),CANDIDATE_SHA)
        self.assertEqual(len({f['png'] for f in self.proof['frames']}),8)

    def test_only_resource_paths_change_in_template(self):
        expected=make_template(self.proof,self.biz,'composite')
        actual=update_template(self.proof,self.biz,self.token)
        paths=actual['pets']['aiPetsData']
        expected['pets']['aiPetsData'].update(resourcePag=paths['resourcePag'],resourcePic=paths['resourcePic'])
        self.assertEqual(actual,expected)
        self.assertEqual(paths['resourcePag'],STAGING_ROOT+self.biz+'/updates/'+self.token+'/native.pag')

    def test_path_injection_rejected(self):
        for token in ('../x','a'*31,'A'*32,'b'*32+'/x',''):
            with self.subTest(token=token),self.assertRaises(ValueError):update_template(self.proof,self.biz,token)
        for biz in ('foreign','../owned','flippets-charlie-'+'a'*32+'/x'):
            with self.subTest(biz=biz),self.assertRaises(ValueError):update_template(self.proof,biz,self.token)

    def test_session_is_direct_owned_child(self):
        good=ROOT/'work/phone-qa'/('pet-update-'+self.token)
        self.assertEqual(session_path(good),good.resolve())
        for path in (ROOT/good.name,good/'nested'/good.name,good.parent/('pet-update-'+self.token.upper())):
            with self.subTest(path=path),self.assertRaises(ValueError):session_path(path)

    def test_quota_never_falls_back_to_add(self):
        entry={'clockInfo':{'templateId':'ai_pets'},'pets':{'petCategory':2,'aiPetsData':{'bizId':self.biz}}}
        self.assertEqual(native_update_index(json.dumps([{},entry,{}]),self.biz),1)
        for history in ([],[entry,entry],[{'pets':{'aiPetsData':{'bizId':self.biz}}}]):
            with self.subTest(history=history),self.assertRaises(ValueError):native_update_index(json.dumps(history),self.biz)

    def controls(self,**changes):
        attrs={'package':'com.miui.aod','resource-id':'com.miui.aod:id/confirm','text':'Готово','enabled':'true','clickable':'true'}
        attrs.update(changes)
        return ('<hierarchy><node '+' '.join(k+'="'+v+'"' for k,v in attrs.items())+'/></hierarchy>').encode('utf-8')

    def test_only_enabled_oem_update_accepted(self):
        self.assertEqual(update_control(self.controls()).get('text'),'Готово')
        for changes in ({'text':'Добавить'},{'text':'Применить'},{'enabled':'false'},{'clickable':'false'},{'package':'other'},{'resource-id':'other'}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):update_control(self.controls(**changes))

    def test_ambiguous_or_unsafe_controls_rejected(self):
        valid=self.controls()
        for raw in (b'',valid.replace(b'</hierarchy>',valid+b'</hierarchy>'),b'<!DOCTYPE x>'+valid,b'x'*(2*1024*1024+1)):
            with self.subTest(size=len(raw)),self.assertRaises(ValueError):update_control(raw)

    def test_changed_native_resource_blocks_preview(self):
        class Fake:
            def text(self,command):return 'b'*64+' resource'
        with self.assertRaises(ValueError):verify_previous_files(Fake(),{'resources':[{'path':'/data/system/theme_magic/users/0/wallpaper/a','sha256':'a'*64}]})

    def test_modified_candidate_rejected(self):
        from pathlib import Path
        original=Path.read_bytes
        def read(path):
            raw=original(path)
            return raw+b'x' if path.name=='candidate.pag' else raw
        with patch.object(Path,'read_bytes',read),self.assertRaises(ValueError):calibrated_resources()

    def test_unapproved_update_never_contacts_phone(self):
        class Fake:
            def __getattr__(self,name):raise AssertionError('Unexpected phone contact')
        with self.assertRaises(ValueError):apply_update(Fake(),'anything')

    def test_other_history_and_count_must_survive_update(self):
        row={'clockInfo':{'templateId':'ai_pets'},'pets':{'petCategory':2,'aiPetsData':{'bizId':self.biz,'resourcePag':'old'}}}
        new=deepcopy(row);new['pets']['aiPetsData']['resourcePag']='new'
        before=[{'private':'first'},row,{'private':'second'}]
        after=[new,before[0],before[2]]
        self.assertEqual(unchanged_other_history(json.dumps(before),json.dumps(after),self.biz),new)
        for bad in (after+[{}],[new,{'private':'changed'},before[2]],[new,before[2],before[0]],[new,new]):
            with self.subTest(bad=bad),self.assertRaises(ValueError):unchanged_other_history(json.dumps(before),json.dumps(bad),self.biz)

    def test_editor_in_background_still_counts_as_present(self):
        name='com.miui.tinykeyguard.editor.edit.EditActivity'
        for line in ('Hist #0: ActivityRecord{abc u0 com.miui.aod/'+name+' t123}', 'realActivity=com.miui.aod/'+name):
            self.assertTrue(editor_present(line))
        self.assertFalse(editor_present('mCurrentFocus=other'))

if __name__=='__main__':unittest.main(verbosity=2)
