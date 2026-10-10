# Earlier KernelSU and native pet investigation

**Superseded planning sequence:** read [Native cover integration: investigation and agent handoff](native-cover-root-and-rootless-agent-plan.md) first. The user subsequently deferred pet generation and all alternative backends. Generation sections below are retained as inactive research notes, not implementation requirements. The new plan also establishes a native FlipHome launcher route for ordinary app-owned cards and a separate optional 2×3 MAML widget extension.

Status: planning only, 10 October 2026. Work in `E:\FlipPets`. This document does not authorize installation of root, flashing, native Apply, account access, photo upload or implementation. The user explicitly paused implementation and requested this plan for a later agent. Resume implementation only when the user requests it.

## Product outcome and sequence

Deliver reliable KernelSU support for the existing open, awake, unlocked cover session first. The next native pet proof uses known donor resources. **Generate my pet is deferred by the user**, including provider selection and backend integration. Do not make it a dependency of native pets or apps.

The desired native milestone is a donor pet on MIX Flip's folded lockscreen, managed by Xiaomi's own renderer. Keep the unfolded app session and native folded selection independent, with an explicit option to use the same pet on both. Build reusable resource, geometry, lifecycle and restoration contracts. A native single-PAG pet does not establish an interactive card host, continuous AOD animation or an independent rear screen after main-screen sleep. The newer plan identifies a separate native launcher route for app cards.

Recommended order:

1. Establish an exact baseline and reliable root supervisor.
2. Prove native folded playback and restoration with one known donor PAG.
3. Adapt app-owned cards for Xiaomi's native cover launcher, following the newer plan; this work does not depend on native pet Apply.
4. Consider additive native MAML widgets only after launcher apps are verified.
5. Leave photo-to-animation generation and donor runtime transplantation deferred.

Do not add Glow, Vortex clocks, stock-widget clones or unrelated gallery changes to this work merely because they are easy candidates. Preserve the rootless default and all existing catalogue IDs.

## Read first and establish source identity

Read `AGENTS.md`, `HANDOFF.md`, `TODO.md`, and these documents:

- `docs/kernel-su-module.md`
- `docs/folded-wallpaper-options.md`
- `docs/native-tiny-preview-evidence.json`
- `docs/independent-display-power.md`
- `docs/framework-power-provenance.json`
- `docs/donor18-resource-import.md`
- `docs/donor18-mini-app-runtime.md`
- `docs/photo-pet-generation.md`
- `docs/mini-apps.md`
- `work/research/hongkong-low-effort-audit.json`

Inspect the dirty checkout before any edit. Many changes predate this plan. Do not reset, stage everything, switch signing keys or use the historical checkout. Recompute the current APK/controller/module hashes rather than copying a handoff's “current” hash. Check whether any old QA process remains active before using the emulator.

| Source | Verified knowledge | Boundary |
| --- | --- | --- |
| MIX Flip `ruyi`, actual EEA OS3.0.303.0.WNIEUXM / Android 16 | Native AOD/editor and wallpaper APKs were inspected; native preview accepted Charlie data | Phone is still unrooted as of this planning session; no root runtime proof |
| MIX Flip Global OS3.0.303.0.WNIMIXM | Downloaded `miui-services.jar` inspected | Not the exact EEA framework; matching APKs do not prove matching framework |
| 18 Pro `hongkong`, OS4.0.15.0.XFRCNXM / Android 17 / SDK 37 metadata | Selected product and system_ext partitions verified; original resources and Themes/subscreen code inspected | Whole OTA incomplete and non-flashable; no donor APK installation or full subsystem port |
| 17 Pro `pandora`, CN OS3.0.319.0.WBLCNXM | Earlier power-framework comparison and pet sources | Its power analysis must not be relabeled as an 18 Pro framework audit |

Native EEA AOD APK evidence SHA: `31c6dd09226e24f13f519822425a0b3f2a6d4fb8d6bf565bbd3a0568ee494d5d`. Donor Themes APK SHA: `3888058041439577aadbb933c9bed1fb3ef16acda20d15404fb620314a8edd0a`. Verify again against the intended device/build before applying a compatibility profile.

## Existing code and contracts to preserve

### Open phone session

`outputs/flip-pets-control.sh` and `work/app/assets/controller.sh` are byte-identical. The controller verifies UID 2000, `ruyi`, presentation state 5 and the firmware layout; it waits for open/awake/unlocked conditions and an ON cover before launching `PetActivity`. The root builder derives its UID 0 variant from this canonical script.

