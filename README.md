# Flip Pets for Xiaomi MIX Flip

Rootless Android port of original Xiaomi 17/18 Pro rear-screen resources, adapted to
MIX Flip. A guarded Shizuku shell controller enables both physical displays while
the phone is open and unlocked. Folding, sleep or lock returns the stock cover
interface/AOD. No donor firmware is flashed.

The reviewed development controller now keeps root consent in private persistent
storage, separates root and Shizuku runtime files, and holds a shared lock for the
whole session. Stop one backend before starting the other. Root observes module
disable/remove while running. Manual Start also requires an acknowledged lifecycle
watcher. The optional module remains experimental pending assembled phone testing;
see [setup and migration](docs/kernel-su-module.md).

## Native folded-screen priority

The default folded path remains Xiaomi's own cover interface, secure lock screen and
AOD. The next priority is optional animated cover-lock wallpaper through Xiaomi's
stock wallpaper editor/engine, so the native system handles folding and persistence.
Version1.1 does not implement that native export/apply path. The native tiny editor
accepted a donor-based preview, but animation and safe apply/restore remain unverified;
this folded-lock work is deferred at the user's request. See the
[folded wallpaper research](docs/folded-wallpaper-options.md) and
[donor-based roadmap](docs/cover-screen-research.md). Optional utility cards are a
secondary addition; stock folded widgets already provide many comparable functions.

## Version 1.1

The released1.1 APK (`1d7d6181…`) passed343 emulator checks and6 virtual-cover lifecycle checks.
Full-screen mini-app captures were visually reviewed. Physical MIX Flip and
KernelSU verification remain pending. Subsequent controller development APKs have
separate scoped evidence and do not inherit those full-release results. Each
reviewed development milestone is published as a GitHub prerelease with matching
source commit, APK, experimental module and hashes. Physical testing waits for the
assembled build; see [HANDOFF](HANDOFF.md) for the current development identity.

- Three additions from verified Xiaomi18Pro product resources: **Butterfly carp ·18Pro** (four scenes), **Vortex ·animated background** and **Card effect ·18Pro** (one-shot manual preview). The existing30 entries and IDs stay unchanged:33 entries,176 clip paths,148 unique media SHA256.
- Carp uses the donor MAML progress thresholds,500ms fade-out,100ms delay after actual scene load and300ms fade-in. Automatic scene selection does not write preferences; a tap manually selects another scene. With/without-clock placement controls also apply to this fish.29 original clock glyphs are retained. This is a Java adaptation, not the Xiaomi Folme/MAML engine.
- Vortex fills the cover while preserving video proportions. Its native analogue clock/date/battery layers are not included. The card animation previews the SmartAssistantPanel transition; it does not provide NFC, payment or AI backend functionality.
- The Chinese18Pro Themes APK has a separate online rear-screen shop. Flip Pets currently offers bundled resources/private photos; online theme download/import remains unimplemented. See [shop research](docs/online-rearscreen-themes.md).
- Exact source archive/member hashes, selected partition hashes and decoded-frame provenance are in [donor18 research](docs/donor18-resource-import.md). The complete OTA ZIP was not downloaded/verified; the partial file must not be flashed.
- New scenes and their physical camera clearance require a MIX Flip check. Folded lock/AOD and ordinary Power behavior remain native and unchanged.

## Version 1.0

- Each pet has explicit **With clock / Without clock** variants, selected with
  the **Вариант и положение** button beside the preview. With clock keeps the exact
  default size and position from0.9.1. Without clock enlarges the pet on the right,
  preserving proportions and using fixed face-placement guides; round characters
  reach the available width before they can fill the panel height.
- Optional scale and horizontal/vertical position are saved separately per pet
  and variant. The dialog reuses the existing virtual-cover renderer. Changes
  affect only that preview until **Apply**; **Cancel** discards them. **Automatic**
  resets the selected variant's manual offsets and scale, saved on Apply.
  Camera circles are schematic: manually adjusted poses still need a phone check.
- Without clock hides only the app's clock, skips clock-digit loading and minute
  redraws. Clocks already encoded inside a video remain. Photos, compositions and
  Flowing glitter keep their existing layouts. Ordinary PAG live wallpaper shares
  saved placement; its direct-Surface MP4 path still uses the earlier placement.

Retained from0.9.1:

