# Flip Pets: instructions for contributors and coding agents

## Product and scope

Build a rootless Android port of Xiaomi 17 Pro rear-screen artwork and behavior
for Xiaomi MIX Flip. Prefer actual donor resources and MAML evidence over invented
behavior. Do not call an adaptation an exact copy unless it has been verified.

The current controller uses Shizuku's shell UID 2000 to show our cover activity
while the phone is open and unlocked. Folding, lock, and sleep restore Xiaomi's
own cover interface and AOD. Preserve that default. The next priority is an
optional native animated cover-lock wallpaper on the folded phone, through the
stock Xiaomi wallpaper editor/engine. Do not replace the secure lock screen with
an activity or keep the display awake to imitate AOD.

Battery, music, and visual timer cards are optional and off by default. Xiaomi's
stock folded-screen widgets already cover many of these needs; prioritize donor
animations and native integration. New modes must be explicit user choices.

## Repository and build

- Work from the Git checkout, currently `E:\FlipPets`; the earlier Codex workspace
  is a historical copy. Do not split edits between the two directories.
- Android code is Java in `work/app/src/org/flippets/app`; there is no Gradle build.
  `work/build_apk.py` uses the portable JDK 17 and Android 36 tools under `work/tools`.
  Run `python -X utf8 work/build_apk.py` from the repository root.
- Min SDK 29, target SDK 35; package `org.flippets.app`; native ABIs arm64-v8a and
  x86_64. Preserve 16 KiB native LOAD alignment and APK zip alignment.
- Artwork and binary dependencies use Git LFS. Run `git lfs pull` after cloning.
  Keep SDK/JDK, firmware images, generated APK/ZIPs, and signing keys ignored.
- Preserve the existing local signing key for update installation. Never commit
  it or include it in a source/evidence ZIP. Replacing the key requires uninstall
  and can lose private photos/settings.
- `outputs/flip-pets-control.sh` and `work/app/assets/controller.sh` must match
  byte for byte. The embedded script is rebuilt into the APK.
- Generated code is MIT; Xiaomi artwork/fonts retain their ownership and are
  outside the code license. Keep provenance and dependency notices.

## Behavior, layout, and resource use

- Cover hardware observed: 1208x1392, density 520, rotation 2. Main screen:
  1224x2912, density 520. Use actual Window bounds/insets; cover screenshot pixel
  proportions alone do not prove physical camera clearance.
- Version0.9.1 uses `CoverGeometry`, fixed subject focus per family and bottom-right
  placement, most10% larger than intermediate0.9; Coco fills the opaque scene width. There is no rectangular camera-column
  crop. Opaque scenery aligns with the source transform and blends at its top edge.
  `CoverPreview` renders the same virtual cover before scaling. Wide effects may
  cross the camera area or crop at screen edges; camera circles are schematic.
  Charlie has a source crest slice in intermediate frames; padding did not recover
  pixels. Do not describe it as fixed. MP4 avatars retain opaque source rectangles.
  Ordinary PAG live wallpaper shares that geometry; its direct-Surface MP4 path
  still has the earlier placement and must not be claimed camera-safe.
- Version1.0 adds explicit per-pet With clock / Without clock profiles in
  `scene-ID` preferences. The default clock geometry is exactly0.9.1. Clockless
  enlarges on the right using fixed face guides; round pets remain width-limited.
  Manual scale60–160% and X/Y±25% are relative to that mode's automatic placement.
  The dialog reparents the existing preview/decoder; its local draft must never
  affect the cover before Apply. Cancel restores the preview; reset affects only
  the selected mode. Clockless releases clock assets and skips minute redraws.
  Photos, compositions and Flowing glitter retain their dedicated controls.
- Keep the cover task separate from Main. `CoverGuard` is an enabled-session
  foreground service, not a frame loop. Closing Main should retain the cover;
  explicit Stop must close only our tasks and signal the shell supervisor.
- Rootless Shizuku needs restarting after reboot. Never promise uninterrupted
  auto-start after reboot or survival of force-stop/OEM restrictions.
- Start sensors, decoding, timer ticks, and view listeners only while their panel
  is visible; release them on stop. No wake lock, background video decoding,
  frame-by-frame logs, or per-second preference writes.
- Standard hinge-angle values are degrees. Xiaomi flip_status is categorical;
  do not treat it as a measured continuous angle. Without a usable sensor,
  preserve the stock transition.
- Photos imported through Android's document picker become bounded private
  copies. Do not store reliance on a temporary source URI or upload photos.
- Keep app logs bounded and limited to this app. Do not log notification text,
  track titles, photo contents, or frame/sensor streams.