`PetActivity` uses the separate `org.flippets.app.cover` task. The supervisor launch must retain `--ez coverSession true`: the current manual/non-session path adds `FLAG_KEEP_SCREEN_ON`, while the controlled session does not. Do not accidentally use the manual path for root support or native lockscreen experiments.

`CoverGuard` is a user-enabled foreground session service. Removing Main from Recents retains that session. `CoverGuard.requestStop` and `ShizukuBridge.stop` persist `controller-stop`; the controller must observe it. `ControllerService` deliberately requires shell UID 2000; do not casually weaken its checks to build a root bridge. `StopCover` is an exported receiver protected by `android.permission.DUMP`.

`PetStage`, `HingeFade`, `CoverPreview`, `CoverGeometry`, `PetLayout` and `PetLayoutProfile` own the current lifecycle and geometry. Existing `scene-ID` profiles and draft/Apply/Cancel behavior remain valid. Do not merge folded-native geometry into these preferences implicitly. Standard hinge angles are degrees; Xiaomi `flip_status` is categorical.

### MIX Flip native folded pet

The specific native entry point is:

```text
package: com.miui.aod
activity: com.miui.tinykeyguard.editor.edit.EditActivity
action: miui.tinykeyguard.editor.EDIT
STRING extra: param_template_item_json
schema: com.miui.tinykeyguard.editor.data.template.TemplateItem
clockInfo.templateId: ai_pets
pets.petCategory: 2
pets.aiPetsData: bizId, resourcePag, resourcePic,
                 firstFrameCoordinateAxes, lastFrameCoordinateAxes
axes: leftX, leftY, rightX, rightY
```

Inspect local decompilation under ignored `work/folded-research/gateway-current/`:

- `Tiny-EditActivity.java`: incoming JSON and template refresh.
- `Tiny-TinyEditorAiPetsView.java`: poster-derived wallpaper data for both orientations.
- `Aod-TinyEditorPetsPagView.java`: category 2, lifecycle, autoplay inputs and `preInit` route.
- `Tiny-AiPetsPagView.java`: loading, replay, pause, final frame and geometry.
- `Tiny-TemplateApiImpl.java`: `fileCopy`, `applyTemplate`, current selection, history and rollback.
- `Tiny-TemplateFilePathGenerator.java`, `Tiny-TemplateItem.java`: filesystem and schema requirements.

`AiPetsPagView.loadFileComplete` creates a 1208 x 1392 composition. `updateCompositionRotation` applies translation, not donor scale. Rotations 0 and 2 have different placement calculations. `preInit` can receive frame axes or explicit translation points; trace which path the real editor selects. `rePlayPag` branches on `mIsAutoPlay`; the class initializes `endStopProgress` to zero and returns zero end-stop frames. Trace inherited `PetsPagView`/`PagViewBase` behavior before interpreting a still preview as a decoder failure or promising a repeat policy.

The import expects readable regular filesystem paths. This copy branch does not parse `content://`. Native AOD performs the final copy into its `tiny_keyguard/<timestamp>/AI_PAG` resources and updates `current_tiny_keyguard_info` and history. A decompiler inverted a copy-result condition previously; critical branches must be checked against DEX when the reconstruction is inconsistent.

Historical preview only: supplied JSON accepted, Charlie visible, no Apply, current/history values unchanged. The poster came from a gallery thumbnail, not an exact decoded frame. Motion, native copy, persistent selection and restoration remain unproven.

### 18 Pro content and generation

The donor uses MAML and PAG/video assets. Original events, delays and completion behavior are content-specific; a single native AI-PAG slot cannot automatically reproduce the full donor pet state machine.

`work/extracted/hongkong/JsCanvasScreenElement.java` hosts MAML inline Script or locale JS variants through `QuickJsBridge` and `libquickjs_canvas.so`. It includes display/AOD, storage, sensor, audio and rendering lifecycle integration. `RearScreenAiAppMamlView.java` loads MTZ using `ZipResourceLoader` and `ScreenElementRoot`. Neither is a standalone library-drop solution for Android 16.

`AiCompanionApiService.java`, `AiCompanionRealApiProvider.java`, its `generateImage` and `submitVideoTask` coroutine classes, `AiCompanionAcquireApi.java`, `CompanionGenerateRawDataBuilder.java` and `AiCompanionConstants.java` establish:

1. Reference photo and prompt through `AiWallpaperManager` / `StartWithAiCompanionHandle`, scenario `accompanyPic2Pic`.
2. Polling and user confirmation of the static character.
3. Confirmed image through `accompanyPic2Video`, with linked task/business IDs.
4. Acquisition through `POST ai/acquire`; raw text/image URL data encrypted with a key from preceding stages.
5. Files including `reference.jpg`, `generated_static.png` and `details.mtz`.

This is evidence for image-to-image-to-animation/resource generation. It does not prove a mesh/rig, local generation model, compatible backend access on EEA, or the exact media payload inside an actual generated MTZ.

## Reusable architecture for pets and later apps

These are proposed responsibilities, not claims that the classes already exist. Introduce the minimum interfaces needed by the first real features, not a generic plugin framework.

| Component | Responsibility | Must stay outside it |
| --- | --- | --- |
| Content descriptor and private store | Stable ID, content type, hashes, source/provider provenance, dimensions, duration, poster, supported roles and format version | Raw account tokens, arbitrary executable commands |
| Validator and importer | Size/count limits, archive traversal/symlink rejection, media decode, supported formats, private copy, required dependencies | Executing unknown MAML/JS as root or in SystemUI |
| Geometry model | Canvas bounds, rotation, subject/face bounds, exclusion guides, clock space and reversible transforms | Assuming current app placement equals native editor placement |
| Generation provider | Typed create-image, query-job, create-animation, cancel and download operations with durable job state | Root access, native Apply or automatic selection |
| Runtime adapters | Existing app PAG/video renderer, isolated HTML host, native folded PAG installation; later MAML host only after proof | One renderer claiming capabilities of another |
| Root controller and native installer | Fixed allowlisted operations, compatibility checks, ownership, installation receipts and restoration | Cloud generation, arbitrary shell from cards, frame rendering |
| Selection and lifecycle policy | Separate drafts and applied selections per target; explicit Start/Stop and native Restore semantics | Per-frame preference writes or silent cross-mode changes |

Expose capability results per target: `unfoldedApp`, `foldedNativePag`, `nativeAod`, `touchInput`, `clockControl`, `network`, `supportedMedia`. Represent unknown separately from unsupported and supported. Probe using exact build/component hashes; do not turn one successful preview into a global compatibility flag.

A generated pet and a future app card share validation, storage, selection, geometry and diagnostics. They need different runtime adapters. Keep HTML/JS in the app sandbox, retain isolated preview storage and the existing offline request restrictions. Adding INTERNET for a generation client must not accidentally enable networking in `MiniAppView`; enforce resource-origin restrictions independently.

Treat simultaneous displays as separate consumers. No global WebView `pauseTimers()`, no shared mutable draft selecting content on another display. Each consumer releases its hidden resources. Installing native content is a transaction, not a daemon rendering loop.

## Milestone A Reliable KernelSU controller

Read `work/kernel-su/module-control.sh`, `action.sh`, `boot-completed.sh`, `customize.sh`, `uninstall.sh`, `module.prop`, and `work/build_kernel_su_module.py`.

Resolve these concrete review findings:

1. Boot currently calls `enable_session` once and fails if external app storage is unavailable. Distinguish boot complete, first user unlock, package readiness and screen keyguard. Wait with low-frequency, cancellable checks; do not clear a Stop request hidden by locked storage.
2. Canonical `supervise` clears Stop and returns after spawning, before proving the child survived. Design an explicit start acknowledgement and separate explicit start from unattended resume. Do not clear a new concurrent Stop during boot or recovery.
3. `session-enabled` and `session-owned` currently live in the replaceable module directory. Define opt-in persistence and migration across updates and reboot; installation alone must never opt in. Preserve durable Stop independently of a transient process.
4. Ownership currently uses a marker, root UID and a cmdline substring. Verify the exact command/arguments and process identity; handle PID reuse, stale locks and concurrent Action/boot calls. A failed probe must not take over a Shizuku session.
5. The wrapper does not monitor module disable/remove flags after launch. Ensure those actions stop only its own live session and restore only its owned presentation request. Do not kill generic shells, ADB, SystemUI or unrelated apps.
6. Root-created runtime files may have UID 0/mode 0600. Audit both directions of switching root and Shizuku so stale root markers/status files do not trap the user in one backend. Do not solve this with world-writable control paths.
7. `ShizukuBridge.start` currently clears Stop before obtaining a controller result. If an app-side root selector is later added, make backend ownership and Start/Stop atomic enough to prevent conflicting sessions; keep shell-only Binder permission checks intact.
8. Preserve bounded launch retries and the canonical fold/lock/sleep rules. Do not add an outer restart loop that defeats the controller's three-failure limit or resurrects a force-stopped app against user intent.
9. Provide compact status: opted out, waiting for first unlock, waiting for open/unlocked screen, running, stopped by user, compatibility failure, launch failure. Persist only changes and bounded diagnostics.

