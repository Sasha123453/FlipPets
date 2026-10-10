# Flip Pets: contributor and agent instructions

## Product and authorized scope

Build an Android adaptation of Xiaomi 17/18 Pro rear-screen artwork and behavior
for Xiaomi MIX Flip. Prefer verified donor resources and MAML evidence over
invented behavior. Never call an adaptation an exact copy without verification.
Read `HANDOFF.md` for the latest state, outstanding work and evidence.

The default controller is rootless: Shizuku shell UID 2000 opens our cover activity
only while the phone is fully open, awake and unlocked. Folding, locking or sleeping
returns control to Xiaomi's stock cover interface and AOD. Preserve this policy.
Keep the cover task separate from Main. `CoverGuard` is a user-enabled foreground
session service, not a frame loop. Closing Main must retain the cover session;
explicit Stop must close only our tasks and signal the shell supervisor.

The user authorized an optional KernelSU module and said root is not installed yet.
The experimental module only substitutes a root supervisor for Shizuku. It does
not solve independent display power, folded lockscreen or AOD integration. Do not
install root, change the framework or claim physical root compatibility without
appropriate device work. Keep the rootless path as the default.

Battery, music and the existing visual timer overlay remain optional and off by
default. New modes require an explicit user choice. Prioritize authentic donor
animations and native integration over duplicating Xiaomi's stock widgets.

## Repository and build

- Work in the Git checkout at `E:\FlipPets`. The earlier Codex workspace is a
  historical copy; do not split source edits between the two directories.
- Java sources: `work/app/src/org/flippets/app`. There is no Gradle build. Run
  `python -X utf8 work/build_apk.py` from the root. It uses portable JDK 17 and
  Android 36 tools under `work/tools`.
- Minimum SDK 29; target SDK 35; package `org.flippets.app`; native ABIs
  `arm64-v8a` and `x86_64`. Preserve 16 KiB ELF LOAD and APK ZIP alignment.
- Artwork and binary dependencies use Git LFS; run `git lfs pull` after cloning.
  Keep SDK/JDK, firmware images, emulator data, generated APK/ZIP files and signing
  keys ignored. Preserve unrelated working changes.
- Preserve the existing local signing key so updates retain private photos and
  settings. Never commit it or include it in source/evidence archives. Replacing
  it can require uninstalling the app and losing its private data.
- `outputs/flip-pets-control.sh` and `work/app/assets/controller.sh` must remain
  byte-identical. Rebuild the APK after changing its embedded controller.
- Build the optional root ZIP with `python -X utf8 work/build_kernel_su_module.py`.
  Generate its controller from the canonical script; do not maintain a divergent
  root implementation. Build evidence must identify the matching APK SHA.
- Our generated code is MIT-licensed. Xiaomi artwork, fonts and original HTML
  retain their owners' rights and are excluded from the code license. Preserve
  provenance records and dependency notices.
- Explicitly use UTF-8 when reading/writing text with Python on Windows. The
  host's default encoding can corrupt Russian UI strings.

## Layout, lifecycle and privacy

- Observed cover: 1208 x 1392, density 520, rotation 2. Main: 1224 x 2912,
  density 520. Use actual window bounds/insets. Screenshots and schematic camera
  circles do not establish physical camera clearance.
- Version 0.9.1 uses `CoverGeometry`, fixed subject focus per family and placement
  at the bottom right. Most pets are 10% larger than intermediate 0.9; Coco fills
  the opaque scene width. There is no rectangular camera-column crop. Opaque
  scenery follows the source transform and blends at its top edge. `CoverPreview`
  renders the same virtual cover before scaling. Wide effects can cross the
  camera area or crop at screen edges.
- Charlie's crest is clipped in intermediate source frames; padding did not
  recover those pixels. Do not call it fixed. MP4 avatars retain opaque source
  rectangles. Ordinary PAG live wallpaper shares the activity geometry; its
  direct-Surface MP4 path still has the earlier placement and is not camera-safe.
- Version 1.0 stores per-pet With clock / Without clock profiles in `scene-ID`
  preferences. With clock preserves the exact 0.9.1 automatic geometry.
  Clockless enlarges on the right using fixed face guides; round pets remain
  width-limited. Manual scale (60-160%) and X/Y (+/-25%) are relative to that mode's
  automatic placement. The editor reparents the existing preview/decoder. Drafts
  must not affect the cover before Apply. Cancel restores the preview; Reset
  affects only the selected mode. Clockless releases clock assets and skips
  minute redraws. Photos, compositions and Flowing glitter keep separate controls.
