# Flip Pets continuation — 2026-10-11

## Current milestone — private root state and backend lifetime (step 3)

The user requested finishing the handoff, with a fresh independent review and
automatic code/APK upload after each completed milestone. Continue after uploading;
fully assembled physical phone testing is deferred. Root installation, native Apply,
generation and optional native widget hooks are not authorized by this source work.

- Root consent/receipt/cancellation use schema 1 under root-owned mode-0700
  `/data/adb/flippets-controller`, outside replaceable module scripts. Fresh or
  interrupted empty initialization does not opt in. Valid consent persists across
  updates; unknown schemas and unsafe paths fail closed. Legacy module-local
  consent is not silently migrated. Uninstall leaves bounded opted-out state.
- Root runtime is private. A stable regular root/shell-owned 0644 file opened
  read-only supplies a shared lifetime flock. FD8 survives supervisor/manual watcher
  creation; the short module transition FD9 does not. Stop the other backend first.
  Older pre-lease sessions also block root through their unchanged legacy markers.
  Only fixed regular obsolete root diagnostic leaves can be unlinked under lease;
  shell diagnostics are preserved and symlinks refused.
- Root observes module disable/remove and cancellation during normal policy polling
  and launch checks. Manual Start requires a watcher acknowledgement, rolls back
  failures, and restores a stale request after watcher death before explicit retry.
  Dead receipt-bound supervisor files are cleared before discarding their receipt;
  live unverified identities remain untouched and return failure.
- Final canonical/embedded bytes are identical and the preserved-key APK rebuilt.
  APK: `cf4aeedaf7018ec59d20a610b719ee7f920d564d04ac8c8d5ceb31670d45763e`.
  Module: `515750d44ab6e3792112bab8d176d855706aedf866f7ff7cd6c015f72379d851`.
  Canonical: `eaf0f94cc6a57ba21cc342c7c7b7fe5914215ae540d38b583ab7315e4af5d06c`.
- Fresh final verification: 151 command checks (15+23 shell, 15+23 generated root,
  29 live backend/manual/legacy tests, 44 wrapper race/update/death tests, two fresh/
  interrupted-state checks), eight Android shell syntax checks and current-APK
  signature/certificate/assets/ZIP/ELF 16 KiB structure verification. Evidence:
  `work/research/kernel-su-runtime-evidence.json`. Real emulator flock/processes;
  root UID metadata and HyperOS commands are stubbed, not actual root/SELinux proof.
- Fresh independent reviewers found the legacy pre-lease coexistence and manual
  watcher lifetime gaps. Both were fixed and covered. Final code review found no
  further actionable issues. Physical boot/unlock/fold/update behavior stays untested.
- No phone was targeted. Full current-SHA APK visual/lifecycle suites are still
  pending the assembled app milestone; historical 343+6 results are not reused.

Steps 1 and 2 are already pushed and published with verified matching assets:
`https://github.com/Sasha123453/FlipPets/releases/tag/dev-controller-startup-20261011`
and `https://github.com/Sasha123453/FlipPets/releases/tag/dev-controller-ownership-20261011`.
Step 3 publication uses `dev-controller-runtime-20261011` after this reviewed commit.

Next: app-owned native-launch card activity, isolated navigation/storage, validated
cover routing, normal foreground lifecycle and emulator touch/persistence/isolation
QA. Exact EEA FlipHome policy/admission still needs actual read-only device evidence;
do not invent a grant/boot restoration transaction without policy readback/restore.
Then prepare one known native pet resource with a decoded matching poster and a
guarded motion/restore proof workflow. Native Apply remains gated on actual motion
and exact restoration; continue independent source work. Generation is deferred and
small native widget hooks are optional, not required for the first full-screen cards.

## Historical milestones below

# Flip Pets continuation — 2026-10-11

## Current milestone — root ownership and module transitions (step 2)

The user requested continued implementation, a fresh independent review and
code/APK GitHub publication for each step. Fully assembled physical testing is
deferred. Root installation, native Apply and generation remain unauthorized.

- Root wrapper ownership now uses PID + process start time + boot ID, root-owned
  regular control files, and exact NUL-delimited interpreter/controller/`run`
  argv. A reused PID or command-line lookalike does not authorize stopping it.