Use fixed root operations and validated app-owned staging paths. If an app-to-root bridge is added, authenticate caller identity, reject symlinks/path escape and never accept arbitrary script text. KernelSU Action can remain the first supported control surface; a convenient app button is not a substitute for correct ownership and recovery.

Keep the module script-only unless a later proven integration actually requires a mount. Do not bundle whole donor APKs or add broad SELinux policy. Build from the canonical controller and record the matching APK SHA. Rebuild the APK only when its embedded code/assets change; a module-only change does not validate or invalidate unrelated APK rendering by itself.

Exit criterion: command fixtures and module-wrapper tests pass, followed by physical UID/SELinux/start/Stop/boot/fold tests on a rooted `ruyi`. Before physical tests, label the ZIP experimental. The phone is currently unrooted; this milestone cannot be certified solely here.

## Milestone B Native folded playback and restoration

### Compatibility and backup first

With later explicit device-work authorization, require an explicit serial and verify MIX Flip identity. Capture exact firmware and relevant AOD/Wallpaper/SystemUI versions/hashes privately. Do not publish serials, installed-app inventories, user templates or personal images.

Map the current template, history, referenced resources, file ownership, modes and SELinux labels. Define a restoration receipt with hashes and the specific fields/files touched. Avoid copying live global settings databases or changing unrelated system settings.

Reopening the old JSON and pressing Apply may create new timestamps/history. `rollbackAiPetsByBizId` removes matching entries and can select another history item; it is not a general snapshot restore. `CLEAR_ALL_TEMPLATES` is not rollback. Separate restoring visible selection from exact preservation of resources/history, and satisfy the repository's exact restore requirement before applying to the user's setup. If no exact route exists, stop native Apply and report the concrete missing operation.

Plan for partial failure between copy, selection save and history insertion. Record intent before mutation, commit only after readback, and recover interrupted own transactions without overwriting a later user selection. Restoration must be ownership-aware, not an unconditional boot action. Module disable/uninstall should restore only an active selection it owns, while its helper is still available; do not delete resources still referenced by native settings. Prove the actual disable/uninstall hook behavior, including reboot while disabled.

### Prove the renderer independently of generation

Use the known Charlie source `work/app/assets/pets/bird-pandora/pag_0.pag` as a diagnostic fixture, not the final generated pet. Its source SHA in the prior native preview is `3bb7533fd7506cdfcd6b0ad48a7027fe8b37353ee7723547a18a6b7e5518dc14`; verify before reuse. Decode exact first/last frames and construct a matching poster and bounds. Do not reuse the approximate thumbnail poster as motion evidence.

Trace autoplay, resumed/visible state, resource read errors, load acknowledgement and inherited PAG lifecycle. Demonstrate several distinct composed native frames after loading; confirm the poster alone cannot account for them. Native preview proof and actual folded lockscreen playback are separate results.

Original Charlie is 976 x 596. With full-file axes, the recorded native calculation produced translation 232,796; it is not the app's enlarged geometry. `work/folded-research/native-pag-wrap.py` is an ignored binary-format prototype adding a 1208 x 1392 outer composition with constant scale/translation. An isolated libpag probe decoded distinct frames, but the native engine has not accepted it in a verified test. Review IDs/tag encoding, duration, source-body preservation and parser assumptions before promoting it. Prefer a supported authoring/export path if available; libpag playback capability does not imply arbitrary PAG encoding.

Test native rotations 0/2, measured window/cutout data, face visibility, every relevant pose, and clock overlap. First/last frame bounds are not a substitute for the animation's full subject envelope. Native axes perform translation/clamping, not free zoom. Preserve the donor original and hash every derived asset. Charlie's source crest remains clipped in some frames; do not repair the claim through padding or a favorable still.

