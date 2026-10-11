# Native cover integration: investigation and agent handoff

Research date: 10 October 2026. Repository: `E:\FlipPets`.

**Status: planning only.** The user requested investigation and this Markdown handoff, not implementation. The phone is still unrooted. Do not install root, flash, alter the phone, apply a native template or implement these proposals until implementation is requested. Pet generation and alternative generation backends are deferred. Use known donor assets for the first native pet proof.

**Update — 11 October 2026:** the user resumed implementation. The source-feasible controller, native-launch card and known-pet preparation steps are
implemented and independently reviewed; see `HANDOFF.md` for exact artifacts,
verification and the remaining device admission/motion/restoration gates. The original planning status
above describes the research session. Physical device changes, native Apply and
generation remain outside the resumed source-work milestone.

This is the current recommendation. It supersedes the sequence and generation requirement in [the earlier plan](root-native-integration-plan.md). That document retains useful source notes and root-controller failure cases, but its generation milestone is inactive.

## Decision

Build on **MIX Flip's existing native hosts**, with app-owned rendering for full-screen mini-apps:

1. Preserve the existing open/awake/unlocked pet session. Harden its optional KernelSU supervisor first when root work resumes; retain Shizuku as default.
2. For folded **unlocked apps**, adapt a normal Flip Pets activity and let Xiaomi's FlipHome launcher/continuity system launch it. Reuse our offline mini-app renderer. Investigate non-root admission before adding any native hooks.
3. For a folded **lockscreen pet**, continue the existing `com.miui.aod` tiny-keyguard editor/PAG investigation. Prove playback, native copying and exact restoration with one donor asset. Root is a possible installation/diagnostic aid, not yet a proven requirement for this editor route.
4. Treat native **2×3 MAML widgets** as a later, optional root extension. A real host exists in FlipHome, but registering an additional widget needs more than copying a resource.
5. Do not transplant the whole 18 Pro rear-screen subsystem. It adds dependency, framework and update coupling without helping the quickest app route.

This changes an earlier overly broad assumption: adding apps does **not** inherently require porting the 18 Pro native card runtime. Native launcher integration and native rendering are different things. Our offline WebView cards can run inside our ordinary activity while Xiaomi handles launching, folding, keyguard and power.

| Goal | Best non-root option | Best root option | Evidence / work remaining |
|---|---|---|---|
| Reliable current open-phone pets | Existing Shizuku controller | Harden current script-only KernelSU controller | Existing behavior retained; root hardware QA unavailable |
| Folded unlocked full-screen mini-apps | Native FlipHome launch + app adaptation; package-specific Shizuku/ADB admission if required | Same activity; opt-in boot restoration of verified admission policy | Strong code/documentation evidence; exact EEA launcher and phone behavior untested |
| Folded native lockscreen pet | OEM editor route, if its native writer accepts our resources | Same native renderer; root-assisted staging/restore only if needed | Historical static preview only; motion, Apply and restoration unresolved |
| Small native cover widgets | No verified public third-party registration route | Narrow FlipHome catalogue/resource extension | Actual host verified; registration, cache and rollback work medium/high |
| Original 18 Pro native JS Canvas cards | App-contained runtime adaptation if later justified | Root provides installation, not missing runtime compatibility | Large port; not recommended for this stage |
| Pet after main-screen Power/timeout while unfolded | Unresolved | Separate power/framework research | Neither a root supervisor nor app admission proves this |

“Non-root” has two levels here. A normal app-only entry needs no privileged helper if the stock policy admits it; that has not been established for our package. Shizuku/ADB remains non-root but supplies shell privileges for a temporary compatibility override. Do not market that as setup-free or reboot-persistent.

## Source identity and strength of evidence

Read `AGENTS.md`, `HANDOFF.md`, `TODO.md`, [folded options](folded-wallpaper-options.md), [power findings](independent-display-power.md), [root module](kernel-su-module.md), [native preview evidence](native-tiny-preview-evidence.json), and [18 Pro card runtime](donor18-mini-app-runtime.md).

