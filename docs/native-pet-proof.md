# One native pet: prepared resources and physical proof gates

The first resource is Charlie (`bird-pandora`, `pag_0.pag`), unchanged from the
verified 17 Pro container. The inspected 18 Pro copy is byte-identical. This is
resource preparation for MIX Flip's existing tiny-keyguard host. It does not add
an installer or enable native Apply in Flip Pets.

## Reproduce the resource bundle

Run `python -X utf8 work/tests/prepare_native_pet.py` with the explicitly guarded
`emulator-5554` available and the current APK built. Python Pillow is required for
independent PNG pixel verification. The script verifies the
original container and member hashes, extracts the current APK's x86_64 renderer
libraries into isolated emulator staging, and decodes eight samples at the
original 976×596 resolution. It does not launch an Activity, read app preferences,
call an OEM service or change native state. Staging is removed afterwards.

`outputs/FlipPets-native-Charlie-proof.zip` contains the original PAG, a decoded
first-frame poster, eight sampled PNGs and a manifest. The PNG pixels are checked
against the decoder's RGBA hashes. No resizing, thumbnail substitution, padding
or PAG modification is performed. The manifest binds the renderer APK, original
container/member, poster, samples and probe source. Xiaomi artwork remains outside
the MIT code license.

The first/near-end alpha bounds and sampled union describe source pixels. They
are candidate geometry data, not validated native placement. Eight samples do not
establish the envelope of every frame or physical camera clearance. Charlie's
crest is still clipped in intermediate source frames.

## What the inherited OEM path says

The preserved EEA AOD APK is hash-bound in
`work/research/native-pet-preparation-evidence.json`. Its editor initializes the
pet view with autoplay requested. `PetsPagView.init` forwards that request into
`PagViewBase.mIsAutoPlay`. Filesystem input uses asynchronous PAG loading; the
load callback reaches `AiPetsPagView.loadFileComplete`, which builds a 1208×1392
composition. The inherited composition setup uses one repeat and calls `play()`
only on the autoplay branch after a non-null load. Replay either plays from frame
zero or flushes/pauses there, depending on that flag. Relevant DEX instruction
graphs were checked alongside decompiled methods; the whole decompilation is not
claimed error-free or recompilable.

This establishes a source path capable of requesting motion. It does not prove
that the historical accepted preview loaded our PAG, displayed animated frames,
or will play on the folded lockscreen. Poster visibility and our emulator decoder
cannot satisfy that gate. The native host translates the donor; it does not use
our app's `CoverGeometry` scaling. First/last axes, optional explicit translation,
poster dimensions and the host's even rotations require actual comparison.

## Read-only device identity, when phone testing resumes

`python -X utf8 work/tests/capture_native_capabilities.py --serial <explicit-serial>`
refuses implicit targets, emulators, other devices and builds other than the
observed `ruyi` EEA `OS3.0.303.0.WNIEUXM`. It reads and hashes the installed FlipHome,
AOD and framework artifacts, pulls them into ignored `work/phone-qa`, and checks
the local bytes against the on-device hashes. Updated `/data/app/~~…` APK paths
are supported. It does not grant admission, change settings, launch the native
editor, install root or Apply a template. The current source work did not run it
against a phone. A firmware update requires a newly inspected profile.

Inspect those exact artifacts before implementing a package admission transaction.
Compare them to the Global audit, trace the EEA policy reader and verify policy
readback, list refresh, metadata/property types and restoration. The documented
`clear` command alone cannot restore an unknown prior policy exactly.

## Motion and restoration workflow before Apply

1. Verify the explicit physical target and relevant build/APK/JAR hashes. Keep
   raw captures and identifiers private. Inventory the selected template, relevant
   history entries and all referenced files, with hashes, owners, modes and SELinux
   labels. Establish readable, restorable native state before changing it.
2. Stage only the validated bundle under a unique identity. Test native filesystem
   read access and the OEM writer's copy semantics. Record a denial precisely;
   do not broaden permissions or assume root is necessary. Bind any later helper
   to fixed validated inputs and an exact supported build.
3. Open preview only after phone testing is authorized. Capture several distinct
   frames of the actual OEM-rendered pet, with timing and a native-window identity.
   Compare the pet region to the static poster and source samples. A progress
   property, app-rendered sequence or moving editor background is insufficient.
   Verify both rotations, placement and camera clearance separately.
4. Define the native installation/restore transaction before Apply. Its private
   receipt must bind the before selection, relevant history identity/version and
   referenced file metadata, plus exactly our inserted history IDs and created
   resources. Preserve the prior bytes needed for restoration. Never back up or
   overwrite a live global settings database as a shortcut.
5. Prove the OEM transaction and exact restore under controlled testing, including
   partial copy, history insertion, selection update and interruption. Read back
   each operation. Restore only if the current selection/history still match our
   recorded after-state; a later manual Xiaomi choice must survive. Delete an
   owned resource only after checking all native references. Unknown state or an
   unverified restore API stops this branch rather than guessing.
6. Only after those gates, implement the user-facing native install/Restore flow.
   Native Restore remains distinct from the open-session Stop action. Validate
   folded lockscreen motion, stock screen-off/AOD limits, unlock/fold transitions,
   reboot and process death on the actual phone. Rooted staging additionally needs
   real UID/SELinux evidence. No current bundle claims these outcomes.

Current source deliverables finish preparation and the inherited playback trace.
Native admission, motion, Apply and exact restoration remain physical evidence
gates. Generation is deferred; small MAML widget hooks remain optional.