- Cover pets use a fixed subject focus per family and uniform bottom-right placement.
  Most are10% larger than intermediate0.9; Coco is enlarged further to fill the
  opaque scene across the panel. Charlie is framed by
  the bird rather than his wide branches. The rectangular camera-column crop is
  removed, so lower scenery remains continuous; the screen edges can still crop
  wide effects. Opaque scenery backgrounds share the animation's source transform.
  The48px scenery-edge feather is currently specific to the activity renderer;
  the ordinary wallpaper PAG renderer uses the same geometry without that mask.
- Charlie's crest touches the edge inside the donor video composition during some
  intermediate frames. Enlarging its PAG container cannot recover those pixels;
  the original completed frame has the full crest. Playback still ends at1.0.
- Settings preview renders a virtual1208×1392 cover at520dpi, then scales it to the
  card. It uses the same placement as the cover activity; camera circles are schematic.
  An optional34–55% left margin lets the user increase camera clearance.
- Opaque MP4 avatars still show their source rectangle; natural background blending
  for them remains pending. Photos and clock compositions retain their layouts. These changes adapt
  donor art to MIX Flip; they are not a verified exact copy of17Pro placement.
- Showing pets after **any** main-screen shutdown, including Power and timeout,
  is deferred. A short panel-off experiment leaves PowerManager Awake and does not
  establish secure lock/sleep behavior. The default still returns Xiaomi's own AOD.
  See [power policy research](docs/independent-display-power.md) and [TODO](TODO.md).

Retained from0.8:

- Material You settings/gallery: system tonal colors, light/dark themes, search,
  categories, favorites and private photo controls.
- Optional compact utility overlay: battery/charging/temperature, published media
  session controls, or a visual 25-minute focus timer/stopwatch. Off by default;
  one overlay at a time. These are additions to the port, not copied 17 Pro UI.
- The cover activity has its own task. A user-enabled foreground session with a
  quiet notification and Stop action separates the cover from the settings task.
  Closing settings no longer intentionally ends the session. No wake lock or
  background animation is added; HyperOS force-stop/kill behavior is still a limit.
- Bounded startup retries wait for the cover display to become ready after unfold.
  Steady-state polling remains2seconds; this addresses observed state5 rollback
  followed by the old10second restart backoff. It is not a guarantee of instant recovery.
- Optional fold fade uses a hinge-angle sensor when exposed, otherwise Xiaomi's
  discrete flip-state sensor. The latter is a transition between states, not a
  reconstructed continuous angle. If neither exists, stock transitions remain.

Battery/media changes use events; only a visible running timer redraws once per
second. The visual timer has no sound or exact background alarm. Music controls
require the existing notification-listener access and actions supported by the
player. Imported photos remain private copies, independent of the source image.

## Optional Xiaomi cards and root controller

The gallery separates **17 Pro**, **18 Pro**, **Свои** (photo/text templates) and
**Архив Xiaomi** (presets without verified donor-model attribution). Type filters,
search and favorites work inside the selected collection. The 18 Pro collection
also contains the three mini-app cards; opening one shows a preview before Apply.

Optional [mini-apps](docs/mini-apps.md): choose Focus, Water or Words in Main and
press **На внешний экран**. Browsing/Cancel leaves the cover unchanged. These are
three original public Xiaomi Canvas examples, with their Chinese UI,8-glass
water counter, English/Chinese vocabulary and25/5-minute Pomodoro retained. The
offline host blocks networking/native bridges and fills the cover using the original
responsive Canvas dimensions, with proportional artwork and controls. The bundled
HTML bytes stay unchanged. A [firmware audit](docs/donor18-mini-app-runtime.md)
confirmed a separate native JsCanvas/QuickJS engine and six built-in MAML cards;
the three public examples were not found in those packages.
Choose **Вернуть питомца** or a gallery item to return.
They replace the pet only in our open/unlocked cover activity, not live wallpaper
or Xiaomi's folded lockscreen/AOD. The old utility overlay remains independent.

An [experimental KernelSU module](docs/kernel-su-module.md) is prepared for a
future rooted MIX Flip. It is an alternative supervisor, not verified independent
rear-screen power. The development controller now acknowledges child startup;
unattended boot resume never clears Stop and waits up to ten minutes for unlocked
app storage. The root wrapper additionally verifies exact process receipts and
serializes module actions, preserving a newer disable request during startup.
Root now uses private durable state and a session-lifetime lock shared with Shizuku;
physical root verification remains pending. The [photo-pet generation audit](docs/photo-pet-generation.md)
documents the donor image/video service chain; a working generator is still required.