- Start sensors, decoders, ticks and listeners only while their panel is visible;
  release them on stop. No wake locks, background video decoding, per-frame logs
  or per-second preference writes. Shizuku must restart after reboot; do not
  promise survival of force-stop or OEM restrictions.
- Standard hinge-angle values are degrees. Xiaomi `flip_status` is categorical,
  not a measured continuous angle. Preserve stock transitions without a usable sensor.
- Imported photos must become bounded private copies through Android's document
  picker. Do not rely on temporary source URIs or upload photos as part of import.
  A future online generator requires explicit confirmation of the service and
  photo upload. Keep secrets out of APKs and repository files.
- Keep logs bounded and limited to this app. Never log notification contents,
  track titles, photo contents or frame/sensor streams.

## Gallery and original mini-app cards

- The user requested collections by origin: 17 Pro, 18 Pro, Personal (the UI uses
  the Russian label for personal photo/text templates), and Xiaomi Archive.
  Keep type filters, search and favorites within the selected collection.
  Do not assign an unverified donor model to archived presets.
- The gallery exposes 33 catalogue entries plus three separate mini-app entries.
  Do not change original catalogue IDs/metadata merely to reorganize the UI.
  Personal contains four OEM-derived customization templates, not an AI generator.
- The user rejected our invented mini-app design. Current cards are original
  public Xiaomi HTML examples from `https://m.mi.com/appcard`, bundled offline:
  water (ID 1), English/Chinese vocabulary (ID 3), Pomodoro (ID 5). Source hashes:
  `work/research/xiaomi-mini-apps-provenance.json`.
- Preserve original stored HTML bytes and attribution. The host adds viewport/CSP
  at load time. The user requested full-screen cards: supply the original scripts'
  CANVAS_W/CANVAS_H contract (976 logical width, height from actual bounds), fill
  the portrait cover and preserve proportional content/touch mapping. Public
  examples do not prove native 18 Pro runtime identity. Firmware audit and six
  extracted built-in cards: `docs/donor18-mini-app-runtime.md`.
- Keep WebView offline, with file/content/network access and external navigation
  blocked, no native JavaScript bridge and permissions denied. Preview storage
  must be isolated/disabled. Browsing or Cancel must not change live selection or
  card data; only Apply selects a card. Destroy hidden WebViews and release hidden
  pet resources. Do not use global `pauseTimers()` across independent displays.
- The original vocabulary card shows word, pronunciation and translation, with
  known/unknown actions and weighted repeats. Unused flip-rendering code does not
  establish a working tap-to-flip action. Pomodoro is not a background alarm.
- See `docs/mini-apps.md`, `docs/kernel-su-module.md` and
  `docs/photo-pet-generation.md`. Root does not provide Xiaomi's generation backend.

## Donor 18 Pro implementation

- Version 1.1 resumed 18 Pro import at the user's request. Selected product and
  system_ext partitions and original source/member hashes are verified; the whole
  OTA is incomplete and unverified. Keep its ignored resumable archive non-flashable.
  There are 33 entries, 176 clip paths and 148 unique media SHA-256 values. Original
  1.0 IDs and metadata remain intact. See `docs/donor18-resource-import.md`.
- Carp is a source-backed Java adaptation: four canonical hongkong 456 scenes,
  29 original clock PNGs, original thresholds and 500/100/300 ms fades. Automatic
  local selection must never write preferences/global revisions. Actual file-load
  acknowledgement starts the delay. Stop releases callbacks/media. Do not
  duplicate variant 488 as four additional scenes.
- Vortex is an animated background only. The card effect is a finite manual
  preview, not NFC or AI integration. Background/effect roles use full-canvas,
  aspect-preserving placement without app clock/pet controls.
- Online Themes routes: `docs/online-rearscreen-themes.md`. Authenticated
  download/import has not been verified.

## Deferred native wallpaper and display power work

Read `docs/folded-wallpaper-options.md`, `docs/independent-display-power.md` and
`TODO.md` before resuming native integration. The user deferred folded wallpaper
and continuation after any main-screen shutdown, including Power and timeout.
An app-only launch button is not an acceptable substitute. A root supervisor alone
does not resolve these limitations.

