# Charlie: native pet flow on the MIX Flip

Current continuation: [MIX Flip collection and calibrated Charlie](mixflip-pets-integration.md).
The calibrated Charlie was subsequently updated in its existing owned record with
explicit user authorization. Exact resource copies and preservation of other saved
designs were acknowledged; the user accepted its folded appearance. The user has
now deferred further Charlie changes and requested completion/push of the six stock
MIX Flip pets. Exact Restore remains unproven. See the current top checkpoint in
[HANDOFF.md](../HANDOFF.md); preview-only statements below are historical.

Updated 11 October 2026 after authorized EEA phone testing. The user resumed the
pet work and deferred cards. This supersedes the earlier folded-pet deferral;
independent display power and root installation remain separate.

## Pause checkpoint after native Apply

The user explicitly accepted manual restoration, selected the saved Bichon slot
for replacement, then requested continued work. Only that saved entry was
removed through Xiaomi's UI. The four other saved profiles survived unchanged;
the OEM automatically changed the current selection during removal. The built-in
Bichon artwork and preset catalogue entry remain available for later re-adding
when one of the three pet slots is free.

Charlie was subsequently **applied through the native Add control**. Readback
confirmed the owned identity and exact SHA of the copied PAG. History now has
five entries/three pets, with all four preceding saved profiles preserved.
`native_pet_apply.py --readback-only` recovered an observation interrupted between
native current/history writes without a second Add. Exact Restore is unproven.

The user reports that Charlie is small and **does not move on the folded outer
screen**. Neither issue is fixed. Actual SystemUI source suppresses tap/wake
animation while `getHasNotifies()` is true and skips a biometric wake branch;
the actual notification flag was not measured. Do not claim this is the proven
cause or remove other apps' notifications without authorization. All pets must
ultimately have a comparable character size to the stock capybara; the earlier
25% Charlie proposal is superseded. No new size change was applied.

The user also requested native-set management inside Flip Pets and the six stock
MIX Flip pets for the unfolded mode. The import completed in source only:
39 catalogue entries/194 clip paths, including18 unchanged stock PAGs and12
original AOD vector foregrounds. First33 entries equal the previous catalogue.
Gallery collection, vector rendering, playback, size guides, thumbnails and
fresh APK QA remain unfinished. There is **no Android native-pet manager UI yet**.

Work was stopped at the user's request. See [HANDOFF.md](../HANDOFF.md) for exact
private receipts, consent and next actions. The current installed APK predates
the new import. Historical preview text below must not be read as the latest
phone state.

## Current result and remaining gate

The actual EEA AOD and SystemUI hashes match the inspected artifacts. Charlie
loads and moves in Xiaomi's own editor. The first unmodified-PAG fixture showed
a double bird on a gray background: a transparent animated layer was drawn over
the static bird poster. A compatibility composition now supplies the verified
original MAML background behind the unchanged donor compositions. Its opaque
animated canvas covers the static poster during playback.

A first candidate exposed a decoder-readiness bug: a background-only snapshot
became the poster and the bird disappeared after the OEM fade. The probe now
waits, with a five-second deadline per sample, for actual donor-pose pixels.
The first pose must match all checked opaque donor pixels exactly; later samples
allow at most 0.5% of checked pixels outside a one-channel-value tolerance and
mean maximum-channel error at most 0.1. These tolerances cover sparse nested
compositing edges; they do not allow an empty background to pass.

The final candidate moves the original composition to `(0, 796)` in a
1208×1392 canvas. The earlier `(232, 796)` placement hid the bird behind the
editor's camera representation at 180°. Both editor orientations now have
observed motion and a visible resting bird. The user tentatively accepted the
background/duplication fix before this final placement adjustment. Physical
camera clearance on the folded lockscreen and the whole motion envelope remain
unverified. Wide branches retain the original composition's clipped edge; moving
that edge inside a wider canvas can expose the source boundary. This is not a
finished visual acceptance or an exact copy of Xiaomi's native AI-generated pet.