## Testing and evidence

- Scope verification to the change. Pure timer/hinge/playback/controller logic
  has tests in `work/tests`. Controller fixtures simulate hardware signals.
- Emulator tools explicitly target `emulator-5554` and assert emulator identity.
  Never use an implicit ADB device when multiple emulators/phones are attached.
  Physical helpers require an explicit serial and verify MIX Flip identity.
- Current APK QA extras are emulator-only: `qa` (170 clips), `qaComposition`
  (68 checks), `qaSwitch` (15 transitions), `qaUtilities` (15 checks). Run UI and
  utility QA separately, wait for completion, and pull each named JSON. Check
  APK SHA, counts, failures, and skipped tests before accepting results.
- Version1.0 additionally requires `qaPetLayout` on Main:19 real dialog/control,
  renderer matrix and preference-restoration checks. Use `run_pet_layout_qa.py`
  separately. Clear only our Main task's stale QA launch extras when restarting
  normal UI tests. Final1.0 passed287 APK checks and6 virtual-cover lifecycle
  checks, plus1,076 source geometry assertions; new physical layout is unverified.
  Version1.0 was installed as an update on MIX Flip and exact installed APK SHA
  was verified; `hardware-install-v100.json` is installation-only evidence.
- Utility QA uses a synthetic MediaSession through the real notification
  listener. Failure to discover it must not become a mocked pass.
- `work/tests/runtime_cover_qa.py` tests virtual secondary display, Main task
  removal, foreground session, simulated fold receiver, and notification Stop.
  It does not prove HyperOS behavior or physical hinge events.
- CPU samples report 100% as one CPU core; PSS is not battery drain. Label
  software-decoded emulator results separately from hardware phone results.
- Package with `work/package_release.py`, not the historical `package_v03.py`.
  Fresh QA must match the exact APK. Keep historical hardware/lifecycle/profile
  evidence with its original SHA and clearly state untested current features.
- Phone baseline 0.5 confirmed two screens, fold return, hardware decoding and
  private photo persistence on EEA HyperOS 3.0.303. Version 0.7 also confirmed
  Shizuku startup, foreground service, actual hinge-angle registration and
  retention after Main was swiped from Recents. Fold recovery was intermittently
  slow (about 20 seconds, including first-launch rollback/backoff); that baseline
  does not establish stable recovery. Version 0.8 adds bounded display readiness/
  launch retries; require fresh phone results before calling that fix verified.
- A prior USB test temporarily set `stay_on_while_plugged_in=2`; original value
  was 0. During the authorized 0.7 phone test it was restored to 0 and confirmed.
  Preserve that restored value; screen timeout was 60000. Do not publish serials.
- Raw phone dumps belong only in ignored `work/phone-qa`. Public evidence must
  omit device identifiers, private images, other-app UI, and collected metadata.

## Changes and publishing

Keep unrelated working changes intact. Update README/CHANGELOG and installation
instructions when user-visible behavior changes. Include meaningful validation
and residual hardware limits in the handoff. Before a requested push, inspect
the staged file list for generated files, secrets, and private phone material.
The user repository is `git@github.com:Sasha123453/FlipPets.git`; this checkout
can use its local HTTPS rewrite when SSH is unavailable. Do not put credentials
in repository files or commands.

Native folded-wallpaper research is in `docs/folded-wallpaper-options.md`.
The actual wallpaper engine has outer lock target 8, but shell's filesystem
write-access checks fail despite 0777 directories. Themes' known video import
applies inner targets 1/2/3. Do not call it a working outer video import or modify
wallpaper type before a verified resource-copy and exact restore path exist.

The tiny editor accepted a donor-based JSON preview via `param_template_item_json`;
PAG animation/apply/rollback are not verified. Folded native wallpaper is deferred.
The user also deferred continuation after **any** main-screen shutdown (Power or
timeout) after the rootless power audit. An app-only launch button is not acceptable.
`cmd display power-off 0` left mainOFF/coverON while PowerManager remained Awake;
it is not secure sleep/AOD proof. Preserve native Power semantics, avoid repeated
wake/ON/brightness hacks, and consult `docs/independent-display-power.md`/`TODO.md`.

Xiaomi18Pro artwork is deferred to the next version by the user's request.
The resumable partial OTA and checkpoint are local/ignored. Only payload metadata
has been verified so far; the complete ZIP and selected partition hashes have
not. See `docs/donor18-resource-import.md`; do not import or claim new18Pro assets
in1.0. Preserve original catalogue IDs and require verified source hashes/MAML
before any later selective import.