| Source | What was inspected | Boundary |
|---|---|---|
| Actual MIX Flip EEA `OS3.0.303.0.WNIEUXM`, Android 16 | Earlier AOD/editor and wallpaper extraction; accepted Charlie preview | No root, motion/Apply/rollback proof |
| MIX Flip Global `OS3.0.303.0.WNIMIXM` | Newly extracted FlipHome APK and stock date-widget MTZ, Java/DEX inventory | **FlipHome has not been hash-compared with the actual EEA phone** |
| 18 Pro `hongkong`, `OS4.0.15.0.XFRCNXM` | Previously verified product/system_ext resources, Themes and subscreencenter code | Whole OTA remains incomplete/non-flashable; not an installed donor runtime |
| 17 Pro `pandora` | Earlier asset and power comparison | Do not relabel its framework findings as 18 Pro evidence |

Fresh Global evidence:

- Product image: 3,765,919,744 bytes, SHA-256 `89100bc816e60aebd4152aa60dbe832a2b83cc9e815181f6e8b0e11b68ce9107`. Its historical extraction sidecar records payload operation and partition hash checks; it does not contain a digest. The listed digest is the fresh local image hash.
- `/priv-app/FlipHome/FlipHome.apk`: 23,241,468 bytes, SHA-256 `e3c03f3307dae5b2799f9c62f27347b038f575acbc7f54c73270d54429433027`, version `ALPHA-1.1.4.1103-04221121` / `101041103`, min SDK 34 / target 35. APK ZIP CRC passed.
- Stock `flip_watch_maml_dateshow.mtz`: SHA-256 `7ac35f84cc13f00204562a8528d64ae1eb1f7e84f387bb380acf40edc1424fb2`; outer and nested ZIP CRC passed.
- JADX 1.5.6 CLI produced usable inspected methods but reported **95 decompilation errors** across the APK. Do not treat the output as recompilable source. Validate any ambiguous or failed critical method against DEX before implementing a hook.

Machine-readable hashes, class/method line anchors and limitations: [ruyi-fliphome-native-host-audit.json](../work/research/ruyi-fliphome-native-host-audit.json). Raw output stays ignored under `work/folded-research/fliphome-audit/`; Java paths below are relative to its `decompiled/sources/` directory. Reproduce with the CLI main class `jadx.cli.JadxCLI`; the all-in-one JAR's default main opens the GUI.

The earlier AOD APK hash is `31c6dd09226e24f13f519822425a0b3f2a6d4fb8d6bf565bbd3a0568ee494d5d`. A matching historical AOD does not imply matching FlipHome or framework. Bind future capability profiles to the exact target build and relevant APK/JAR hashes.

## What the MIX Flip code actually provides

### Native launching of ordinary apps

`com/miui/fliphome/model/DefaultLauncherApps.java` enumerates `LauncherApps` activities. `addValidAppsToAllAppList` admits activities by component or package allowlists after explicit exclusions. `initValidApplist` obtains these from the `continuity` service using `getContinuityActivities("app_intercept_component_allowlist")` and `getContinuityPackages("app_intercept_allowlist")`.

The launcher caches a continuity version. An unchanged/non-positive version can skip refresh; a successful shell command alone is therefore insufficient evidence that the selectable launcher list changed. Confirm admission, selection in Settings, icon visibility and actual launch separately. Preserve existing launcher pins/data; do not use `pm clear` to refresh it.

`utils/PerformLaunchAction.java` has a special `miui.fliphome.default` action, but dispatch is gated by a fixed five-package set in this Global APK: Weibo, Meitu, NetEase Music, Xiaomi Home and Tencent News. **Adding that intent action to our manifest alone will not select our cover-specific entry.** Use a normal launcher entry first. A root hook adding only our package to that set is a possible convenience later, not a prerequisite for cards.

The same model exposes package-oriented lookup methods that return one matching entry. Multiple activities/aliases may therefore be collapsed or ambiguously selected despite component enumeration. Validate this before choosing a second launcher icon as the product design.

