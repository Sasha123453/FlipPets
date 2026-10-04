Flip Pets 0.8 — source/build bundle

Generated Java/Python/shell/PowerShell code: MIT, see work/CODE-LICENSE.txt.
Xiaomi artwork/fonts/MAML/PAG/MP4 retain their original ownership; the code license
does not cover them. Provenance: work/research/portable-resource-provenance.json.

Android >=10/API29; target API35; arm64-v8a and x86_64. Tencent libpag4.5.98
standard Android AAR and ffavc1.0.1; dependency notices in app/assets/licenses.
Sources: https://github.com/Tencent/libpag/tree/v4.5.98
         https://github.com/libpag/ffavc/tree/1.0.1
         https://github.com/RikkaApps/Shizuku-API
No obfuscation, network permission, root module or firmware flashing.

Build from project root:
  python -X utf8 work/build_apk.py
Portable dependencies expected relative to project root:
  work/tools/jdk/jdk-17.0.20.1+1/bin/{java,javac,keytool}.exe
  work/tools/sdk/platforms/android-36/android.jar
  work/tools/sdk/build-tools/android-16/{aapt2,zipalign}.exe
  work/tools/sdk/build-tools/android-16/lib/{d8,apksigner}.jar
  work/tools/libpag/classes.jar and jni/{arm64-v8a,x86_64}/*.so
  work/tools/shizuku/{api,provider,aidl,shared,annotation}.jar
SDK/JDK and firmware images are not duplicated in the source ZIP. Libpag/Shizuku
runtime dependency files are included. No Gradle or network access is required
once the local tools exist. Git clones require git lfs pull for binary resources.

Build compiles resources/Java/DEX, adds native libs, aligns/signs/verifies APK.
Original signing key: work/local-signing.p12, deliberately excluded from bundles.
A fresh build elsewhere creates a different key and cannot update the installed
original without uninstalling it. Private photos/settings can be lost on uninstall.

Current runtime QA (emulator only; execute separately, wait for each fresh file):
  adb -s emulator-5554 shell am start -n org.flippets.app/.PetActivity --ez qa true
    -> qa.json, 170 clip checks
  adb -s emulator-5554 shell am start -n org.flippets.app/.PetActivity --ez qaComposition true
    -> composition-qa.json, 68 checks
  adb -s emulator-5554 shell am start -n org.flippets.app/.PetActivity --ez qaSwitch true
    -> ui-switch-qa.json, 15 transitions
  adb -s emulator-5554 shell am start -n org.flippets.app/.PetActivity --ez qaUtilities true
    -> utility-qa.json, 15 checks with an enabled notification listener
  python -X utf8 work/tests/run_pet_layout_qa.py
    -> pet-layout-qa.json, 19 real dialog controls/rendering/restoration checks
Files: /sdcard/Android/data/org.flippets.app/files/. Pull each named file explicitly.
QA extras are gated to ranchu/goldfish. Utility QA uses its own synthetic MediaSession
without audio/network, exercises real callbacks, and restores utility/timer/selection
preferences. Missing notification-listener discovery is a failure, not mocked success.

Packaging (run only after all fresh outputs exist):
  python -X utf8 work/package_release.py --qa-dir work/qa-v03/device-files
  optional: --profile work/qa-v03/resource-profile-v100.json
  optional: --current-evidence PATH_TO_SHA_BOUND_JSON [MORE_JSON...]
This replaces report.html, Verification.json/zip and source/resources ZIPs. It checks
APK version1.0, exact QA SHA/count/failures, APK asset equality, composition image
hashes, signature, zipalign and native ELF page alignment. Historical hardware,
resource and lifecycle data are labelled with their original SHA, not current evidence.
Only explicit public evidence/source files are bundled; no raw phone dumps or keys.

Pure logic tests can be compiled into ignored work/tests/classes:
  PetStateTest, PlaybackPolicyTest, StepLedgerTest, SceneGeometryTest,
  TimerStateTest, HingeOpacityTest (where present).
  python -X utf8 work/check_native.py
  python -X utf8 work/tests/run_controller_tests.py
  python -X utf8 work/tests/run_supervisor_tests.py
Controller/supervisor tests use stubbed device signals on emulator-5554, not physical
fold/display hardware. SHA-bound renderer QA does not prove HyperOS behavior.

Resource regeneration is optional; APK assets already exist:
  python -X utf8 work/prepare_catalog.py
  python -X utf8 work/inspect_compositions.py
  python -X utf8 work/prepare_compositions.py
Inputs: work/original-resources and work/jars/pandora-subscreencenter.apk.
CompositionRenderer is a selective Canvas adaptation, not a complete MAML interpreter.
Cloud/Folme/AON services are not bundled. Original font paths/hashes are recorded.

Native folded-screen priority:
Preserve Xiaomi's secure cover lock screen/AOD by default. Optional native animated
cover-lock wallpaper through stock Xiaomi editor/engine is the next stage, not an
implemented0.8 export/apply feature. See docs/folded-wallpaper-options.md and donor
roadmap in docs/cover-screen-research.md. Utility cards are secondary, default off.

0.8 behavior:
Material You settings/gallery; optional battery/media/visual-timer compact overlay.
The timer has no audible/exact background alarm. CoverGuard is a user-enabled
specialUse foreground service with quiet notification and Stop action; cover activity
uses a separate task. It does not hold a wake lock or render while the panel is hidden.
Closing settings is separated from the cover session. Sensor-based hinge fade uses
continuous degrees only when an angle sensor exists; discrete flip states are not angles.

Rootless Shizuku runs at shell UID2000 and needs restarting after a device reboot;
then re-enable the cover session. Appearance/favorites/private photos persist. No boot
receiver makes a claim of automatic rootless two-panel startup. HyperOS force-stop,
battery restrictions and foreground-service policies can still stop the session.
The temporary Shizuku Java UserService is removed after each fixed RPC.

0.5 physical baseline: two panels/fold return/hardware decoder/photo persistence were
verified on MIX Flip EEA OS3.0.303.0.WNIEUXM. Historical0.7 phone validation
confirmed installed APK hash, Shizuku UID2000, state5/two panels, foreground service
and real hinge-angle sensor registration (5 observed checks). The user confirmed
Main removal retained the cover session, but fold recovery could take20seconds
(firststate5 rollback to3 plus old10second backoff). Version0.8 adds bounded
readiness/startup retry; its fresh268-check emulator run is pending. Version0.8
is not being installed/tested on the phone for this release; the phone stays on0.7. Utility controls, long stability and battery drain are unconfirmed.

Diagnostics: rare events in bounded private AppLog files, duplicate suppression,
bounded controller snapshot, and own-UID logcat only on explicit export. No READ_LOGS
permission or telemetry; no media titles are explicitly written to AppLog. Export uses
ACTION_CREATE_DOCUMENT. Native crashes are not guaranteed in the private journal.
