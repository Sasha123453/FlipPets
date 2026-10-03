Flip Pets 0.4 — source and resource bundle

Generated Java/Python/shell/PowerShell implementation: MIT, see CODE-LICENSE.txt.
Xiaomi artwork, fonts, MAML, PAG and MP4 assets retain their original ownership.
They were extracted for this user's local experiment; they are not covered by
the code's MIT license. Provenance is in work/research/portable-resource-provenance.json.

Runtime: Android >= 10 / API 29, target API 35; arm64-v8a and x86_64.
Renderer: Tencent libpag 4.5.98 standard Android AAR with ffavc software decoder.
Licenses of native dependencies are in work/app/assets/licenses.
Unmodified library source: https://github.com/Tencent/libpag/tree/v4.5.98
ffavc source: https://github.com/libpag/ffavc/tree/1.0.1
The app uses replaceable shared native libraries; no obfuscation or network code.

Build on this PC:
  python -X utf8 work/build_apk.py
Use the bundled Python path if python is not in PATH.
The JDK and Android SDK were downloaded into the original work/tools folder.
They are intentionally not duplicated in this source ZIP.
Required paths, relative to the bundle root:
  work/tools/jdk/jdk-17.0.20.1+1/bin/{java,javac,keytool}.exe
  work/tools/sdk/platforms/android-36/android.jar
  work/tools/sdk/build-tools/android-16/{aapt2,zipalign}.exe
  work/tools/sdk/build-tools/android-16/lib/{d8,apksigner}.jar
  work/tools/libpag/classes.jar and jni/{arm64-v8a,x86_64}/*.so (included)

No Gradle or online repository access is required once these tools exist.
Build script assembles resources, compiles Java, produces DEX, adds native libs,
aligns for 16 KiB pages, signs, verifies and writes outputs/FlipPets.apk.
The signing key is kept only in the original work/local-signing.p12.
It is excluded from this ZIP. A fresh build in another folder creates a new key;
that APK cannot replace the original APK without uninstalling it first.

Checks:
  javac -d work/tests/classes work/app/src/org/flippets/app/PetState.java work/tests/PetStateTest.java
  java -cp work/tests/classes org.flippets.app.PetStateTest
  python work/check_native.py
  python work/tests/run_controller_tests.py
The last test explicitly targets emulator-5554, asserts ro.kernel.qemu=1, and
uses fixture functions for phone state/display commands. It does not test hardware.
Full asset QA:
  adb -s emulator-5554 shell am start -n org.flippets.app/.PetActivity --ez qa true
  adb -s emulator-5554 pull /sdcard/Android/data/org.flippets.app/files/qa.json
Wait for this file to be written after the complete run. Do not reuse an old result.
PAG QA renders two different timeline points offscreen; MP4 QA uses Android's
MediaMetadataRetriever. UI, wallpaper and dual-display checks are separate.

Resource preparation (optional; APK assets already included):
Unpack Original-Xiaomi-Resources.zip into work/original-resources and place
its pandora-subscreencenter.apk in work/jars; run python work/prepare_catalog.py.
The archive has the original MRC/MRM and manifests, including presets that
need proprietary services and are not exposed in this app.

New offline compositions:
  python work/inspect_compositions.py
  python work/prepare_compositions.py
Run prepare_catalog.py first. Raw MRC inputs are needed only for regeneration.
Five original Xiaomi fonts are already included in work/app/assets/fonts;
font-provenance.json records their product.img paths and SHA-256 hashes.
CompositionRenderer is a selective Canvas adaptation, not a complete MAML interpreter.
Cloud providers, image-generation services and Folme are not bundled.
Compiled Xiaomi nine-patch PNGs are drawn by Android NinePatch.

Additional tests:
  javac -d work/tests/classes work/app/src/org/flippets/app/StepLedger.java work/tests/StepLedgerTest.java work/app/src/org/flippets/app/SceneGeometry.java work/tests/SceneGeometryTest.java
  java -cp work/tests/classes StepLedgerTest
  java -cp work/tests/classes SceneGeometryTest
  adb -s emulator-5554 shell am force-stop org.flippets.app
  adb -s emulator-5554 shell am start -n org.flippets.app/.PetActivity --ez qaComposition true --ez qaSwitch true
  adb -s emulator-5554 pull /sdcard/Android/data/org.flippets.app/files/composition-qa.json
  adb -s emulator-5554 pull /sdcard/Android/data/org.flippets.app/files/ui-switch-qa.json
Wait for fresh outputs. QA extras are gated to ranchu/goldfish emulators.
The scene tests cover all original image decoding, native fonts/nine-patches,
three device aspect ratios, spring/layout changes, text layouts and private photo import.
Source ZIP excludes the signing key, firmware ZIPs, portable SDK and legacy root module.

Rootless Shizuku bridge:
API/provider/aidl/shared 13.1.5 and androidx.annotation 1.3.0 jars are included
under work/tools/shizuku. The MIT license is in app/assets/licenses.
Official sources: https://github.com/RikkaApps/Shizuku-API
ControllerService only allows fixed operations from this application's UID,
requires shell UID 2000 and refuses a root backend. Provider is protected.
Its script uses stock system commands with a ruyi firmware/model guard.
On the emulator, a real Shizuku shell UserService was bound, UID 2000 verified,
and the non-ruyi model was refused. Device-state behavior uses test fixtures.
Run python -X utf8 work/tests/run_supervisor_tests.py for 11 supervisor cases.
Run python -X utf8 work/tests/profile_resources.py 12 for CPU/PSS measurements.
Both are explicitly restricted to emulator-5554, never a physical device.

Persistence is SharedPreferences/private image files, selected by stable IDs.
Shizuku and the temporary display controller need re-enabling after reboot.
The app contains no boot receiver, foreground wakelock, network permission,
root module, binary patch, vendor-service replacement or firmware flashing.

The shell UserService is removed after every RPC to avoid keeping a second
Android Java process resident. The nohup shell supervisor survives removal.
Repeated commands are serialized and binding has a 25-second timeout.

Diagnostics: AppLog stores rare events in two bounded 64KiB private files,
with duplicate suppression. A separate shell status snapshot is capped at
32KiB. Logcat collection filters this application's UID and is executed only
on explicit export, with a 3-second timeout and 32KiB output limit. There is
no READ_LOGS permission or automatic telemetry. A Java uncaught exception
handler records an event then delegates to Android's original handler.
Native crashes are not guaranteed to be captured in the private journal.
The report is exported through ACTION_CREATE_DOCUMENT, surviving rotation.