- Module boot/Action/disable use a bounded Android `flock` transition. Detached
  controller children do not inherit that lock. A new disable generation cancels
  an in-progress Start before it can restore opt-in.
- Stale boot cleanup takes the lock and rechecks generations before deleting
  opt-in. Stop timeout retains its receipt; Action retries Stop. Receipt-write
  failure cleans up only a still-identical in-memory captured process, otherwise
  asks for app Stop and leaves unverified processes alone.
- Legacy ownership/opt-in markers are not silently treated as new consent. Module
  update migration is still unfinished. Shared root/shell runtime paths,
  cross-backend serialization, post-start module disable monitoring and actual
  rooted MIX Flip compatibility remain next work. Do not install this intermediate
  candidate for hardware testing before the assembled build is ready.
- Module-only change: APK/canonical/embedded bytes remain identical to step 1.
  APK: `012d42fa4548ef84e0d9c77f6769ebde4477fa20d0fa305953353f5cabdca361`.
  Current module: `1a049ca30d81575851ddc17a525ee4f2da55b2b84e2002f17e7bddb3cc3ed7a3`.
- 36 new wrapper command cases passed using real emulator process identities,
  background children and flock; UID ownership/storage/controller commands are
  stubbed. The unchanged canonical/root controller reports retain their verified
  matching hashes (76 checks). Seven final module/canonical syntax checks passed.
- Fresh independent review found a stale-boot cleanup race. It was fixed and
  covered by a deterministic interleaving test. The reviewer requested stop-timeout
  and post-ACK receipt-write failure cases; both were added and passed. Follow-up
  independent review found no additional actionable findings.
- Current scoped evidence: `work/research/kernel-su-ownership-evidence.json`.
  Full APK rendering/lifecycle QA still belongs to the historical release SHA;
  physical root/SELinux/display compatibility is not inferred from fixtures.

Step 1 is pushed as commit `d97a0db`, with exact assets and digests verified at
`https://github.com/Sasha123453/FlipPets/releases/tag/dev-controller-startup-20261011`.
Each development prerelease includes the matching APK, experimental module and
sanitized evidence. Generated binaries and signing keys remain excluded from Git.

## Implementation resumed — first controller hardening step

The user requested “read handoff.md and start doing”, then an independent review
at the end. This supersedes the planning-only implementation pause below. This
session implements the boot/startup part of the KernelSU milestone in
`docs/native-cover-root-and-rootless-agent-plan.md`; it does not authorize physical
phone changes, root installation, native Apply or generation. The subsequent
instruction authorizes a fresh independent review and code/APK GitHub publication
for each milestone. Physical testing is deferred until the fully assembled build.

- Canonical/embedded controllers remain byte-identical. `supervise` is explicit
  Start; new `resume` preserves Stop. Both wait for the child readiness marker,
  which is written after child verification and cleanup-trap installation.
- KernelSU boot waits at five-second intervals for up to ten minutes for primary
  user unlock and accessible app storage. Stop discovered after unlock cancels
  opt-in. Action opt-out and disable/remove flags cancel the wait. Timeout retains
  opt-in but does not start a retry daemon. See updated installation instructions.
- This is partial hardening. Exact process identity/PID reuse, serialized
  Action/boot/Stop, update migration, root-owned leftovers and post-start module
  disable handling still need work. Do not claim reliable physical KernelSU.
- APK rebuilt with the preserved signing certificate; matching root ZIP generated
  from the canonical controller. Version remains 1.1/code 12, development only.
- Current APK: `012d42fa4548ef84e0d9c77f6769ebde4477fa20d0fa305953353f5cabdca361`.
- Current root ZIP: `90e47d597584044c02d9c3d7d4b0385f403e346b4fc7e6a843f0a7da80ec062a`.
- Current canonical controller: `815e11a50f6549dbd14968e4fc3257dc0270d3c9f6800a1a9096e7f1afe2c99e`.
- Fresh structure checks passed: asset byte identity, original signing certificate,
  v3 signature, APK ZIP and both ABI ELF 16 KiB alignment. Report:
  `work/qa-final/apk-structure-current.json`.
- Existing 343 APK and six lifecycle passes below belong to APK `1d7d6181...`.
  They do not validate this rebuilt APK. No release/source/verification bundles
  are regenerated for this development change, and no phone installation occurs.

