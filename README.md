# Flip Pets for Xiaomi MIX Flip

Rootless Android port of original Xiaomi 17 Pro rear-screen resources, adapted to
MIX Flip. A guarded Shizuku shell controller enables both physical displays while
the phone is open and unlocked. Folding, sleep or lock returns the stock cover
interface/AOD. No donor firmware is flashed.

## Native folded-screen priority

The default folded path remains Xiaomi's own cover interface, secure lock screen and
AOD. The next priority is optional animated cover-lock wallpaper through Xiaomi's
stock wallpaper editor/engine, so the native system handles folding and persistence.
Version0.8 does not implement that native export/apply path. See the
[folded wallpaper research](docs/folded-wallpaper-options.md) and
[donor-based roadmap](docs/cover-screen-research.md). Optional utility cards are a
secondary addition; stock folded widgets already provide many comparable functions.

## Version 0.8

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

## Project layout

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
Version0.8 requires a fresh170/68/15/15 run (268 checks) against its exact APK SHA;
those checks are still pending while the new APK is being built. Version0.7 passed
that full emulator set under its original SHA. Emulator helpers explicitly target
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
rolling back to3 and the old10second retry delay. **Version0.8 has not yet been
physically validated and is not being installed for this release.** The phone
remains on0.7;0.8 concludes after emulator checks. Its bounded readiness retry
is the proposed fix; fold
return/fade, real media controls, long stability and battery drain remain pending. Old CPU/PSS, wallpaper, reboot and hardware
results retain their original APK SHA; they are not re-labelled as 0.8.

After reboot, photos, appearance and favorites persist. Rootless Shizuku must be
started again, then the cover session re-enabled. The foreground session does not
remove that limitation or guarantee survival of every HyperOS restriction.

The port does not reproduce Xiaomi's proprietary AI dialog, AON camera gestures,
payments, cloud providers or complete Folme engine. [Research](docs/cover-screen-research.md)
distinguishes implemented additions from remaining donor features. Generated code
is MIT-licensed ([license](work/CODE-LICENSE.txt)); Xiaomi artwork/fonts retain
original ownership and are outside that license.