"""Synthetic filesystem tests for donor import; not artwork/runtime/device QA."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'prepare_donor18.py'
spec = importlib.util.spec_from_file_location('donor18', SCRIPT)
donor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(donor)

HOLD = '''<Widget><Var name="assets" expression="'bird'"/><Function name="onComplete"><FrameRateCommand rate="0"/></Function><PagView loop="1"/></Widget>'''


class ImportTests(unittest.TestCase):
    def test_reactive_event_numbers_actions_and_delay_are_contract_changes(self):
        original = ET.fromstring('''<Widget><Var name="level_rule" values="1,8,7,6,5,4,3,2"/><Var name="music"><Trigger><IfCommand ifCondition="#music_state"><VariableCommand name="event_index" expression="3"/><FunctionCommand target="switchPag" delay="1000"/></IfCommand></Trigger></Var><Function name="switchPag"><PagCommand target="pet" command="play"/></Function><PagView name="pet" loop="1"/></Widget>''')
        baseline = donor.reactive_contract(original)
        for tag, attribute, value in [('VariableCommand', 'expression', '5'), ('PagCommand', 'command', 'pause'), ('FunctionCommand', 'delay', '2000'), ('IfCommand', 'ifCondition', '! #music_state')]:
            changed = ET.fromstring(ET.tostring(original))
            changed.find('.//' + tag).set(attribute, value)
            self.assertNotEqual(donor.reactive_contract(changed), baseline)

    def test_reactive_dependent_constants_and_callback_links_are_checked(self):
        original = ET.fromstring('''<Widget><Var name="delay_ms" expression="1000"/><Var name="intermediate" expression="#delay_ms"/><Function name="onComplete"><FunctionCommand target="switchPag" delay="#intermediate"/></Function><FolmeConfig name="cfg" onComplete="'onComplete'"/><PagView name="pet" loop="1"/></Widget>''')
        baseline = donor.reactive_contract(original)
        changed = ET.fromstring(ET.tostring(original))
        changed.find("Var[@name='delay_ms']").set('expression', '2500')
        self.assertNotEqual(donor.reactive_contract(changed), baseline)
        changed = ET.fromstring(ET.tostring(original))
        changed.find('FolmeConfig').set('onComplete', "'different'")
        self.assertNotEqual(donor.reactive_contract(changed), baseline)

    def test_finite_hold_is_not_converted_to_loop(self):
        kind, policy, count, _ = donor.playback(ET.fromstring(HOLD), 'bird', ['assets/bird/pag_0.pag'])
        self.assertEqual((kind, count), ('ambient', 1))
        self.assertIn('hold', policy)

    def test_unknown_single_cycle_policy_is_not_silently_looped(self):
        kind, *_ = donor.playback(ET.fromstring('<Widget><PagView loop="1"/></Widget>'), 'unknown', ['a.pag'])
        self.assertIsNone(kind)

    def test_classic_completion_indirect_replay_is_not_a_hold(self):
        tree = ET.fromstring('''<Widget><Function name="onComplete"><FrameRateCommand rate="0"/><FunctionCommand target="restart"/></Function><Function name="restart"><PagCommand target="pet" command="play"/></Function><PagView loop="1"/></Widget>''')
        kind, *_ = donor.playback(tree, 'bird', ['pag_0.pag'])
        self.assertIsNone(kind)

    def test_unsafe_archive_names_rejected(self):
        for name in ('../escape.pag', '/absolute.pag', 'assets\\bad.pag'):
            with self.assertRaises(ValueError):
                donor.safe_member(name)

    def fixture(self, root):
        assets = root / 'app/assets'
        (assets / 'pets/old').mkdir(parents=True)
        (assets / 'pets/old/shared.pag').write_bytes(b'old shared media')
        old = [{'id': 'bird-pandora', 'kind': 'ambient', 'clips': {'0': 'pets/old/shared.pag'}, 'customField': 'retain'}, {'id': 'existing-composition', 'kind': 'composition', 'clips': {}, 'renderer': 'photo'}]
        (assets / 'catalog.json').write_text(json.dumps(old))
        source = root / 'extracted/hongkong/rearscreen'
        (source / 'content').mkdir(parents=True)
        for uid in ('first', 'second'):
            with zipfile.ZipFile(source / 'content' / (uid + '.mrc'), 'w') as z:
                z.writestr('manifest.xml', HOLD)
                z.writestr('assets/bird/pag_0.pag', b'old shared media')
                z.writestr('assets/bird/pag_1.pag', b'new media')
        return assets, source, old

    def test_plan_reuses_overlap_and_aliases_second_set_without_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assets, source, old = self.fixture(root)
            with patch.object(donor, 'WORK', root), patch.object(donor, 'ASSETS', assets), patch.object(sys, 'argv', ['prepare_donor18.py', '--source-root', str(source)]):
                donor.main()
            report = json.loads((source / 'import-plan.json').read_text())
            self.assertEqual(report['newCatalogueEntries'], 1)
            self.assertEqual(report['newUniqueMedia'], 1)
            self.assertEqual(report['decisions'][1]['decision'], 'exact-media-set-alias')
            self.assertEqual(report['decisions'][0]['reusedMediaAssetPaths'], ['pets/old/shared.pag'])
            self.assertEqual(json.loads((assets / 'catalog.json').read_text()), old)
            self.assertFalse((assets / 'pets/bird-hongkong').exists())

    def test_apply_requires_verified_provenance_before_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assets, source, old = self.fixture(root)
            with patch.object(donor, 'WORK', root), patch.object(donor, 'ASSETS', assets), patch.object(sys, 'argv', ['prepare_donor18.py', '--source-root', str(source), '--apply', '--allow-missing-thumbnail']):
                with self.assertRaises(ValueError):
                    donor.main()
            self.assertEqual(json.loads((assets / 'catalog.json').read_text()), old)
            self.assertFalse((assets / 'pets/bird-hongkong').exists())


if __name__ == '__main__':
    unittest.main()