Fresh scoped verification: 15 canonical controller + 23 canonical supervisor +
15 generated UID0 controller + 23 generated UID0 supervisor + 15 module boot
command checks passed (91 total), plus seven Android `sh -n` syntax checks.
UID0/storage/device responses are fixture stubs, not physical root proof.
Exact hashes/report digests and limits:
`work/research/kernel-su-startup-hardening-evidence.json`. Local detailed reports
are in `work/qa-final/`; the old `work/qa-v02` supervisor report is preserved.

The user-requested independent agent review found no actionable correctness
issues in this bounded milestone. It identified missing late-child ACK-timeout
coverage; that fixture was added, independently rechecked, and passed for both
variants. Review does not certify the deferred ownership/migration work.
The identity-verified test emulator was shut down after collection; no physical
phone was targeted.

Next source milestone: exact process ownership and serialized module transitions,
then persistent opt-in migration/root-to-shell cleanup. Native launcher admission
still needs the exact EEA policy reader; native pet Apply remains gated on motion
and exact restore. Generation remains deferred. Reviewed milestones are pushed
to main with exact matching APK/module assets in a development prerelease; APK/ZIP
files remain ignored in the source tree.

## Previous planning and release state — 10 October 2026

## Latest planning direction — implementation paused by user

The user explicitly said “Do not make. Just plan for now.” Subsequent requests
authorized a detailed agent plan and a folded/unfolded visual concept, not code
implementation or device changes. Read the current detailed handoff:
`docs/native-cover-root-and-rootless-agent-plan.md`. It supersedes the sequence in
`docs/root-native-integration-plan.md`. The user subsequently deferred **Generate
my pet** and all generation backends. Use known donor assets for the native proof.
Phone is still unrooted. Priority: reliable KernelSU for the existing mode;
native FlipHome launching for folded unlocked app-owned cards; native tiny-keyguard
PAG for folded lockscreen pets after motion and exact restoration are proven.
Read-only Global FlipHome audit found ordinary launcher entries admitted through
the continuity service, plus a native 2X3 MAML widget host with a fixed catalogue
and private cached selection. Special `miui.fliphome.default` dispatch is gated
by a five-package set; a manifest action alone is insufficient. Native small widgets
are a later optional root extension, not a prerequisite for full-screen cards.
New evidence: `work/research/ruyi-fliphome-native-host-audit.json`. Global FlipHome
has not been hash-compared to the phone's EEA APK. No phone mutations occurred.
The current KernelSU wrapper was reviewed but not hardened in this session.
Concepts use historical Charlie frames and do not prove folded native playback.
Resume implementation only when requested; preserve the historical QA status below.

## Current user instructions

The user resumed work with “Read HANDOFF.md / Keep going”, requested English,
then requested mini-apps fill the entire cover and asked to obtain the cards from
18 Pro firmware instead of assuming the public HTML is the native implementation.
These instructions supersede the previous session's stop point below. The user
subsequently requested committing/pushing the finished new version to GitHub.
Phone installation, root installation, flashing, login and photo upload remain outside
this request. The larger native-runtime/KernelSU transplant idea was set aside at
that point; the planning-only native-host investigation above is the current direction.

## Current changes

- MiniAppView uses the original scripts' CANVAS_W/CANVAS_H contract: logical
  width 976, height from actual host bounds. Original backgrounds fill the cover;
  FIT/DX/DY retains proportional content and touch mapping. Asset HTML bytes and
  their provenance SHA values are unchanged. Dialog previews are portrait.
- Corrected dialog wording to say public Xiaomi catalogue instead of implying
  verified 18 Pro runtime identity.
- MiniAppsQa now uses asynchronous PixelCopy of the composed window and waits
  before switching/destroying cards. The host removes stale PNGs and writes a
  capture manifest bound to the APK SHA and image hashes.
- Pet QA fixtures temporarily suspend/restore mini-app selection with QaPetMode.
  The first broader suite found every switch assertion failed because an existing
  selected mini-app hid all pet renderers; failure evidence is ignored at
  work/qa-final/initial-switch-failure.json (old SHA fdcec2f...; not a current pass).
- Added work/tests/run_gallery_qa.py for real UI collections/type/search/favorites,
  preview/Apply/Cancel, virtual-cover screenshots, small-window and large-font QA.
  It must run separately from other device suites.