Official corroboration: Xiaomi documents native cover app launching, temporary `allowstart` testing, selecting the app in cover Settings, continuity handling and full-screen configuration. It also documents `miui.supportFlipWatchOverlayGroupView` as a package/activity **property**, whereas full-screen behavior uses typed metadata. The testing override expires after reboot. [Xiaomi Flip adaptation guide](https://dev.mi.com/xiaomihyperos/documentation/detail?pId=2026), updated 28 February 2025, checked 10 October 2026.

Future targeted probe, only after phone testing is authorized and the explicit device serial is verified as MIX Flip:

```text
adb -s <verified-MIX-Flip-serial> shell wm dump -setForceDisplayCompatMode org.flippets.app allowstart
```

Use no implicit ADB target and no all-app allowlist. Record the prior package policy first. The documented package-scoped `clear` operation clears its override policies; it is not necessarily an exact inverse if other package overrides already existed. Design restoration accordingly. Do not execute this command merely because it appears in this plan.

Our manifest currently puts Boolean `miui.supportFlipFullScreen=true` and metadata `miui.continuity.policy=5` on `PetActivity`. The official examples use integer full-screen values and refer to an admission property whose complete identifier is not established by that prose. Trace the exact target framework reader for the property name, type, scope and values. **Do not declare the current metadata sufficient or guess a replacement.** The existing `PROPERTY_COMPAT_ALLOW_SMALL_COVER_SCREEN` likewise does not prove Xiaomi admission.

### A real native MAML widget host

Relevant files:

| File under `com/miui/fliphome/` | Finding and consequence |
|---|---|
| `widget/ui/maml/FlipMaMlHostView.java` | Extends `MamlView`, selects `2X3`, delivers resume/pause and launcher/window lifecycle commands. This is a native rendering host. |
| `widget/ui/maml/FlipMaMlWidgetCompat.java` | Loads a local directory or MTZ through `ParseMamlResource`, selects dimensions 2×3, resolves previews/metadata; uses device-protected storage. Failed local loading can delete the cached ZIP/directory before loading the preset. |
| `widget/model/FlipWatchDefaultConfig.java` | Enumerates fixed names, not arbitrary directory discovery. `ruyi` takes the N8 list; the O8 check identifies `bixi`. Adding a file is not registration. |
| `widget/model/FlipWidgetModel.java` | Cached selected-widget list, maximum five; serializes the selection to a Room row. |
| `widget/model/database/FlipWidgetRepository.java` | Private `flip_widget_db`, device-protected context. A live DB edit would contend with app caches and database state. |
| `settings/widget/WidgetViewModel.java` | Settings rebuilds selection from the known catalogue. An unknown entry injected only into the DB is fragile. |
| `FlipHomeProvider.java` | Reviewed calls cover previews and `showFlipWatch`; no widget registration call found in that switch. |
| `widget/ui/FlipWidgetManager.java` | Caches host views and forwards visibility/lifecycle. A no-op `recycle()` in the host is not proof resources are always released. |
| `widget/WatchOverlayWindow.java` | Observes folding, screen state and launcher lifecycle. A touch-routing branch requires unlocked keyguard; screen OFF dispatches stop. This does not prove a secure lockscreen app host. |

The preset code path is `/system/media/theme/default/maml/`. The actual extracted preset member is in the product image under `/media/theme/default/maml/`. Verify the runtime filesystem alias/mount and cache paths on the target; do not invent a module overlay destination from only one of these paths.

The inspected date package has `description.xml`, preview images and a **nested ZIP named `widget_2x3`**, containing its own `manifest.xml` and resources. Its root is `Widget`, with logical `screenWidth=1208`, `resDensity=520`, `frameRate=0`, and `useVariableUpdater=DateTime.Second`. That logical width does not make it a full-screen host. It reacts to `init/resume`, `pause`, `launcherPause`, `launcherResume`, and `colorChanged`; it uses calendar content-provider binders. Thus geometry, external commands and provider contracts matter, not just XML syntax. Frame rate zero also does not mean no scheduled variable updates.

`com/miui/maml/elements/ScreenElementFactory.java` supports normal MAML elements, WebView, video, Lottie and conditional PAG. `PagUtils` requires HyperOS version at least 2 and `/system_ext/framework/pag-hyperos-release.jar`. Actual PAG playback still needs validation. No QuickJS/JsCanvas declaration and no `.so` member were found among this APK's 13,277 declared classes and ZIP members. This is a bounded APK inventory, not proof that no external framework can supply additional features.

Do not move our HTML into this privileged MAML WebView as a shortcut. `WebViewScreenElement` enables JavaScript and exposes a `maml` JavaScript interface; that has different capabilities from our isolated `MiniAppView`. Only reviewed, dependency-bounded MAML should be considered for a native widget experiment.

### Native tiny-keyguard pet route

The previously inspected entry is `com.miui.aod/com.miui.tinykeyguard.editor.edit.EditActivity`, action `miui.tinykeyguard.editor.EDIT`, string extra `param_template_item_json`. The relevant `TemplateItem` uses `clockInfo.templateId=ai_pets`, `pets.petCategory=2`, and `aiPetsData` with `bizId`, `resourcePag`, `resourcePic`, plus first/last frame coordinate axes.

This is a **local renderer/import contract**; its “AI” naming does not require generation for a known donor PAG. Historical rootless preview accepted JSON and displayed Charlie, without native Apply or selection/history changes. Poster visibility did not establish animation.

Trace `Tiny-EditActivity`, `Tiny-TinyEditorAiPetsView`, `Aod-TinyEditorPetsPagView`, `Tiny-AiPetsPagView`, `Tiny-TemplateApiImpl`, and `Tiny-TemplateFilePathGenerator` under ignored `work/folded-research/gateway-current/`. These filenames are evidence extracts, not proposed replacement classes.

The renderer composes at 1208×1392 with orientation-dependent translation. It does not automatically perform our app's donor-to-cover scale adaptation. Donor Charlie is 976×596; frame axes, poster and media must agree. Prepare an adapted resource only if required, keeping original bytes/provenance. Do not infer safety from a schematic camera circle or a single frame.

On confirmation, native code has resource-copy and current-template/history paths, including `tiny_keyguard/<timestamp>/AI_PAG`. Inputs are filesystem paths, not a demonstrated generic content-URI API. Test who can read staging and who performs copying. The fact shell could not write the wallpaper directory does not prove the OEM editor cannot do so.

## What is worth porting from 18 Pro

| Candidate | Effort judgment | Recommendation |
|---|---|---|
| Known donor PAG/artwork and frame/poster metadata | Low to medium; format/placement dependent | Reuse for first native pet, one scene first |
| Source-backed finite behavior such as Carp selection/fades | Medium per renderer | Existing app adaptation is useful; single-PAG native import does not carry this state machine |
| Existing public Water/Words/Pomodoro HTML | Low incremental host work, medium native-launch/lifecycle QA | Reuse unchanged in app-owned offline WebView |
| Basic MAML expressions, animations and input patterns | Medium after dependency audit | Adapt selectively to verified MIX Flip elements and 2×3 widget contract |
| Six built-in donor native cards | Medium/high and card-specific | Inspect provider/service/permission calls first; no blanket portability claim |
| Donor `JsCanvasScreenElement` / `QuickJsBridge` / `libquickjs_canvas.so` | High | Only a future app-contained runtime project if real desired MTZ content requires it |
| Donor Themes, subscreencenter, framework or SystemUI wholesale | Very high | Reject for the first integration milestone |
| AI generation/account/backend pipeline | Outside current scope | Deferred; root cannot supply Xiaomi's service |

The donor runtime really differs from our WebView. Themes' `RearScreenAiAppMamlView` loads MTZ, while JsCanvas executes MAML scripts via QuickJS and Android Canvas. Its ABI, JNI, MAML version, font/input/lifecycle and privileged-service dependencies require adaptation. A KernelSU module does not provide those dependencies automatically. Preserve the distinction between public HTML examples and the six verified firmware MAML cards; see [donor runtime evidence](donor18-mini-app-runtime.md).

## Instructions for the implementing agent

### 0. Establish a baseline and capabilities

After the user resumes implementation, inspect `git status`, current source, APK/module/controller hashes and running QA processes. Preserve unrelated work and the signing key. Read both this document and the prior root-controller analysis. Do not assume root has been installed since this planning session.

Create a small capability record with separate statuses for open-session Shizuku, open-session KernelSU, native launcher apps, tiny-keyguard preview/apply/restore, and native MAML widgets. Each status needs build/hash identity and evidence. Never use one global “root supported” flag to imply all of them.

For phone probes, identify the explicit serial privately and verify `ruyi` and the exact EEA build. Extract/hash only the APK/JARs needed. Compare actual FlipHome with this Global audit; trace the exact framework continuity policy handler, including `allowstart`, list refresh and metadata/property typing. Keep device identifiers and raw dumps ignored.

### 1. Harden KernelSU for the existing mode

Keep this a script-only optional backend generated from the canonical controller. Relevant files are `work/kernel-su/module-control.sh`, `boot-completed.sh`, `action.sh`, `customize.sh`, `uninstall.sh`, `work/build_kernel_su_module.py`, `outputs/flip-pets-control.sh`, `work/app/assets/controller.sh`, `CoverGuard`, `ShizukuBridge`, and `ControllerService`.

Resolve these concrete issues before describing it as reliable:

1. Boot invokes startup once, and startup needs app external storage. Handle first-unlock/storage readiness with bounded cancellable waiting. An unreadable Stop location must not be interpreted as consent to resume.
2. `supervise` can clear Stop and return before child survival is acknowledged. Separate explicit Start from unattended resume, add a real acknowledgement, and preserve Stop arriving during startup/recovery.
3. Enabled/owned files live inside the replaceable module directory. Define opt-in persistence, update migration and interrupted-install behavior. Installation must not turn the session on.
4. Current ownership uses a marker, UID and command-line substring. Establish exact process identity, PID-reuse handling and serialized Action/boot transitions. Never take over an unrelated Shizuku controller.
5. Check root-created files and locks when returning to shell. Avoid mode/owner leftovers that prevent Shizuku recovery; do not make control paths world-writable.
6. Keep `coverSession=true` and the canonical fold/lock/sleep guards. Keep UID-2000-only Binder checks where intended; a new root control path must be separately authenticated.
7. Verify module disable, uninstall, app Stop, process death and reboot, including the fact that disable need not call uninstall. Use bounded recovery; no watchdog that overrides user Stop.

KernelSU scripts do not require a mounting metamodule; filesystem overlays do. Java method hooks require a separately selected compatible hooking mechanism. Do not add one merely to run ordinary cover apps. [KernelSU module guide](https://kernelsu.org/guide/module.html), checked 10 October 2026.

Acceptance: targeted controller/wrapper fixtures, shell syntax, matching APK/module provenance, then actual rooted MIX Flip UID/SELinux/start/Stop/boot/first-unlock/fold tests. Until rooted hardware evidence exists, label this experimental. Root installation itself remains a separate user action.

### 2. Add native-launch apps without making them depend on root

Proposed `CoverAppsActivity` is a new, app-owned foreground activity for native launcher entry. Reuse `MiniAppView` and content validation, but not the current `PetActivity` lifecycle wholesale:

- `PetActivity` without `coverSession=true` adds `FLAG_KEEP_SCREEN_ON`. With the extra it enters the controlled-cover set, starts session plumbing and can be stopped on fold. Neither behavior is the desired native-launch app contract.
- Native-launch cards must not join `PetActivity.covers`, `CoverGuard`, hinge fade or supervisor ownership. `STOP_COVER` must not close a user-launched card accidentally.
- Preserve the separate Main/controlled-cover task policy. Test any new task affinity against Xiaomi continuity and Recents before fixing it as the contract.
- Prefer an ordinary launcher entry. Initially route Main's native cover launch to the card surface using validated window/display context. Do not equate a narrow main-window or a hard-coded display ID with the folded cover. Retain access to settings, and validate context again after configuration changes.
- Evaluate a separate launcher activity/alias only if actual FlipHome selection supports it predictably. A special-action-only entry is insufficient on the inspected APK.
- Correct full-screen/property typing after tracing the exact build. Hide the widget strip, if appropriate, using verified per-activity support rather than leaving a persistent provider toggle behind.
- Honor real bounds, density, rotation and insets. Fit controls around actual cutouts; background may extend farther than interactive content. Preserve the existing logical Canvas/touch mapping contract.
- Save card navigation/state across native folding or Activity recreation. On unfold, allow normal system continuity; return to the card rather than resetting to the gallery. Re-evaluate metrics instead of forcing display state 5.
- Use normal visibility lifecycle; no keep-screen-on, wake lock, `showWhenLocked`, `turnScreenOn`, root launches while locked or background WebView decoding.

`MiniAppStore` currently has one global live selection. Give native-launched cards separate navigation/selection state so browsing them cannot replace the open-phone pet. Keep preview origins isolated, original HTML bytes/hashes, blocked network/file/content access, denied permissions and no native JS bridge. A root helper must never accept commands from card content. Do not use global WebView `pauseTimers()` across the two displays.

Non-root setup: first test stock admission. If needed, perform a package-specific shell grant after explicit feature opt-in, report its actual success, and let the user select the icon in native Settings. Handle missing/restarted Shizuku, policy reset on reboot, stale launcher list and app recreation as separate states. No endless retry/foreground service merely to keep an icon admitted.

Root setup: reuse the **same** app and admission operation. Add an independent opt-in for boot policy restoration, not tied to the open-phone session's enabled marker. Wait for the verified service/package, apply once, read back and log a bounded result. Preserve prior policy and later user changes on disable. Do not continually overwrite cloud/system policy or launch the card at boot.

Acceptance: native icon selection/launch, real touch on all three cards, full-screen/strip behavior, both rotations, fold/unfold continuity, Home/Back/Recents, secure lock/Power/timeout, process recreation, offline behavior and reboot/setup recovery. Emulator layout/touch tests supplement this; they do not prove Xiaomi admission.

### 3. Prove one native folded pet with exact restoration

Keep this investigation independent of apps and generation. Begin with one known PAG and a decoded matching poster/frame geometry. Trace autoplay/inherited PAG behavior and load acknowledgements. Several distinct captured native frames must demonstrate animation; a poster, progress counter or app-rendered preview is insufficient.

Before Apply, inventory the selected template, relevant history entries, referenced files and ownership/mode/SELinux labels. Define an installation receipt that records only our changes and an exact restore procedure. `rollbackAiPetsByBizId` is not automatically a complete backup/restore contract. Do not copy/overwrite a live global settings database.

Attempt the OEM writer path without assuming root necessity. If it cannot read or stage the resource, document the exact denied operation. A root helper may then supply narrowly scoped validated staging/native installation, preserving labels and native transaction semantics. Do not solve it by global chmod, disabling SELinux or replacing the AOD APK.

Handle partial copying, history insertion, selection update and interruptions. Read back before committing success. Rollback must not overwrite a later manual Xiaomi theme choice. Do not remove resources still referenced by native state. App Stop stops the open session; native Restore is a separate explicit operation.

Acceptance: preview motion, folded lockscreen motion, both rotations/camera clearance, screen-off/AOD behavior under stock policy, unlock/fold transitions, reboot, process death, interrupted install and exact restoration. Respect native animation limits: a successful folded lockscreen pet does not promise continuous AOD animation or unfolded main-off playback.

### 4. Optional native MAML widget extension

Only proceed if the user wants small native widgets after the prior milestones. Begin with a reviewed local MAML probe within the actual 2×3 bounds; do not silently replace a stock weather/clock slot.

Prefer a narrowly version-gated additive catalogue hook over a repacked/resigned FlipHome APK. It must make the resource available to both `FlipWatchDefaultConfig` and Settings, maintain the five-selected-widget contract, resolve category handling, and coordinate native cache/model updates. The hook's exact mechanism is an unresolved implementation choice; KernelSU alone does not intercept Java methods.

Validate the real device-protected resource path and preset mount alias. Use an app-owned unique resource identity. Prevalidate nested ZIP paths, size/count limits, required elements, providers and resources. The native failed-load cleanup is a reason to avoid manipulating an existing stock identity. Use supported model operations where possible; do not edit a live Room DB or clear launcher data.

Trace all lifecycle/gesture commands, including the pager intercepting drag versus click, resource release, screen OFF, fold and overlay changes. Keep script/provider capabilities narrowly bounded. No unknown MAML/HTML executed inside privileged FlipHome. For rich cards, launch the ordinary card activity instead of expanding the privileged widget renderer.

Before enabling any hook, establish a boot-safe disable path, exact build matching, stock fallback, restore receipt and proof that an unsupported update leaves the stock launcher usable. If this cannot be achieved with small changes, retain native-launch cards and defer widgets.

## Reusable foundations without a large rewrite

Keep content separate from where it runs. A small descriptor can carry stable ID, origin/hash, asset paths, logical bounds, capabilities and supported targets. Add only fields actually used. Preserve the existing catalogue IDs and scene layout profiles.

Three execution paths should stay explicit:

| Path | Owns rendering/lifecycle | Shares |
|---|---|---|
| Existing controlled open session | App renderer plus Shizuku/KernelSU session policy | Donor files, validated content, app geometry |
| Native-launch folded apps | App renderer, normal Activity lifecycle, Xiaomi launcher/continuity | Offline card catalogue, renderer, card persistence |
| Native folded pet / later widget | Xiaomi renderer and stock screen lifecycle | Validated export bundle, capability profile, install/restore receipt |

Share content validation, geometry metadata, provenance, package admission and bounded status reporting where relevant. Do not force native tiny-keyguard and app WebView to share one renderer or selection preference. Native widget export is an optional adapter. This lets a new ordinary card be added without changing root supervision, and a new compatible pet use the same native installer after validation.

## Verification and deliverables

For implementation, run only tests appropriate to changed paths, then the required current-SHA suites before a release. Build with `python -X utf8 work/build_apk.py`; build the optional module with `python -X utf8 work/build_kernel_su_module.py`. Preserve 16 KiB native/APK alignment and matching controllers. Use the exact target emulator identity; hardware QA needs a verified explicit serial.

| Area | Required evidence |
|---|---|
| App cards | Current APK SHA, actual rendered captures, MotionEvents, persistence/recreation and isolation results |
| Root session | Wrapper failure cases plus actual rooted UID/SELinux/boot/Stop/fold results |
| Native launcher | Actual EEA hashes, policy before/after, native Settings and launch, continuity, lock/sleep behavior |
| Native pet | Exact asset hashes, real native motion, install receipt and successful exact restore |
| Widget extension | Matching FlipHome/hash, additive registration, selection persistence, lifecycle/gesture tests, hook disable/reboot fallback |

Do not publish serials, private photos, unrelated app UI or broad logs. Keep source evidence separate from emulator results and physical results. Existing historical QA cannot validate a new APK. New product changes require README/CHANGELOG/install documentation and a precise HANDOFF update. A research-only update does not require an APK build.

The implementing agent should deliver small reviewable milestones, record unresolved gates honestly and stop the relevant branch if restoration or compatibility is unproven. Continue independent app work where possible. Do not replace the requested native experience with screen-wake tricks or claim a donor-exact port from a visually similar adaptation.

**First next step when implementation is requested:** establish the exact EEA FlipHome/continuity contract and harden the existing root wrapper in source. Rootless native-launch cards can then progress without waiting for root installation. Native pet Apply remains behind the motion and restoration gates. No generation work is required.