At the earlier preview-only checkpoint, all sessions were exited without Apply. Current selection and history
were byte-identical before/after the final session. The selected native state
referenced 18 inventoried dependencies; their bytes were backed up privately.
Shell write checks failed for all 18. This does not prove that root is required:
the OEM writer can copy with its own UID. It does mean a shell copy-back operation
is not a proven restore path.

**That checkpoint had no native Apply or Restore.** Subsequent Apply is recorded
above; no exact Restore implementation exists. A model transaction
does not establish the native writer, wallpaper notifications, cache invalidation
or restoration after process death. No app lockscreen overlay, wake workaround,
framework change or root installation was used. The Shizuku pet session policy
is unchanged. Public scoped evidence: [native-pet-phone-followup.json](../work/research/native-pet-phone-followup.json).

## Reproduce preparation and preview

The unchanged proof bundle remains `outputs/FlipPets-native-Charlie-proof.zip`.
It retains its historical renderer-APK binding. Do not relabel it as a decode of
the current APK. To prepare the adaptation:

```powershell
python -X utf8 work/tests/prepare_native_composite.py
python -X utf8 work/tests/probe_native_composite.py
python -X utf8 work/tests/prepare_native_template.py --variant composite
python -X utf8 work/tests/run_native_pet_flow_tests.py
```

The decoder explicitly targets and verifies `emulator-5554`. It never loads an
OEM Activity. The composition writer is restricted to the known Charlie PAG and
background hashes; donor video/vector payloads remain unchanged. It adds a root
composition and the original background, stretched as the donor MAML specifies,
with one pixel of background overscan to prevent antialiased transparent edges.
See Tencent's [PAG codec source](https://github.com/Tencent/libpag/tree/main/src/codec)
and its existing Apache-2.0 notice in `work/licenses/libpag-LICENSE.txt`. Xiaomi
artwork remains excluded from the MIT code license.

The serializer creates a fresh owned `bizId`, fixed staged paths and a resource
manifest. It refuses stale decode evidence or changed PNG pixels. `--variant
original` retains the diagnostic original fixture; it reproduces the known
transparent-PAG/poster mismatch and is not the recommended appearance.

Authorized phone work uses an explicit serial and the exact EEA profile:

```powershell
python -X utf8 work/tests/capture_native_capabilities.py --serial <serial>
python -X utf8 work/tests/native_pet_preview.py --serial <serial> inspect
python -X utf8 work/tests/native_pet_preview.py --serial <serial> begin --prepared <new-prepared-folder>
python -X utf8 work/tests/native_pet_preview.py --serial <serial> finish --session <private-preview-session>
```

`begin` requires normal awake/unlocked primary-user state. It validates AOD and
SystemUI, reads a stable selection/history baseline, stages only the two owned
resource files and opens the exported editor. It does not press Add/Apply.
`finish` sends Back only to the exact focused editor, verifies actual exit and
compares both settings. A remaining confirmation dialog or changed state stops
the check. Staging/backup receipts and raw images remain in ignored
`work/phone-qa`; they are not uploaded or included in a release. Staging is kept
for diagnosis, not deleted while the editor might still reference it.

The native editor displays Xiaomi's own “Создано ИИ” label for this template type.
Our resource was composed from donor artwork; no AI generation or photo upload
occurred. The label is not evidence of a generation backend.

## Geometry trace

`AiPetsPagView.getTranslationByAxes` uses the first-frame axes and fixed native
anchors for rotations 0/2. With a 976×596 input its negative overflow clamp yields
`(+232,+796)`. This source quirk is modeled, not treated as camera clearance.

`TinyEditorAiPetsView.refreshTemplateItem` creates both wallpaper orientations
from the poster. `PositionInfo(Matrix,x,y,w,h)` stores `left=-x`, `top=-y`,
`right=w-x`, `bottom=h-y`. The matrix contains the editor preview scale and
translation. A later crop can replace these structures.

