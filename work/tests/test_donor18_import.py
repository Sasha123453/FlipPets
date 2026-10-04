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
    def test_finite_hold_is_not_converted_to_loop(self):
        kind, policy, count, _ = donor.playback(ET.fromstring(HOLD), 'bird', ['assets/bird/pag_0.pag'])
        self.assertEqual((kind, count), ('ambient', 1))
        self.assertIn('hold', policy)

    def test_unknown_single_cycle_policy_is_not_silently_looped(self):
        kind, *_ = donor.playback(ET.fromstring('<Widget><PagView loop="1"/></Widget>'), 'unknown', ['a.pag'])
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