- Updated README, CHANGELOG, TODO, installation instructions and AGENTS policy.
  No unrelated donor changes were reset or staged.

## Firmware source answer

Read docs/donor18-mini-app-runtime.md and
work/research/hongkong-mini-app-runtime.json. Rehashed the complete product image
and checked both inspected APKs directly against the original partition bytes.
Extracted/CRC-checked six built-in card packages: Desk calendar, Upcoming events,
Incognito mode, Xiaomi Home camera, Xiaomi car, Stocks. They are MAML resources;
no standalone HTML/JS members were found in these six or the two inspected APKs.
Water/Vocabulary/Pomodoro were not found in these packages. Do not claim absence
from every APK or the online store, and do not relabel the existing public examples
as firmware extracts.

Donor subscreencenter contains JsCanvasScreenElement/QuickJsBridge and
libquickjs_canvas.so; the element runs inline MAML Script text or locale JS variants
against Android Canvas. Themes loads MTZ through RearScreenAiAppMamlView and has
native/page/v3/AI_GENERATED_APP, downloadUrl resolution and MTZ extraction paths.
This is source evidence, not a port of the native runtime or verified online access.
No native library or unrelated stock widget was added to the app. Raw packages,
full inventories and decompiled classes stay ignored in work/extracted/hongkong.

## Historical 10 October release artifacts and verification status

- APK: 1d7d6181abe85b5056f432c6f37a849ed31f2ba7710768c6f06a666dcace2c37
- KernelSU ZIP: d72d8c62d57fe3ea753b88f56712f0789d8431b54ec99858778306aed0dede82
- Signing certificate and both canonical/embedded controllers remain unchanged.
- Current structure report passed: work/qa-final/apk-structure-current.json.
- All seven current-SHA APK suites passed: 176 clip, 68 composition, 15 switch,
  15 utility, 19 layout, 23 donor18 and 27 mini-app checks: 343 total, zero
  failures/skips. Reports: work/qa-v03/device-files/. Catalogue clip coverage and
  original image/NinePatch counts are checked again by the release packager.
- Six virtual-cover lifecycle checks passed: work/qa-v03/runtime-v110.json.
  The host now waits for the actual emulator display and SurfaceFlinger readiness
  within 15 seconds instead of assuming a fixed two-second creation time.
- Pure timer/hinge, 1,106 geometry, 474 carp, 33 playback and eight synthetic import
  cases passed against the current source. Synthetic filesystem tests need a
  writable TEMP/TMP when the Windows sandbox's default temp is restricted.
- Mini-app screenshots use real PixelCopy, plus actual SurfaceFlinger virtual-cover
  captures. Reviewed all three card previews, Main preview and full cover images:
  backgrounds fill the 1208x1392 virtual cover, proportions and controls retained.
  The source's Chinese interface remains. These are not physical camera-clearance
  observations. Capture hashes are bound to the current APK.
- Supplemental gallery automation observed 18 successful collection/filter/search/
  favorite/Apply/Cancel/selection checks, then its accessibility reader lost the
  root during font/window recreation. The incomplete run is preserved honestly in
  work/qa-v03/gallery-qa.json; do not call it a complete 20/20 automated pass.
  The host retries fresh roots within a bounded launch deadline and offers
  --windows-only to separately check the two window/font layouts. That retry
  passed the large-font assertion but also timed out reading the small-window
  root. Separate real input opened the small-window gallery and its screenshot
  was reviewed: functional, but the headers leave only a short scrolling grid.
  Compact-window polish is deferred. See visual-miniapps-v110.json and both
  gallery automation reports; no complete supplemental automated pass is claimed.
- Donor QA exposed a fixture abort on deliberate Home destruction; poll now permits
  teardown only after homeRequested, retaining native release/ACK checks. The
  initial failure remains ignored at work/qa-final/initial-donor-hide-failure.json.
- Source/verification packaging uses work/package_release.py and exact current
  reports. Original-resource archives are not regenerated by --skip-originals.
  Catalogue import provenance uses LF serialization; packaging accepts Windows
  CRLF only for this generated JSON and records both hashes. APK/source assets
  and original donor files still require identical bytes. Git preserves original
  mini-app HTML and hongkong MAML bytes with -text attributes.
  APK/ZIP files, signing keys, raw donor data and emulator files remain excluded
  from Git. No physical phone or KernelSU runtime claim is added.

