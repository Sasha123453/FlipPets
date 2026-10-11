# MIX Flip collection and native Charlie continuation

11 October 2026. Source checkout: `E:\FlipPets`.

Current development APK: `57d39faa9cf1cd54a79fc50a6045214e325076a623efe131237123ac16e09778`.
The six stock pets and original clocks are implemented; fresh scoped reports are
in HANDOFF. Calibrated Charlie was updated in place and its body size accepted
on the phone. Further Charlie work, including its different native AI/app clocks,
is deferred at the user's request. Future profiles: [adding pets](adding-native-pets.md).

The app catalogue now contains 39 entries and 194 clip paths. The original 33
entries are unchanged. MIX Flip is a separate collection of six stock pets with
three original PAG scenes each. Xiaomi retains the artwork rights.

All 18 stock files passed their import hashes and actual libpag decoding at a
maximum 696-pixel render surface: eight samples per clip, including the exact
start/end progress. Source dimensions are recorded separately. Some start frames
are genuinely transparent (Devon actions1/3, otter actions1/3, bichon action2).
A transparent first frame must not be treated as a decoder failure. Each scene
has at least three distinct sampled hashes and a visible final pose.

Stock files are not all 1208 pixels wide: bichon action1 is1308, otter action2
is1408, panther action1 is1409, and several cat/panther scenes are1268. The app
retains each source canvas and the OEM Zoom transform. A separate stock branch
keeps the original donor CoverGeometry rules intact. The numeric translation
tables and action mappings were compared in the inspected EEA AOD and SystemUI
DEX; the raw CFG was needed because JADX's enum Java lost constructor arguments.
See `work/research/mixflip-native-geometry.json`.

The imported English foreground vectors sit in the wallpaper/background layer
behind the pet. They are artwork with lettering, not flat background colors.
Both0/180 variants are used. The app adapts the stock TYPE_NORMAL TinyClock
layout with the original C700 font, per-pet time/colon colors, signed resource
margins and separate date/week layer above the pet. The exact EEA DeviceConfig
selects clock rotation2 only for a nonempty RIGHT cutout; otherwise0. This is
independent of raw Display.getRotation(); the pet media now uses this same cutout
selector, as verified in OEM PagViewBase. Source
parameters/font hashes: `work/research/mixflip-clock-provenance.json`. On MIX Flip
the date uses its system MiSansLatinVF at wght700; other systems retain a platform
font fallback. This is an app adaptation, not the entire OEM TinyClock runtime. Manual donor layout profiles are disabled
for these stock pets so automatic stock geometry stays unchanged.

The app plays each scene once, holds the completed pose, ignores taps during
playback, then advances1→2→3→1 on touch. Stop releases the composition, cache and
foreground; restart replays the saved scene. Gallery previews use static decoded
thumbnails and an explicit Apply/Cancel. Cancel does not select a pet. This
selection affects only the app's open-phone mode, not Xiaomi's saved lockscreen.

## Charlie on the native folded screen

Before the calibrated replacement, during the phone run
the user observed the stock Charlie after folding/locking, no tap replay with
notifications, then working replay without notifications. This agrees with the
inspected gate, but does not prove all wake/biometric/AOD/orientation conditions.
ADB was disconnected during the clean manual trial; there is no technical native
layer/progress measurement for it. Subsequently the unique owned Charlie was
updated through OEM «Готово». Current/history converged, exact PAG/poster copies
matched, and all four other designs plus their15 resources remained unchanged.
Five old-only Charlie preview/crop/PAG references were removed by OEM replacement;
no other saved design was deleted and no additional slot was used. The user
accepted the folded appearance. Exact automatic Restore remains unproven.

A separate local candidate scales Charlie's body using the capybara action1
first-pose silhouette, excluding Charlie's branch/flowers from the body guide.
Its constant transform is approximately scale2.220779, x−663.273, y117.273 in a
1208×1392 composition. Original donor composition payloads remain unchanged.
Eight original-resolution candidate samples are opaque and moving; the poster
is the actual decoded first pose. Original crest/branch clipping remains.
The first-pose size comparison does not establish physical camera clearance or
clock clearance throughout movement. See `work/research/charlie-native-calibration.json`.

The inspected AOD EditActivity resolves AI history through
`getHistoryTemplateInfoByAiPagId`, comparing `aiPetsData.bizId`, and then sets its
history index/Add flag. The actual update control and replacement/readback were
verified on the inspected phone profile. The host planner accepts only one unique
owned `flippets-charlie-…` entry and never falls back to Add at a full quota.

## Native management from Main

“Питомцы на штатной блокировке” offers an explicit native-state query and access
to Xiaomi's saved-template and built-in catalogue screens. The separate Shizuku
UserService accepts three fixed operations, validates shell UID/owner, primary
user, ruyi/EEA build and both inspected APK hashes. It reads bounded JSON twice
and returns only fixed pet labels and3/9 slot counts. It does not return paths,
photos, custom names or raw JSON and does not write AppLog. It cannot import,
delete or apply resources. The user controls changes in Xiaomi's own UI.

The phone run verified the actual Shizuku summary (Charlie,3/3 pets,5/9 designs)
and both OEM HistoryActivity/HomepageActivity launches, with unchanged current
selection/history. These initial UI checks belong to APK b9e9fcfb…; consult the
SHA-bound phone report for the subsequent clock build.
Prepared Charlie import/update from the app and exact automatic Restore remain
unfinished. There is no claim of complete native management or a fixed physical
animation. Root, stock secure sleep/AOD and the default controller policy are
unchanged; main-off continuation remains deferred.

## Reproduce local checks

Run each emulator suite separately, targeting only guarded emulator-5554:

```powershell
python -X utf8 work/tests/run_mixflip_guard_tests.py
python -X utf8 work/tests/run_native_pet_flow_tests.py
python -X utf8 work/tests/run_mixflip_source_qa.py
python -X utf8 work/tests/prepare_mixflip_metadata.py
python -X utf8 work/tests/prepare_calibrated_charlie.py
python -X utf8 work/build_apk.py
python -X utf8 work/tests/run_mixflip_source_qa.py --calibrated --full
python -X utf8 work/tests/run_mixflip_qa.py
python -X utf8 work/tests/run_release_qa.py
python -X utf8 work/tests/run_pet_layout_qa.py
```

The stock/shared runtime suite requires80 named cases, natural playback completion,
real MotionEvents and preference restoration. Publication now requires194 clip
checks and479 total APK checks, including the previous suites and80 stock/shared cases.
The packager preserves the old33-entry canonical hash and donor18 serialization,
and verifies all18 PAG/12 foreground files against import provenance. A rebuilt
APK does not inherit historical emulator or phone evidence. No release archive,
commit or push is implied by these source changes.