Only after the restore gate passes, use the native editor's own copy/apply path first. Root may assist validated staging, diagnosis and restoration; it need not be the final writer if AOD already performs the correct copy. Keep preview/Cancel side-effect-free. Do not inject a full donor AOD/SystemUI or write guessed settings paths.

### Folded behavior and ownership

Verify this matrix on the exact phone build:

| State or action | Required result |
| --- | --- |
| Folded lockscreen awake | Native pet renders; secure keyguard remains native |
| Folded screen timeout / Power | Stock sleep and AOD policy; no forced video loop |
| Unfolded, awake, unlocked | Root-supervised app displays the explicitly selected open-mode content |
| Unfolded, main locked or asleep | Existing controller yields; independent rear power remains out of scope |
| Fold/unfold while animation is loading | No orphaned decoder, stuck override or competing app/native surface |
| App Stop | Stops the app session; UI clearly distinguishes separately installed native wallpaper |
| Restore native / disable integration | Restores the owned native installation with verified receipt |
| Main removed from Recents | User-enabled open session remains; native selection remains system-owned |
| Reboot / first unlock / process death | No forced wake, repeated Apply or loss of user selection |

Do not promise uninterrupted animation while folded/asleep. AOD, one-shot wake animation, touch response and continuous looping require separate evidence. A native wallpaper install must not depend on the app running a background decoder.

## Deferred research only: Generate my pet

The user deferred this entire section after it was written. The requirements below describe a possible future generation feature only. Do not execute them or block current native work on them.

### Prove service and format before product UI

Trace the donor generation manager's gateway, authentication and task-result parsing read-only. Investigate authorized Xiaomi access first, but do not assume root bypasses account, region, request-signing or server availability. Do not extract personal credentials or replay private app tokens. If unavailable, present a documented alternative provider and obtain the user's choice before implementing that provider or uploading a photo.

Use a provider-neutral job contract. A generation request must identify provider, supported input/output, price/credit behavior if any, retention terms and actual task status. Prefer server-held credentials or a reviewed user credential arrangement; never put service secrets in the APK, module, repository or logs. Local generation is a separate option only if compatible models, license, memory and measured phone performance support it; no such model is currently verified.

The decisive spike is a real provider output that can play both in the app and in the chosen native folded route. Download and inventory an actual `details.mtz` or alternative output; validate files rather than trusting an extension. Determine whether it contains PAG, MP4, images, masks, editable layers or other metadata.

If the provider yields MP4 only, do not rename it to PAG or claim the PAG wrapper prototype converts it. Prove a supported PAG authoring/conversion pipeline or the separate outer-target-8 video route with backup/restore. Known Themes video import applies inner targets 1/2/3; it is not outer video import. If neither route works, generated unfolded playback is a partial result and the folded generation milestone remains incomplete.

Prove background/alpha handling and crop behavior. Current MP4 avatars keep opaque rectangles. A solid-background clip may be acceptable only as an explicitly previewed scene; do not call it a transparent pet cutout. Check identity consistency, face placement, unwanted limb changes, temporal flicker and loop seam. A single animation suffices for the first supported pet; multiple reactions require separately generated or verified states.

### User flow and durable jobs

1. Select a photo with Android's document picker; make a bounded private copy. No upload at import.
2. Show provider, what will be uploaded and relevant cost/retention facts; require explicit consent.
3. Submit character-image generation with a durable job ID and duplicate-submission protection.
4. Let the user approve or regenerate the character image before animation submission.
5. Generate animation; show real queued/running/failed/completed state, bounded polling/backoff and cancellation.
6. Resume a job after Main closes or process recreation without re-uploading or paying again unintentionally. Server work can continue while local decoders are released; do not keep a screen awake to wait.
7. Download to private temporary storage, validate size/format/hash/decode, then atomically publish the content package. Keep the previous active pet on failure.
8. Preview folded and unfolded placements separately. Apply is explicit per target. Cancel, browsing and regeneration never alter live selection or native settings.
9. Support deleting private source/intermediates/results and explain any provider-side deletion limit. Do not delete media still referenced by an installed native selection without restoration.

Acceptance requires a real user-authorized photo producing a new character and animation, successful private persistence, app playback, and verified folded native playback/restoration. A canned donor pet, static generated picture or file-import-only flow does not satisfy Generate my pet.

## Milestone D Make later apps straightforward