## Remaining work

The user authorized the source/evidence update to origin/main after final staging
review. Generated verification/source bundles are prepared with --skip-originals.
The emulator used for these checks is shut down after collection. No physical
installation was requested. Physical camera/touch clearance,
HyperOS recovery and battery use need fresh phone evidence for this version.

For native card replacement, obtain a verified matching MTZ or export before
promising a transplant; the six extracted built-ins are different cards. Preserve
rootless fold/lock/sleep policy. Photo generation and physical root/display-power
work remain subject to the constraints in AGENTS.md and the previous detail below.

---

# Previous handoff — historical snapshot, superseded above


Prepared on 2026-10-10 in `E:\FlipPets`.

## Stop point and user intent

The user asked to finish this session, write everything needed for another agent
in an English handoff, and rewrite `AGENTS.md` in English. Do not interpret this
handoff as authorization to install root, flash firmware, publish, push or continue
device experiments automatically.

The preceding requests were:

1. Explore and adapt Xiaomi 18 Pro rear-screen functionality to MIX Flip.
2. Make mini-apps look and work well. The user rejected our initial invented design
   and asked whether it really looked like 18 Pro. Authentic Xiaomi source matters.
3. Investigate creating an animated, 3D-looking pet from the user's animal photo,
   like the demonstrated Xiaomi feature. This is still unimplemented.
4. Prepare a root module if ADB cannot solve integration. The phone currently has
   no root; the user plans to use KernelSU.
5. Separate interface cards into collections such as 17 Pro, 18 Pro and Personal.

Read `AGENTS.md` first. It preserves the repository's original constraints and adds
the current mini-app, gallery and optional root-module contracts. The default
remains rootless, open/awake/unlocked-only operation with stock fold/lock/sleep/AOD.

## Repository state

- This is the actual Git checkout. Do not edit the older historical workspace.
- Many donor-18 changes were already present at the start of this work. The tree
  remains dirty and includes numerous pre-existing modifications/untracked files.
  Do not reset, clean, stage everything, or attribute all changes to this session.
- No commit or push was made. No phone installation, root installation, flashing,
  account authentication or photo upload was performed in this session.
- The local signing key was preserved. The canonical and embedded rootless
  controller scripts are byte-identical and were not changed by the mini-app work.
- App version remains 1.1, version code 12. No release version bump was made.
- README, CHANGELOG, TODO and `outputs/START-HERE.txt` describe the new features
  and limitations. Documentation is not proof of completed hardware verification.

## Current artifacts and exact identity

| Artifact | SHA-256 |
|---|---|
| `outputs/FlipPets.apk` | `ae2488180a6b2282cc907aca78bf74849dd6a5b4a77f1cb678d1015a2d71eee3` |
| `outputs/FlipPets-KernelSU-experimental.zip` | `835e93714c6434fb495fab9bd411e664210c71029d4639e3b7f8310cb6a69513` |
| Canonical/embedded rootless controller | `91c923d909f5c404480843ab5b006ab2503c87d88274cd4310c36b378163e853` |
| Generated root controller | `6df37a0ee00a00fae93ce2d93bf9fb094e6b6708e957afff59ece699759e576a` |

Generated APK/ZIP files remain ignored. The module ZIP's `build-evidence.json`
identifies this APK and hashes its module files. Recheck all identities after any
rebuild. Build with `python -X utf8 work/build_apk.py`, then regenerate the optional
ZIP with `python -X utf8 work/build_kernel_su_module.py`.

The APK uses the original local certificate, SHA-256
`819b54a88b032712475060b68a6adcfff569366c86e9683c92934b36375391ba`.
Final source assets, v3 signature, ZIP alignment and both native ABI ELF LOAD
alignments were verified by `package_release.apk_checks`. The SHA-bound structure
report is local/ignored: `work/qa-final/apk-structure-current.json`.

## Authentic mini-app implementation

The rejected first prototype was removed. The current implementation bundles three
original public Xiaomi Canvas HTML examples, byte-for-byte. This is an adaptation
of official public examples, not verified identity with the native 18 Pro runtime.

Public source discovery:

- Landing page: `https://m.mi.com/appcard`
- Frontend: `https://cdn.cnbj1.fds.api.mi-img.com/ai-app-fe/index-DOugxhMB.js`
- Public catalogue: `https://cdn.cnbj1.fds.api.mi-img.com/ai-app-fe/appList.json`
- Original cards: the same CDN prefix followed by `apps/1.html`, `apps/3.html`
  and `apps/5.html`. The public catalogue contained 100 records when inspected.
- Sanitized provenance: `work/research/xiaomi-mini-apps-provenance.json`.
- Ignored downloaded source evidence: `work/extracted/hongkong/official-appcard.html`,
  `official-appcard.js` and `official-app-list.json`.

| Source ID | Card | Original HTML SHA-256 |
|---|---|---|
| 1 | Water: eight glasses, progress, splash/celebration | `92c9a05d3f725cda8639887ddbd9352eef9ded1c9d44a297c8a693745a24bc44` |
| 3 | English/Chinese vocabulary: batches of 20, known/unknown, weighted repeats | `190752e7bfbddcb9516af97932596c599b6592cf81c9ae3612c6f7b661547157` |
| 5 | Pomodoro: 25/5-minute phases, start/pause/reset/skip | `f06cab695c3b711199eb3bd9f3bf8d60be8d4e49a28c82544751cdc8a261aa58` |

Stored assets: `work/app/assets/miniapps/xiaomi/{1,3,5}.html`, with `NOTICE.txt`.
Chinese UI and the English/Chinese vocabulary are retained. The water goal is
eight glasses, not the rejected prototype's configurable milliliter counter.
The vocabulary source contains unused flip-rendering code, but no working
tap-to-flip interaction; the real known/unknown buttons are tested instead.

Relevant Java files, all under `work/app/src/org/flippets/app`:

- `MiniAppStore.java`: explicit selected-mode preference and package-scoped event.
  Original pages own their state in private WebView localStorage.
- `MiniAppView.java`: offline WebView host, three native switching buttons,
  aspect-preserving 976 x 596 canvas centered on the portrait cover. Black fields
  are intentional; the different hardware aspect ratio prevents an exact layout copy.
- `MiniAppsDialog.java`: isolated preview, explicit Apply/Cancel/return-to-pet;
  accepts an initial card when opened from the gallery.
- `MiniAppsQa.java`: 27 emulator-only functional checks using real MotionEvents,
  actual page state/localStorage and a random isolated QA origin.
- `PetStage.java`: switches rendering roles, releases hidden pet media/sensors and
  the pet ticker, destroys hidden WebViews, restores the pet on return.
- `MainActivity.java`: selection text, shortcut, dialog/lifecycle management.

Host restrictions: dedicated local HTTPS origins; only the three bundled HTML
paths are served; viewport and restrictive CSP are injected at load time; network,
file/content access, outside navigation, mixed content and page permissions are
blocked. There is no native JavaScript bridge and no new INTERNET permission.
Main and dialog previews disable DOM storage and use a separate preview origin.
Visible applied cards use private persistent storage. No global WebView timer pause
is used because Main and the real cover can coexist.

The original animations run while visible. Hidden WebViews are destroyed. Pomodoro
uses the source's wall-clock/endAt policy; it is not an exact/background alarm.
It does not deliver hidden audio or guarantee background phase transitions. No
physical phone CPU/battery measurement or camera-clearance verification exists.
Details: `docs/mini-apps.md`.

## Gallery collections

`GalleryDialog.java` now has a source-collection row and a separate type-filter row.
Search and favorites combine with both filters. Catalogue IDs/metadata were not
rewritten; mini-app rows use separate negative adapter indices and `mini-*` favorite
IDs. Selecting a mini-app opens its preview and requires Apply. Existing pet
selection clears the mini-app mode. A hidden pet is no longer marked selected
while a mini-app is active.

Observed collection counts with all type filters enabled:

| Collection | Count | Classification |
|---|---:|---|
| All | 36 | 33 catalogue entries plus 3 mini-apps |
| 17 Pro | 18 | Explicit 17 Pro source, excluding personal templates |
| 18 Pro | 6 | 3 donor entries plus 3 original mini-apps |
| Personal (`Свои`) | 4 | `photo`, `signature`, `paper`, `calendar` templates |
| Xiaomi Archive | 8 | Presets without verified donor-model attribution |

