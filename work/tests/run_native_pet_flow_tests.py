"""Host-only Charlie input, OEM geometry and interruption design checks."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from subprocess import CompletedProcess
from native_pet_geometry import translation_by_axes, systemui_translation, editor_position
from prepare_native_template import verify_bundle, make_template, validate_template, axes, prepare
from native_pet_transaction_model import plan, atomic_json, read, advance
from prepare_native_composite import compose, tags
from native_pet_preview import (native_path, stable_state, private_session,
    outer_wallpaper_paths, provider_query_status, verified_inventory,
    validate_restore_preview_template, WALLPAPER_METADATA, NATIVE_ROOT, PACKAGE_HASHES)
from prepare_native_template import sha, ROOT
from native_pet_apply import check_native_add_quota, native_update_index

TEST_TEMP = Path(__file__).resolve().parents[1] / 'qa-final/native-pet-flow-temp'
assert Path(__file__).resolve().parents[2] in TEST_TEMP.resolve().parents
TEST_TEMP.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(TEST_TEMP)


class NativePetFlow(unittest.TestCase):
    def test_update_plan_uses_only_unique_owned_biz_id_at_full_quota(self):
        owned='flippets-charlie-'+'a'*32
        entry={'clockInfo':{'templateId':'ai_pets'},'pets':{'petCategory':2,'aiPetsData':{'bizId':owned}}}
        history=[{'pets':{'petType':2}},{'pets':{'petType':1}},entry]+[{} for _ in range(6)]
        self.assertEqual(native_update_index(json.dumps(history),owned),2)
        for invalid in (history+[entry],history[:2],history[:2]+[entry,entry]):
            with self.assertRaises(ValueError):native_update_index(json.dumps(invalid),owned)
        with self.assertRaises(ValueError):native_update_index(json.dumps(history),'foreign-id')

    def test_calibrated_wrapper_keeps_donor_payload_and_bounds_transform(self):
        from prepare_native_composite import compose, tags
        background=(ROOT/'work/app/assets/pets/bird-pandora/bg.webp').read_bytes()
        candidate=compose(self.pag,background,(2.220779,-663.2727,117.2727))
        before=[p for c,p in tags(self.pag,9) if c==2]
        after=[p for c,p in tags(candidate,9) if c==2]
        self.assertTrue(all(p in after for p in before))
        for transform in ((float('nan'),0,0),(4,0,0),(2,-9999,0)):
            with self.assertRaises(ValueError):compose(self.pag,background,transform)
    @classmethod
    def setUpClass(cls):
        cls.proof, cls.pag, cls.poster = verify_bundle()
        cls.id = 'flippets-charlie-' + '1' * 32

    def test_original_bundle_and_poster(self):
        self.assertEqual((self.proof['width'], self.proof['height']), (976, 596))
        self.assertTrue(self.poster.startswith(b'\x89PNG\r\n\x1a\n'))

    def test_actual_wallpaper_paths_are_separate_dependencies(self):
        raw = ('<wallpaper_data which="8" type="rotation_image" pathSize="2" '
               f'path0="{NATIVE_ROOT}rotation0" path1="{NATIVE_ROOT}rotation180"/>').encode()
        self.assertEqual(outer_wallpaper_paths(raw),
                         [NATIVE_ROOT + 'rotation0', NATIVE_ROOT + 'rotation180'])

    def test_wallpaper_metadata_rejects_incomplete_or_foreign_targets(self):
        valid = f'<wallpaper_data which="8" pathSize="1" path0="{NATIVE_ROOT}image"/>'
        bad = [valid.replace('which="8"', 'which="2"'), valid.replace('pathSize="1"', 'pathSize="2"'),
               valid.replace('path0=', 'path1='), valid.replace(NATIVE_ROOT, '/sdcard/'),
               valid.replace('image', '../image'), valid.replace('pathSize="1"', 'pathSize="999"'),
               '<!DOCTYPE x [<!ENTITY a "x">]>' + valid, '<wallpaper_data',
               valid.replace('/>', '><extra/></wallpaper_data>')]
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                outer_wallpaper_paths(raw.encode())

    def test_provider_permission_denial_even_with_zero_exit(self):
        raw = (b'java.lang.SecurityException: Permission Denial: opening provider '
               b'com.miui.keyguard.editor.data.template.TemplateFileProvider from (null) '
               b'(pid=1, uid=2000) requires miui.keyguard.editor.WRITE_EDITOR_FILE')
        self.assertEqual(provider_query_status(CompletedProcess([], 0, raw, b'')), 'denied-by-permission')

    def test_provider_query_never_establishes_write_capability(self):
        self.assertEqual(provider_query_status(CompletedProcess([], 0, b'No result found.\n', b'')),
                         'reachable-query-only-writing-unproven')
        for result in (CompletedProcess([], 0, b'', b''), CompletedProcess([], 0, b'adb: offline', b''),
                       CompletedProcess([], 1, b'No result found.\n', b'')):
            self.assertEqual(provider_query_status(result), 'unverified-transport-or-provider-result')

    def inventory_fixture(self, root):
        folder = root / 'work/phone-qa' / ('pet-inventory-' + '1' * 32)
        folder.mkdir(parents=True)
        state = {'current_tiny_keyguard_info': b'{"clockInfo":{"templateId":"splicing"}}\n',
                 'all_tiny_keyguard_info': b'[]\n'}
        for key, data in state.items():
            (folder / (key + '.json')).write_bytes(data)
        wallpaper = (f'<wallpaper_data which="8" pathSize="2" '
                     f'path0="{NATIVE_ROOT}rotation0" path1="{NATIVE_ROOT}rotation180"/>').encode()
        rows = []
        for index, (path, raw) in enumerate(((WALLPAPER_METADATA, wallpaper),
                (NATIVE_ROOT + 'rotation0', b'first'), (NATIVE_ROOT + 'rotation180', b'second'))):
            name = f'resource-{index:03}.bin'
            (folder / name).write_bytes(raw)
            rows.append(dict(path=path, backupFile=name, bytes=len(raw), sha256=sha(raw)))
        report = dict(schemaVersion=2, nativeApkSha256=PACKAGE_HASHES, unknownPathCount=0,
                      nativeApplyAllowed=False, resources=rows, outerWallpaperResourceCount=2)
        (folder / 'inventory.json').write_text(json.dumps(report), encoding='utf-8')
        return folder, state, report

    def test_inventory_requires_both_wallpaper_image_backups(self):
        with tempfile.TemporaryDirectory() as temp, patch('native_pet_preview.ROOT', Path(temp)):
            folder, state, report = self.inventory_fixture(Path(temp))
            self.assertEqual(len(verified_inventory(folder, state)['resources']), 3)
            report['resources'].pop()
            (folder / 'inventory.json').write_text(json.dumps(report), encoding='utf-8')
            with self.assertRaises(ValueError):
                verified_inventory(folder, state)

    def test_inventory_refuses_changed_resource_bytes_or_later_choice(self):
        with tempfile.TemporaryDirectory() as temp, patch('native_pet_preview.ROOT', Path(temp)):
            folder, state, report = self.inventory_fixture(Path(temp))
            newer = dict(state, all_tiny_keyguard_info=b'[{"laterChoice":true}]\n')
            with self.assertRaises(ValueError):
                verified_inventory(folder, newer)
            (folder / report['resources'][1]['backupFile']).write_bytes(b'changed')
            with self.assertRaises(ValueError):
                verified_inventory(folder, state)

    def test_inventory_rejects_wrong_profile_and_unbacked_files(self):
        with tempfile.TemporaryDirectory() as temp, patch('native_pet_preview.ROOT', Path(temp)):
            folder, state, report = self.inventory_fixture(Path(temp))
            for mutate in ('profile', 'missing', 'escape'):
                changed = deepcopy(report)
                if mutate == 'profile':
                    changed['nativeApkSha256'] = {}
                elif mutate == 'missing':
                    changed['resources'][1].pop('backupFile')
                else:
                    changed['resources'][1]['backupFile'] = '../outside.bin'
                (folder / 'inventory.json').write_text(json.dumps(changed), encoding='utf-8')
                with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                    verified_inventory(folder, state)

    def test_restore_preview_preserves_valid_crop_json(self):
        matrix = [0.8, 0, -100, 0, 0.8, -10, 0, 0, 1]
        template = dict(clockInfo=dict(templateId='splicing'),
                        wallpaperInfo0=dict(positionInfo=dict(matrixArr=matrix)),
                        wallpaperInfo180=dict(positionInfo=dict(matrixArr=matrix)))
        self.assertEqual(validate_restore_preview_template(json.dumps(template).encode()), template)

    def test_restore_preview_refuses_missing_and_invalid_crop_arrays(self):
        for matrix in (None, [], [1] * 8, [True] * 9, [float('nan')] * 9,
                       [0, 0, 0, 0, 0, 0, 0, 0, 1]):
            template = dict(clockInfo=dict(templateId='splicing'),
                            wallpaperInfo0=dict(positionInfo=dict(left=0, top=0, right=1208,
                                bottom=1392, matrixArr=matrix)), wallpaperInfo180={})
            with self.subTest(matrix=matrix), self.assertRaises(ValueError):
                validate_restore_preview_template(json.dumps(template).encode())

    def test_native_add_respects_pet_and_total_history_limits(self):
        check_native_add_quota(json.dumps([dict(pets={}), dict(pets={}), {}]).encode())
        for history in ([dict(pets={})] * 3, [{}] * 9, None, [None]):
            with self.subTest(history=history), self.assertRaises(ValueError):
                check_native_add_quota(json.dumps(history).encode())

    def test_template_round_trip(self):
        t = make_template(self.proof, self.id)
        self.assertEqual(validate_template(json.loads(json.dumps(t)), self.proof), self.id)

    def test_paths_are_owned(self):
        for bad in ('../../x', 'flippets-charlie-..', 'stock-pet', 'flippets-charlie-' + 'x' * 32):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                make_template(self.proof, bad)

    def test_template_mutations_refused(self):
        original = make_template(self.proof, self.id)
        for key, value in (('resourcePag', '/product/pets/stock.pag'), ('resourcePic', 'content://private'),
                           ('bizId', 'stock'), ('firstFrameCoordinateAxes', axes([0, 0, 976, 596]))):
            t = deepcopy(original)
            t['pets']['aiPetsData'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_template(t, self.proof)
        original['unknown'] = True
        with self.assertRaises(ValueError):
            validate_template(original, self.proof)

    def test_axes_validation(self):
        for bad in ([0, 0, 977, 596], [-1, 0, 976, 596], [4, 0, 3, 596], [0, 0, 976], [0, 0, True, 596]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                axes(bad)

    def test_prepare_keeps_originals(self):
        with tempfile.TemporaryDirectory() as temp:
            output = prepare(Path(temp) / 'new')
            self.assertEqual((output / 'original.pag').read_bytes(), self.pag)
            self.assertEqual((output / 'poster.png').read_bytes(), self.poster)
            m = read(output / 'manifest.json')
            self.assertFalse(m['nativeApplyAllowed'])
            self.assertFalse(m['nativeMotionProven'])
            with self.assertRaises(FileExistsError):
                prepare(output)

    def test_small_source_native_quirk_both_rotations(self):
        for rotation in (0, 2):
            self.assertEqual(translation_by_axes(976, 596, [164, 112, 976, 596], rotation), (232, 796))

    def test_large_source_rotation_anchors(self):
        self.assertEqual(translation_by_axes(2000, 2000, [400, 600, 1400, 1800], 0), (-235, -408))
        self.assertEqual(translation_by_axes(2000, 2000, [400, 600, 1400, 1800], 2), (-356, -408))

    def test_editor_constructor_sign_and_systemui_inverse(self):
        t = make_template(self.proof, self.id)
        for rotation, key in ((0, 'wallpaperInfo0'), (2, 'wallpaperInfo180')):
            p = editor_position(976, 596, [164, 112, 976, 596], rotation)
            self.assertEqual([p[k] for k in ('left', 'top', 'right', 'bottom')], [-232, -796, 976, 596])
            t[key] = dict(positionInfo=p)
        for rotation in (0, 2):
            self.assertEqual(systemui_translation(t, 976, 596, rotation), ('positionInfo', (232, 796)))

    def test_explicit_positions_ignore_axes_and_matrix_scale(self):
        t = make_template(self.proof, self.id)
        t['wallpaperInfo0'] = dict(positionInfo=dict(left=12.9, top=-31.9, matrixArr=[10] * 9))
        t['wallpaperInfo180'] = dict(positionInfo=dict(left=-7.9, top=44.9))
        self.assertEqual(systemui_translation(t, 976, 596, 0), ('positionInfo', (-12, 31)))
        self.assertEqual(systemui_translation(t, 976, 596, 2), ('positionInfo', (7, -44)))

    def test_one_position_uses_fallback_for_both(self):
        t = make_template(self.proof, self.id)
        t['wallpaperInfo0'] = dict(positionInfo=dict(left=999, top=999))
        for rotation in (0, 2):
            self.assertEqual(systemui_translation(t, 976, 596, rotation), ('firstFrameAxes', (232, 796)))

    def test_unsupported_rotation_refused(self):
        for rotation in (1, 3, 180):
            with self.subTest(rotation=rotation), self.assertRaises(ValueError):
                translation_by_axes(976, 596, [164, 112, 976, 596], rotation)

    def model(self, directory):
        before = dict(current=dict(id='previous'), history=[dict(id=str(i)) for i in range(12)],
                      wallpaper=dict(rotation0='original0', rotation180='original180', type=8),
                      resources={'previous': dict(bytes='exact-byte-fixture', mode=420, uid=1000, label='label')})
        receipt = plan(before, self.id, dict(bytes='PAG', mode=420, uid=1000, label='label'),
                       dict(id=self.id), dict(rotation0='new0', rotation180='new180', type=8))
        state, journal = Path(directory) / 'state.json', Path(directory) / 'receipt.json'
        atomic_json(state, before)
        atomic_json(journal, receipt)
        return before, state, journal

    def test_apply_and_exact_model_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            before, state, journal = self.model(temp)
            while advance(state, journal, 'apply'):
                pass
            self.assertEqual(len(read(state)['history']), 10)
            while advance(state, journal, 'restore'):
                pass
            self.assertEqual(read(state), before)  # Includes evicted entries and exact file metadata.

    def test_death_at_every_apply_and_restore_boundary(self):
        for direction in ('apply', 'restore'):
            for step in range(4):
                for point in ('before-state', 'after-state'):
                    with self.subTest(direction=direction, step=step, point=point), tempfile.TemporaryDirectory() as temp:
                        before, state, journal = self.model(temp)
                        if direction == 'restore':
                            while advance(state, journal, 'apply'):
                                pass
                        for _ in range(step):
                            advance(state, journal, direction)
                        advance(state, journal, direction, interrupt=point)
                        while advance(state, journal, 'restore'):
                            pass
                        self.assertEqual(read(state), before)

    def test_later_choice_survives_every_phase(self):
        for phase in range(5):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as temp:
                _, state, journal = self.model(temp)
                for _ in range(phase):
                    advance(state, journal, 'apply')
                later = read(state)
                later['current'] = dict(id='later-manual-choice')
                atomic_json(state, later)
                with self.assertRaises(ValueError):
                    advance(state, journal, 'restore')
                self.assertEqual(read(state), later)

    def test_corrupt_receipt_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            _, state, journal = self.model(temp)
            receipt = read(journal)
            receipt['states'][0]['current'] = 'corrupted'
            atomic_json(journal, receipt)
            with self.assertRaises(ValueError):
                advance(state, journal, 'restore')

    def test_native_resource_paths_refuse_foreign_and_traversal(self):
        self.assertEqual(native_path('/data/system/theme_magic/users/0/wallpaper/data/small_lock.xml'),
                         '/data/system/theme_magic/users/0/wallpaper/data/small_lock.xml')
        for path in ('/sdcard/private.png', '/data/system/theme_magic/users/0/wallpaper/../settings.db',
                     '/data/system/theme_magic/users/10/wallpaper/file', '/product/media/wallpaper/x;id',
                     '/product/media/wallpaper/x\ncat /data/system/users/0/settings_secure.xml'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                native_path(path)

    def test_private_preview_session_scope(self):
        for path in (TEST_TEMP, Path('work/phone-qa/native-folded'), Path('outputs/native-pet')):
            with self.subTest(path=str(path)), self.assertRaises(ValueError):
                private_session(path)

    def test_unstable_native_choice_refused(self):
        class ChangingPhone:
            def __init__(self):
                self.n = 0
            def state(self):
                self.n += 1
                return dict(current=str(self.n).encode())
        with self.assertRaises(ValueError):
            stable_state(ChangingPhone())

    def test_wrapper_preserves_donor_compositions(self):
        from prepare_native_template import ROOT
        background = (ROOT / 'work/app/assets/pets/bird-pandora/bg.webp').read_bytes()
        candidate = compose(self.pag, background)
        original_tags, candidate_tags = list(tags(self.pag, 9)), list(tags(candidate, 9))
        for code in (31, 32, 50):
            self.assertEqual([p for c, p in original_tags if c == code], [p for c, p in candidate_tags if c == code])
        self.assertEqual([p for c, p in original_tags if c == 2][0], [p for c, p in candidate_tags if c == 2][0])
        self.assertEqual(len([p for c, p in candidate_tags if c == 2]), 2)
        self.assertIn(background, candidate)

    def test_wrong_donor_refused(self):
        with self.assertRaises(ValueError):
            compose(self.pag[:-1] + bytes([self.pag[-1] ^ 1]), b'')

    def test_wrong_background_refused(self):
        with self.assertRaises(ValueError):
            compose(self.pag, b'invented background')

    def test_truncated_pag_tags_refused(self):
        for raw in (b'\x3f\x00', b'\x01\x00', b'\x00\x00extra'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                list(tags(raw))


if __name__ == '__main__':
    unittest.main(verbosity=2)