## Project layout

- `HANDOFF.md`: latest implementation state, exact artifact hashes, verification
  scope and outstanding work for the next contributor.
- `work/app`: Android source, manifest, original assets and dependency notices.
- `work/tests`: renderer/controller/profile helpers and pure logic tests.
- `work/research`: original MAML, provenance, firmware layouts and coverage.
- `work/original-resources`, `work/jars`: original resource-preparation inputs.
- `docs`: rootless feature research and the donor-based roadmap.
- `outputs`: APK, installation instructions/scripts and generated verification.

Binary artwork and runtime libraries use Git LFS. Run `git lfs pull` after cloning.
Firmware images, SDK/JDK, emulator, generated APK/ZIPs, raw phone dumps and signing
keys stay local and are excluded from Git.

## Build and verification

See [source/build instructions](work/SOURCE-README.txt). With local dependencies:

```powershell
python -X utf8 work/build_apk.py
python -X utf8 work/check_native.py
python -X utf8 work/package_release.py --qa-dir work/qa-v03/device-files
```

Packaging refuses missing, failed, incorrectly counted or stale SHA-bound results.
Version1.1 requires fresh176/68/15/15 renderer/UI/utility results,19 layout-dialog
and23 donor18 runtime checks,27 mini-app checks against its exact APK SHA, plus virtual-cover lifecycle
checks. Run these suites separately, while no other emulator UI QA is running:

```powershell
python -X utf8 work/tests/run_pet_layout_qa.py
python -X utf8 work/tests/run_donor18_qa.py
```

The runner explicitly guards `emulator-5554`, removes its old result, installs the
current APK, tests real dialog controls, and pulls `pet-layout-qa.json`. It rejects
an incorrect SHA, missing checks, failures and skips. Source geometry tests now
pass1,106 assertions; this does not prove physical camera clearance.
The final1.0 APK passed287 renderer/UI/utility/layout checks and6 virtual-cover
lifecycle checks. Both modes persisted after force-stop/relaunch through real UI.
Five screenshots were inspected. Version1.0 was installed as an update on MIX Flip;
version/code and installed APK SHA were verified. This is installation evidence only.
Current physical camera/hinge/battery validation
remains pending; older phone reports do not validate the new modes.

Historical0.9.1 passed268 render/UI/utility checks,582 geometry assertions and
6 virtual-cover lifecycle checks. Geometry uses offline original-asset sampling.
Its phone evidence is limited to both visible activities,
foreground service, Charlie geometry and short process CPU/PSS samples. New physical
fold/reboot and battery stability remain unverified.
Version0.8 passed the full emulator set under its original SHA. Emulator helpers explicitly target
`emulator-5554`; hardware
commands must name the phone serial. Standard Android emulation is not HyperOS.

The [generated Verification.json](outputs/Verification.json) separates current
APK evidence from historical data. Physical version 0.5 on MIX Flip EEA HyperOS
3.0.303 confirmed two screens, fold return, hardware decoding and private photo
import surviving process restart/source deletion. **Version0.7 had limited physical validation:** installed APK hash, Shizuku UID2000,
simultaneous panels/state5, foreground service and real hinge-angle sensor
registration (5 observed checks). The user confirmed that removing Main from
Recents retained the cover session. Fold recovery was intermittent: sometimes
immediate, sometimes about20seconds; a trace showed the first state5 request
rolling back to3 and the old10second retry delay. Version0.8's readiness retry
passed emulator checks; intermediate0.9 was installed for visual feedback and
its rectangular scene crop was rejected. Current phone observations, when included,
are limited to the installed APK and their stated scope. Long stability, real
media controls, reboot and battery drain remain pending. Historical results retain
their original APK SHA.

After reboot, photos, appearance and favorites persist. Rootless Shizuku must be
started again, then the cover session re-enabled. The foreground session does not
remove that limitation or guarantee survival of every HyperOS restriction.

The port does not reproduce Xiaomi's proprietary AI dialog, AON camera gestures,
payments, cloud providers or complete Folme engine. [Research](docs/cover-screen-research.md)
distinguishes implemented additions from remaining donor features. Generated code
is MIT-licensed ([license](work/CODE-LICENSE.txt)); Xiaomi artwork/fonts retain
original ownership and are outside that license.