Personal is a collection of OEM-derived templates for the user's photo/text, not
four newly generated characters or an independent library of multiple imported
photos. Mini-app gallery thumbnails are native typographic placeholders, not
screenshots of the original artwork; visual refinement remains possible.

## KernelSU candidate

Source: `work/kernel-su/`; builder: `work/build_kernel_su_module.py`;
instructions: `docs/kernel-su-module.md` and `outputs/START-HERE.txt`.

The script-only module checks KernelSU at installation and MIX Flip `ruyi` identity.
It has no framework/system overlay, system properties, sepolicy patch or APK bundle.
The controller is generated from the canonical script by replacing its UID check
with UID 0; fold/lock/sleep policy stays unchanged. Action explicitly toggles the
session. Installation alone does not enable it. Enabled sessions attempt boot
resumption, respecting the app's persistent Stop request.

`module-control.sh` checks ownership using its marker, root UID and the exact
supervisor command line; it refuses to take over an ADB/Shizuku session. It also
handles an owned stale root lock. Disabling/uninstalling must affect only its own
session. Review these ownership branches before privileged phone testing.

Verified locally: 15 existing controller command-fixture cases against the exact
generated root variant, with UID 0 stubbed; six generated shell scripts passed
Android `sh -n`. Reports are local/ignored under `work/qa-final` and `work/ksu-check`.
These do not prove actual UID 0 launching, SELinux compatibility, module-wrapper
ownership behavior, boot ordering or physical KernelSU/HyperOS operation.

The candidate is only an alternative supervisor. It does not keep the cover active
after real main-screen sleep or implement a native folded secure wallpaper.

## Photo-to-pet investigation

No working generator or fake generation button was shipped. No user photo was
provided/uploaded. The existing private photo import is not this feature.

`docs/photo-pet-generation.md` records offline inspection of verified donor Themes
11.5.3.1, APK SHA-256
`3888058041439577aadbb933c9bed1fb3ef16acda20d15404fb620314a8edd0a`.
The `com.rearScreen.aiCompanion` pipeline sends a local reference file and prompt
through `AiWallpaperManager` / `StartWithAiCompanionHandle`, first
`accompanyPic2Pic`, then confirmed image to `accompanyPic2Video`, with polling and
`POST ai/acquire`. Raw text/image URLs are encrypted with a key obtained during
the earlier stages; result constants include `generated_static.png` and `details.mtz`.

This supports an image-to-image-to-video/resource pipeline, not proof of a genuine
3D mesh/rig or continuous 3D renderer. Exact gateway availability, account/token/
signature requirements and access on MIX/EEA still need tracing. Root supplies
neither backend access nor server keys. A real service/export or a documented
alternative generator is needed before an end-to-end feature can be promised.

Ignored decompilation evidence is under `work/extracted/hongkong/`, including
`AiCompanionApiService.java`, `AiCompanionRealApiProvider.java`, its generateImage
and submitVideoTask coroutine classes, `AiCompanionAcquireApi.java`,
`AiCompanionConstants.java` and `CompanionGenerateRawDataBuilder.java`.

## Verification: what passed and what did not

For the exact current APK SHA above:

- Build succeeded with the preserved signing certificate.
- Assets matched source bytes; v3 signature, ZIP and native 16 KiB alignment passed.
- `run_mini_apps_qa.py`: **27/27 passed, zero failures, no skips**. Report:
  `work/qa-v03/device-files/mini-apps-qa.json`.
- Functional coverage includes original HTML hashes, explicit Apply/Cancel, hidden
  pet release/ticker shutdown, real water/Pomodoro/known/unknown touches, storage
  persistence, offline restrictions, stop/restart and restored preferences.
- A real UI probe observed all five collection counts above and search for
  Pomodoro within 18 Pro returning one item. It then failed to locate the card's
  off-screen title by text. This is **partial UI evidence, not a completed gallery
  QA pass**; selection/preview and favorites/type combinations remain to verify.

Known visual-evidence problem: `MiniAppsQa.capture()` calls `stage.draw(Canvas)`.
The pulled `mini-focus.png`, `mini-water.png` and `mini-words.png` omit the hardware
WebView canvas and appear black apart from native host controls. Do not publish
them as successful visual verification. Fix capture with actual rendered pixels
(for example canvas `toDataURL` for source artwork, and window/PixelCopy or actual
device screenshots for host layout), then inspect the results. This was discovered
after the functional suite passed and was deliberately left for the next agent
when the user requested the handoff.