The wallpaper engine has outer-lock target 8, but shell filesystem write checks
fail despite mode 0777 directories. Known Themes video import targets inner 1/2/3.
Do not call it outer video import or change wallpaper type before a verified
resource-copy and exact restore path exist. The tiny editor accepted donor JSON
through `param_template_item_json`; PAG motion, Apply and rollback remain unverified.

`cmd display power-off 0` produced main OFF / cover ON while PowerManager stayed
Awake. This is not secure sleep or AOD evidence. Preserve native Power and secure
keyguard semantics. Do not replace the lockscreen with an activity, keep the screen
awake to imitate AOD or introduce repeated wake/ON/brightness hacks.

## Testing and evidence

- Scope verification to the change. Pure logic/controller tests are in `work/tests`;
  controller fixtures simulate commands and do not prove HyperOS behavior.
- Target `emulator-5554` explicitly and assert emulator identity. Physical helpers
  require an explicit serial and MIX Flip identity verification. Never use an
  implicit ADB target when phones/emulators may coexist.
- Emulator-only APK QA: `qa` (176 clips), `qaComposition` (68 checks), `qaSwitch`
  (15 transitions), `qaUtilities` (15 checks), Main `qaPetLayout` (19 checks),
  `qaDonor18` (23 checks), Main `qaMiniApps` (27 checks). Run specialized suites
  separately using their host scripts. Await completion and pull each named JSON.
  Require the exact installed/current APK SHA, expected test set/count, zero
  failures and no skips. Historical results never validate a rebuilt APK.
- Layout QA tests real controls/matrices and restores preferences. Clear only our
  Main task's stale QA launch extras before ordinary UI tests. Utility QA must
  discover a synthetic session through the real notification listener; no mock pass.
- Donor QA must observe real native progress and two automatic transitions.
  Never fake progress. Hidden-delay checks inspect native view properties against
  the real load-ACK timestamp, not compositor frame timing. Its host isolates and
  restores notification access and performs real Home with a SHA/token handshake.
- Mini-app QA uses real MotionEvents and an isolated random origin. Verify rendered
  pixels separately: software `View.draw()` can omit hardware WebView content and
  produce black screenshots even when functional assertions pass.
- `runtime_cover_qa.py` covers six virtual-display lifecycle checks: Main task
  removal, foreground session, simulated fold and notification Stop. It proves
  neither physical hinge behavior nor HyperOS integration.
- CPU 100% means one CPU core. PSS is not battery drain. Distinguish software
  emulator decoding from phone hardware results.
- Package with `work/package_release.py`, never `package_v03.py`. Fresh package
  evidence must match the exact APK. Keep historical hardware/lifecycle/profile
  evidence bound to its original SHA and state current untested features.
- Historical 1.0 passed 287 APK checks, six virtual-cover checks and 1,076 source
  geometry assertions. It was installed as an update with exact installed SHA;
  `hardware-install-v100.json` is installation-only evidence, not physical layout QA.
- Phone 0.5 confirmed two screens, fold return, hardware decoding and private photo
  persistence on EEA HyperOS 3.0.303. Version 0.7 also confirmed Shizuku startup,
  foreground service, hinge-angle registration and retention after Main was removed
  from Recents. Recovery was intermittently about 20 seconds, including rollback/
  backoff. Version 0.8 added bounded display readiness/launch retries; fresh phone
  evidence is required before claiming that recovery fix works.
- Preserve phone `stay_on_while_plugged_in=0` (restored and verified during 0.7 QA)
  and the observed 60000 ms screen timeout. Never publish serial numbers.
- Raw phone material belongs only in ignored `work/phone-qa`. Public evidence must
  exclude identifiers, private images, other-app UI and private collected metadata.

## Changes and publishing

Update README, CHANGELOG and installation instructions for user-visible changes.
Include meaningful verification and remaining hardware limits in the handoff.
Before a requested push, inspect staged files for generated output, signing keys,
credentials and private device data. Do not reset unrelated changes.

User repository: `git@github.com:Sasha123453/FlipPets.git`. The checkout may use its
local HTTPS rewrite if SSH is unavailable. Never put credentials in commands or
repository files. Do not claim a commit, push, install or package operation occurred
unless it actually did.
