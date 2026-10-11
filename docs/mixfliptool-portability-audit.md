# MixFlipTool: useful contracts and work possible before phone testing

11 October 2026. This is a research addendum for the implementing agent.
It does not change Flip Pets code or authorize a device mutation. Another agent
was editing the app during this audit; its working files were left untouched.

## Recommendation

Use MixFlipTool as a reference for native app admission, not as a subsystem to
port. The strongest new lead is a **manifest-only cover admission declaration**,
now corroborated by the local MIX Flip Global framework. Prioritize that before
building an automatic root admission restorer or requiring a privileged helper.

The phone is unavailable for proper testing, but the agent can still implement
and verify the manifest contract, routing/layout fixes, diagnostics and a narrowly
scoped optional setup abstraction. Label these source-verified candidates until
the actual EEA phone confirms admission, layout and continuity.

## Sources inspected

- [MixFlipTool](https://github.com/parallelcc/MixFlipTool), pinned commit
  `79e84a7427e637494a5e1e3e35b9781fcdf3ca58`, dated 24 October 2024.
  App version 1.1.2, min SDK 33, target SDK 34. Do not infer current HyperOS 3 EEA
  compatibility from this older target or its README.
- Its MainActivity, AppScaleManager, AndroidManifest, build configuration and
  license were read locally. No upstream APK/build script was run.
- Existing Global `ruyi` firmware `OS3.0.303.0.WNIMIXM` supplied
  `miui-appcompat.jar`, `miui-appcompat.appcontinuity.jar` and the previously
  verified `miui-services.jar`. This is **not** the actual EEA framework.
- Hashes and exact source anchors:
  [mixfliptool-portability-audit.json](../work/research/mixfliptool-portability-audit.json).
  Raw source/decompilation remains in ignored `work/folded-research/`.

## 1. Correct manifest property: highest-value finding

MixFlipTool declares an integer Android `property`, not `meta-data`:

```xml
<property android:name="miui.continuity.policy" android:value="5" />
```

[Upstream manifest, lines 41–42](https://github.com/parallelcc/MixFlipTool/blob/79e84a7427e637494a5e1e3e35b9781fcdf3ca58/app/src/main/AndroidManifest.xml#L41).

This is now more than an example copied from another app. In the extracted Global
framework, `ApplicationCompatManager.getPropertyIntByApplication` and
`getPropertyIntByActivity` call `PackageManager.getProperty(...).getInteger()`.
Package/activity scanning puts value-5 entries into the corresponding allow-start
sets. `ContinuityManagerService` includes those sets in the lists supplied to
FlipHome. `InterceptActivityController.isInterceptListForProperty` interprets 5
as allowed and 4 as intercepted, for both activity and application scopes.

Explicit local command overrides are checked before that property branch. There
are additional policy and launch paths; this is not a guarantee every launch will
succeed. Nevertheless, it is strong evidence for a **potentially app-only route**
that does not need reapplying a temporary shell allowlist after reboot.

Instructions for the agent:

1. Compare the current working manifest with this contract; do not rely on the
   old `PetActivity` metadata entry from reviewed commit `c548bc8`.
2. Evaluate activity-scoped integer properties on the ordinary launcher entry
   and card destination first. Main must be eligible for FlipHome enumeration;
   the internal card destination must also satisfy its launch checks. The upstream
   example uses application scope, which is broader than necessary for us.
3. Inspect the compiled manifest with `aapt2`, and verify `PackageManager` reads
   integer 5 in emulator QA. This verifies encoding/scope, not Xiaomi behavior.
4. Keep admission, continuity/resizing, full-screen layout and widget-strip
   visibility as separate features. This property does not establish the other
   three, nor repair the previously identified compact-window routing problem.
5. Preserve the opt-in routing switch and original controlled-pet policy. No
   device-state request, root permission or native Apply is needed for this
   source-level experiment.

## 2. DUMP permission: an optional non-root setup route

The upstream MainActivity first checks whether its own app has `DUMP`. If absent,
it uses Shizuku's package-manager Binder to grant that permission. With DUMP
already present, it skips the Shizuku permission path and directly invokes the
window Binder's `dump` method with `-setForceDisplayCompatMode` and `allowstart`.
This is not a root daemon or screen-rendering service.

[Upstream permission and invocation path](https://github.com/parallelcc/MixFlipTool/blob/79e84a7427e637494a5e1e3e35b9781fcdf3ca58/app/src/main/java/com/parallelc/mixfliptool/MainActivity.kt#L41).

The useful distinction is **persistent app permission versus temporary device
policy**. Upstream describes one-time permission setup, but its allowstart
configuration needs reapplying after reboot. It contains no boot receiver for
automatic reapplication. Thus this suggests a user-triggered non-root setup
button that may work without an active Shizuku session after permission setup;
it does not prove unattended boot recovery on our firmware.

For Flip Pets, prefer the manifest route first, then the existing authenticated
Shizuku service for a fixed own-package operation if necessary. Consider direct
DUMP as an optional convenience only after checking exact permission/service
behavior. Do not copy the upstream hidden-API bypass dependency simply to gain
an API we can already reach through our shell service.

The upstream enumerates every installed package and sends a colon-separated
allowstart list. We need only `org.flippets.app`: no all-package grant, installed
app inventory permissions, or generic shell/Binder command interface. The current
StopCover receiver requiring senders to hold DUMP is not itself a declaration
that Flip Pets holds DUMP; these are different manifest concepts.

## 3. Scaling is separate, and should stay deferred

`configAppScale()` calls the distinct Binder service `MiuiSizeCompat`. Its sequence
reloads rules and sets per-package enable, scale and activity-rule fields. Its
first-run preferences include changes for Contacts, Calendar, Messages, Recorder,
Calculator and Gallery. Those changes are unrelated to our card renderer.

[Upstream scaling calls](https://github.com/parallelcc/MixFlipTool/blob/79e84a7427e637494a5e1e3e35b9781fcdf3ca58/app/src/main/java/com/parallelc/mixfliptool/MainActivity.kt#L97),
[default package settings](https://github.com/parallelcc/MixFlipTool/blob/79e84a7427e637494a5e1e3e35b9781fcdf3ca58/app/src/main/java/com/parallelc/mixfliptool/AppScaleManager.kt#L58).

The locally inspected Global `MiuiSizeCompatService` still recognizes
`dump-rule`, `dumpAll`, `update-rule` and `reload-rule`. This supplies a useful
read-only diagnostic lead if scaling proves problematic later. It does not
establish that forcing scale is necessary for our measured Canvas layout, that
every invocation is permitted from our UID, or that these settings are a
full-screen/camera-clearance solution.

Do not reproduce global rule reload, stock-app defaults or
`activityRule::null` automatically. Start with the normal Activity bounds/insets
and exact full-screen policy. If a future own-package scaling option is needed,
make it opt-in with verified readback and restoration.

## 4. Better diagnostics, but still no complete restore recipe

The new local framework inspection finds a continuity command argument `list`:
the policy handler accepts an own-package argument followed by `list`.
`ContinuityPolicyService.listPolicy` prints policy version and matching configured
lists. It does **not** print the complete `LOCAL_POLICY_BY_COMMAND` map or
`LOCAL_COMMAND_ALLOW_START_SET` needed to reconstruct all temporary state.
Component matches also use a prefix/filter path, so parsing requires care.

`handleSet(allowstart)` updates both a local command map and an allow-start set.
`handleClear` removes entries and clears several Activity compatibility effects.
These are not equivalent to undoing exactly one operation. Simply restoring a
previous map value is also not established as sufficient: the inspected setter
adds allowstart membership but does not visibly remove it when another policy
is subsequently stored. Exact restoration remains an unresolved contract.

Likewise, `MiuiSizeCompat`'s `dump-rule` is scaling readback, not admission
readback. Do not confuse the services or promote a partial diagnostic into a
backup receipt. Upstream returns success without verifying final admission or
scaling state; borrow the mechanism, not that success criterion.

The upstream README says refreshing the cover-app list may require restarting
FlipHome. Our Global code shows local allowstart changes increment a version used
by the continuity service and launcher. Trace the actual EEA refresh behavior;
do not blindly force-stop or clear launcher data. Preserve the user's pins.

## 5. Expand the future exact-device capture

The original capture helper only collected `miui-services.jar` alongside AOD and
FlipHome. This audit locates the relevant property/admission logic in two
additional files:

```text
/system_ext/framework/miui-appcompat.jar
/system_ext/framework/miui-appcompat.appcontinuity.jar
```

Add both to the explicit read-only capture allowlist, with on-device/local hashes
and existing identity guards. Inspect the current working helper first because
another agent may already be extending it. Keep its report clear that artifact
identity is not live policy or window evidence.

Global hashes inspected here:

| Library | SHA-256 |
|---|---|
| `miui-appcompat.jar` | `d2ded23d615794277bee81901bbaf24fb0b483048672244327def6c2caff7415` |
| `miui-appcompat.appcontinuity.jar` | `1513678c67c2254e6dad82534d57b7dd5c329eb34e3815d80add33bba813c313` |
| `miui-services.jar` | `3ee0c554ec6f92da3176e258781bd5dca269fea921ba893a8af8bce4177a329b` |

The two newly extracted libraries passed ZIP CRC checks and JADX CLI completed
without a reported failure. Relevant property, registry and command methods were
inspected. This remains static analysis of Global firmware, not an EEA execution
test or proof every decompiled method is exact.

## What can proceed without the phone

1. Finish the compact-window routing fix and measured layout diagnostics.
2. Add and compile-test the source-backed property declaration on the intended
   activities. Add QA for typed manifest lookup and keep feature status pending
   physical validation.
3. Extend the future artifact capture to the two compatibility JARs above.
4. Design/test a fixed own-package setup abstraction with separate permission,
   command-result, policy-readback and launcher-visibility states. Keep mutation
   disabled where the prior-policy/restore contract is unknown. Do not report
   fixture success as device support.
5. Continue native Charlie preparation/motion-analysis tooling independently.
   MixFlipTool supplies no PAG, tiny-keyguard installation, pet generation or
   screen-power solution.

This is enough to reduce uncertainty and produce a better testable APK now.
Phone-dependent acceptance still includes actual icon admission, full-screen
behavior, rotations/camera clearance, fold/unfold, secure sleep, native pet motion
and restoration. KernelSU needs a separately rooted phone for its hardware gate.

## Reuse boundary

The upstream repository carries GPL-3.0; Flip Pets' generated code is MIT. No
upstream implementation was copied into the app during this audit. Use the API
contracts and independently written integration for this plan. If the project
later chooses to vendor upstream code, handle its license explicitly rather than
silently labeling it MIT. Do not replace the current build with upstream Gradle
or lower our supported SDK solely to match its 2024 configuration.