The temporary gallery probe is ignored: `work/qa-final/check-gallery.py`. Its
screenshots/XML are under `work/qa-v03/`. It tested Main using the short cover-sized
window (1208 x 1392/520), leaving little grid height. Repeat at the observed Main
size (1224 x 2912/520), and use the card's content description or scroll the grid
instead of requiring an off-screen title node. `gallery-18pro-current.png` is a
real screenshot, but not a complete visual review of all cards.

**Not rerun on the final APK:** standard 274 render/composition/switch/utility
checks, 19 pet-layout checks, 23 donor-18 checks and six virtual-cover lifecycle
checks. Existing reports for those suites belong to older APKs, including the
rejected prototype, and must not be reused as current evidence. No final release
archive or Verification bundle was regenerated. Earlier package/report files in
outputs may therefore be stale relative to the current APK.

`work/package_release.py` was updated to require mini-app QA (27 checks) and include
the new root builder/module sources. Its complete APK suite total is now 343,
plus six lifecycle checks if freshly supplied. It must reject stale reports.

## Next steps, in order

1. Review this dirty checkout and the actual diff; preserve unrelated donor work.
2. Fix mini-app screenshot capture and inspect all three original cards plus the
   Main/dialog/real virtual-cover host at the correct window sizes. Rebuild if code
   changes and rerun the 27 checks for the new exact APK SHA.
3. Complete gallery UI verification: collections, type intersection, search,
   favorites, normal selection and mini-app preview/Apply/Cancel. Inspect long
   names, smaller windows and large system font. Avoid claiming the UI is polished
   solely because item counts match.
4. Run the final APK suites separately, with explicit emulator targeting:

   ```powershell
   python -X utf8 work/tests/run_release_qa.py
   python -X utf8 work/tests/run_pet_layout_qa.py
   python -X utf8 work/tests/run_donor18_qa.py
   python -X utf8 work/tests/run_mini_apps_qa.py
   python -X utf8 work/tests/runtime_cover_qa.py
   ```

   Expected totals: 274 + 19 + 23 + 27 = 343 APK checks; six additional lifecycle
   checks make 349. Validate SHA, exact counts, zero failures and no skips.
5. Regenerate the matching KernelSU ZIP after the final APK. Test ownership/Stop/
   boot behavior before any phone claim. Actual root testing must wait for the
   user's rooted phone; preserve stock Power and lock semantics.
6. If packaging is requested, use `work/package_release.py` only after fresh QA.
   Its default profile discovery can find a stale `resource-profile-v110.json` and
   correctly refuse it. Supply a real current profile, or use a clean QA directory
   without stale automatically discovered profiles. Do not relabel old profiles.
7. Resume the photo generator only with a verified service path and explicit user
   confirmation before sending an actual photo. Do not disguise a static import
   or generic animation as the requested generated pet.

## Local tool notes

- Shell: PowerShell. ADB: `C:/platform-tools/adb.exe`. Always pass
  `-s emulator-5554` for emulator operations and assert `ro.kernel.qemu=1`.
- In this session ADB required sandbox escalation; it was approved. No approval
  rejection is outstanding. Do not bypass sandbox rules or target a phone implicitly.
- Portable emulator executable was read/run from the historical workspace:
  `C:/Users/shelk/Documents/Codex/2026-10-03/mi-mix-flip-xiaomi-xia/work/tools/sdk/emulator/emulator.exe`.
  This was a tool dependency, not an alternate source checkout.
- AVD: `work/emulator/avd/fliptest.avd`; set `ANDROID_AVD_HOME` to
  `E:\FlipPets\work\emulator\avd` and `ANDROID_USER_HOME` to
  `E:\FlipPets\work\emulator\home`.
- Software GPU launches repeatedly terminated the entire emulator during WebView
  QA. `-gpu host -feature -Vulkan -no-window -no-snapshot -no-audio -port 5554`
  was stable for the successful current functional run. Do not turn those earlier
  crashes into passed tests or phone performance evidence.
- No new multi-agent work was authorized. Keep any continuation in this checkout
  unless the user explicitly asks otherwise.
- At handoff, the app was stopped on the guarded emulator and this session's
  `emulator-5554` was shut down. No QA process is intentionally left running.