Use one self-contained offline card to exercise the shared descriptor/import/preview/selection/lifecycle contracts after the pet work. Existing Water, Vocabulary and Pomodoro are original public HTML examples; preserve their bytes and attribution. Native equivalents require verified matching packages. Do not relabel HTML as extracted firmware content.

`MiniAppStore` currently accepts only `focus`, `water`, `words`. `MiniAppView`, `MiniAppsDialog`, `GalleryDialog` and `PetStage` implement explicit selection and isolated previews. Generalize incrementally without changing old IDs or mixing card state with pet profiles. Keep target-specific capabilities: a card can support unfolded app rendering while native folded interaction remains unavailable.

The six extracted built-ins depend on Calendar, SecurityCenter, Personal Assistant, Xiaomi Home or Xiaomi car providers. Reuse only verified compatible contracts or explicit user-authorized data adapters. Do not fake provider success or import a chain of donor system apps as a shortcut. Stock widgets are lower priority than requested pets and original mini-apps.

If a native MAML/QuickJS route is investigated, inventory Android API, Java class, native ABI/linker, permission, provider and lifecycle dependencies against the target build. Host reviewed code in a restricted app process first. Full MAML can issue Intents, provider calls and reflective commands; archive validation alone does not make it safe to execute in a privileged process. Maintain an allowlist of supported elements/actions and reject unknown capabilities. Do not weaken the existing offline WebView host while enabling network access for generation elsewhere.

Success of this architecture means an additional offline card requires content/renderer registration and its own tests, not edits to root supervision or native backup logic. It does not mean every Xiaomi app becomes portable.

## Tests and release evidence

Add meaningful tests around the new boundaries, not tests that merely mirror implementation:

- Module wrapper: concurrent Action/boot, first-unlock delay, Stop during startup, child startup failure, stale/reused PID, foreign controller, module update/disable/remove, root-to-Shizuku transition, bounded retries and crash recovery.
- Resources: corrupt/truncated media, path traversal, zip bombs, symlinks, oversized dimensions/duration, missing poster, unsupported schema/codec, duplicate IDs and transactional publication.
- Geometry: app versus native transforms, both native rotations, finite scale values, all-pose subject envelope, exact poster/frame pairing and no draft leakage.
- Generation: consent before upload, approved-image linkage, retry/idempotency, cancellation, app restart, expired results, service errors and failed downloads preserving the active pet. Mock tests must be labeled separately from real-provider evidence.
- Native transactions: preview/Cancel unchanged, failure at each copy/save/history step, interrupted operation, restoration with later user changes, disable/uninstall and non-owned content preservation. Physical native tests are mandatory for release claims.
- Multi-display lifecycle: hidden renderers released, no global WebView timer pause, no generation-driven screen wake, separate Main/cover tasks and real notification Stop.

Use `emulator-5554` only after asserting emulator identity. Physical helpers require explicit serial and `ruyi` verification. Retain phone timeout 60000 ms and `stay_on_while_plugged_in=0`. Raw native templates, photos and device evidence stay ignored under `work/phone-qa`; publish only sanitized hashes/counts/results.

Build with `python -X utf8 work/build_apk.py` when app changes require it, then `python -X utf8 work/build_kernel_su_module.py`. Preserve the signing certificate, native ABI and 16 KiB alignment. Run relevant pure/controller tests first, specialized APK suites separately, and require fresh exact-SHA evidence when shared rendering/lifecycle changes warrant the full set. Existing suite counts are 176 media, 68 composition, 15 switching, 15 utilities, 19 layout, 23 donor and 27 mini-app checks, plus six virtual-cover lifecycle checks. Recheck counts after feature additions; never reuse old reports as a current pass.

Package only with `work/package_release.py`. Include the matching APK/module/content hashes, exact firmware support, test outcomes and unresolved limits. Update README, CHANGELOG, installation instructions and HANDOFF for implemented user-visible behavior. A module fixture pass is not physical KernelSU evidence, emulator CPU is not phone battery evidence, and a screenshot is not proof of native animation.

## Agent handoff checkpoints

After each milestone, record the tested source/build identity, changes made, evidence files, reproducible next command and remaining gate. Stop at unresolved restore, format or service-access gates rather than substituting a mock success. Keep incomplete features visibly experimental and avoid hiding blockers behind a generic “supported” badge.

The current next steps and scope are in the superseding handoff linked above. No root installation, module hardening, new app code, cloud request or native Apply is authorized by this planning document alone. Resume implementation only at the user's request; do not treat the inactive generation notes as a requirement.
