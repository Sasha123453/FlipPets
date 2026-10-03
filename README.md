# Flip Pets for Xiaomi MIX Flip

Rootless Android application adapting original Xiaomi 17 Pro rear-screen resources
to MIX Flip. Shizuku runs a guarded shell controller: while fully open and unlocked,
both physical screens work; folding, sleep or lock returns the stock cover interface.

## Project layout

- `work/app`: Android source, manifest, original assets and dependency licenses.
- `work/tests`: renderer, lifecycle, controller and resource-profile test helpers.
- `work/research`: extracted original MAML, resource provenance and device layouts.
- `work/original-resources`, `work/jars`: original inputs for resource preparation.
- `work/*.py`: extraction, preparation, offline build and packaging scripts.
- `outputs`: installation scripts, firmware download manifest and verification reports.

Binary resources and bundled runtime libraries use Git LFS. Install Git LFS before
cloning; use `git lfs pull` to retrieve them. Full firmware images, SDK/JDK,
emulator, generated APK/ZIP packages, private phone dumps and the signing key stay
local and are excluded from Git. No remote is configured yet.

## Build and tests

See [source/build instructions](work/SOURCE-README.txt) for portable tool paths.
With dependencies available locally:

```powershell
python -X utf8 work/build_apk.py
python -X utf8 work/check_native.py
```

Emulator helpers explicitly target `emulator-5554`. Hardware commands must name
the phone serial explicitly. Never flash the donor firmware on MIX Flip.

## Validation status

The 0.4 baseline passed 170 clip, 68 composition and 15 UI-transition checks on
standard Android 16, plus emulator lifecycle/Shizuku tests. These are not HyperOS
emulation. On the physical MIX Flip (EEA HyperOS 3.0.303), simultaneous main/cover
operation and returning after a fold were observed. Position drift after folding
was addressed in 0.5; the user reported a correct return after folding, and logged
layout coordinates matched. Hardware decoding was observed. Version 0.5 repeated
all 253 asset/composition/UI checks; finite playback and touch replay were tested.
On the phone, photo import survived process restart and deleting the source test
image. See `work/qa-v03/hardware-validation.json` for measurements and limitations.
Extended stability and battery measurements remain unverified.

Shizuku and the controller need restarting after a phone reboot. Appearance,
favorites and imported pictures persist. The port does not reproduce proprietary
Xiaomi AI, payment, cloud weather or AON camera-gesture services.

Generated implementation is MIT-licensed, see [code license](work/CODE-LICENSE.txt).
Xiaomi resources retain their original ownership; the code license does not cover
them. Source/provenance and dependency notices are included in the project.