SystemUI uses `(-left,-top)` only when **both** orientation positions exist;
otherwise it falls back to first-frame axes for both orientations. It does not
transfer the editor matrix scale. Last-frame axes are read but do not determine
the inspected fallback. Our full-cover candidate has zero host translation;
its pet placement and opaque background are already inside its composition.
`native_pet_geometry.py` models these branches and both even rotations.

## Apply and restore dependency map

| Stage | Inspected behavior | Required restore evidence |
| --- | --- | --- |
| Editor input | Refreshes wallpaper position structures for both orientations; preview is not Apply | Before/after JSON and actual cancel behavior |
| `TemplateApiImpl.fileCopy` | Creates a timestamp resource directory; copies AI PAG, original/cropped sources, optional subjects/masks and previews; updates resource paths | Exact files, owners, modes, labels and all live references |
| Apply continuation | File copy succeeds before `saveCurrentTemplateToDatabase`; failed copy must not be treated as selection success | Readback at each interruption boundary |
| Current choice | Writes `current_tiny_keyguard_info` | Original value including absence/null semantics and native observer/cache acknowledgment |
| History | Optional `createHistoryItem`: retains first nine entries, inserts at front for `-1` or replaces a valid index; then writes `all_tiny_keyguard_info` | Exact order, evicted entries, original identifiers and referenced files |
| Editor success observer | Calls `setMiuiRotationImageWallpaper(...,8)` using the two preview bitmaps; pet templates skip the separate Themes non-pet notification branch | Actual outer-wallpaper bytes/type/metadata and confirmed notification path |
| Resource status/cleanup | Updates AI resource status; replacement branches can clear the previous template's resources | Protect originals and references; never assume old files survive Apply |
| Built-in rollback | `rollbackAiPetsByBizId` filters history, may select a different remaining item, and deletes filtered resources | Not an exact inverse; do not use it as our Restore |

The `fileCopy` decompiler inverted a critical PAG-copy condition. The raw DEX
fallback shows success requires a **non-null, non-blank** copied path before
`setResourcePag`/`setResourcePic`; null/blank marks the copy failed. The raw Apply
continuation also confirms copy → current choice → optional history. The large
coroutine and internal FullBackupAgent branches are not claimed fully verified.
The JSON editor entry starts with `Z=-1`/`a0=true`; do not assume it is a dry-run
history replacement or change extras to evade history effects.

The actual AOD manifest registers `com.miui.aod.backup.AodFullBackupAgent` with
`allowBackup=true`/`fullBackupOnly=true`. Registration is not an exported narrow
Restore API. The readable delegate's supported-template map omits `ai_pets` and
its restore validation filters templates against that map. Together with the
40 decompiler errors, this makes system backup an unverified candidate, not a
drop-in exact rollback. Do not invoke broad device backup/restore as a substitute
for the scoped native transaction.

The proposed receipt must preserve exact before values, all affected resources
and metadata, the expected after values, owned IDs and created paths. Journal an
operation before writing, read back after it, recover only a recognized phase,
and preserve later manual state. Never delete a resource while any current,
history or wallpaper reference still uses it. The offline file model covers
interruption before/after every apply/restore phase and later manual choice at
every phase, including evicted history restoration. It lacks external native
serialization/versioning and cannot protect an indistinguishable ABA change;
these remain device-adapter requirements.

The original exact-restore research plan was to identify a narrow OEM writer for resource bytes and
outer-wallpaper/cache state. Then enable one reversible Apply and test the real
folded locked screen: wake without/with notifications, tap replay, biometric
unlock, Power/timeout, rotations, folding and reboot. Root assistance is a
separate fallback only if a concrete capability remains unavailable. A root
supervisor alone cannot complete this flow or supply continuous AOD animation.
The user later allowed native Apply with manual restoration; follow the pause
checkpoint and HANDOFF rather than repeating that approval request.
