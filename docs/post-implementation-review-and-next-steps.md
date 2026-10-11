# Review of the assembled implementation and next steps

Reviewed 11 October 2026 at commit `c548bc8`, against baseline `17ddf28`.
Scope: code review, local artifact/evidence checks, and host tests. No phone or
emulator was contacted in this review. No app/controller implementation changed.

## Assessment

The agent completed substantial source work: root supervision is hardened, the
ordinary card activity is implemented, and the first native-pet resource bundle
is prepared. The architecture follows the intended separation between an open-phone
session, ordinary native-launch apps, and Xiaomi-rendered lockscreen pets.

This is an assembled development candidate, not completed native integration.
The main remaining work is exact-device integration and validation. Do that before
adding more pets, porting the donor runtime or installing native widget hooks.

| Capability | Implemented now | Still missing |
|---|---|---|
| Root open-phone session | Private persistent state, startup ACK, process receipts, cancellation, backend lifetime locks, bounded boot readiness | Actual KernelSU UID/SELinux/boot/fold/switching evidence |
| Ordinary cards | `CoverAppsActivity`, separate selection/origin, Water/Words/Focus, normal visibility lifecycle, measured Canvas dimensions | Exact EEA admission, native launcher routing, full-screen/strip policy, physical continuity |
| Native folded Charlie | Original PAG, matching decoded poster, eight sample frames, inherited OEM playback trace | Real native animation, validated placement, OEM resource copy, installation/restore transaction |
| Native small widgets | Earlier source investigation | No registration hook or widget integration implemented; optional |
| Generated pets / independent main-off display | Deferred | Remain outside the next milestone |

The raw changes were reviewed in `CoverAppsActivity`, `NativeCoverRoute`,
`NativeCards`, Main routing, `MiniAppView`, the canonical controller, module
wrapper/state helper/builder, and guarded native capture. The root changes are
meaningful; the review did not establish an additional root runtime defect.
That is a scoped review, not a substitute for physical root testing.

## Concrete review finding: cover routing assumes a large window

`work/app/src/org/flippets/app/NativeCoverRoute.java:13` requires each window
dimension and total window area to reach at least 80% of the physical cover.
`MainActivity.routeNativeCards()` uses this predicate before opening the cards.

Fresh execution of the actual Java predicate, with identical valid device,
display flags, physical mode and unlocked/awake inputs, produced:

```text
809x1392 route=false
1208x1392 route=true
```

Xiaomi documents 809×1392 as its basic cover app region, with a separate system
area; full-screen presentation is an additional adaptation. See the
[official Flip guide](https://dev.mi.com/xiaomihyperos/documentation/detail?pId=2026),
checked 11 October 2026.

**Impact:** if EEA supplies the ordinary app-region bounds to Main, enabling
cover routing still leaves the user in Main rather than the cards. The current
manifest gives neither Main nor CoverAppsActivity a verified Xiaomi full-screen
configuration. Existing tests check full-cover routing and reject an artificial
300×5568 narrow window; they omit the documented normal app region.

The predicate mismatch is reproduced. The actual EEA window metrics are not yet
measured, so this is a concrete integration risk, not a claimed observed phone
failure. Also verify the folded logical display ID/flags: a profile observed in
the open presentation mode does not prove the folded launcher uses the same
logical-display contract.

**Next correction:** separate verified cover identity from available app bounds.
Capture the actual native launch context, then accept supported native app-area
and full-screen layouts without accepting arbitrary narrow Main windows or
external displays. Add a regression for the real compact cover region and both
rotations. Do not merely lower every threshold or force display state 5.
Full-screen rendering and hiding Xiaomi's widget strip remain separate policies.

## Important baseline interaction

The existing open-session controller already issues package-scoped
`dumpsys window -setForceDisplayCompatMode org.flippets.app allowstart`
at lines 217 and 260. These calls predate the new native-card work. They do not
have the new native-admission receipt/readback/restoration flow.

Consequently, a native launcher trial after starting Shizuku or the root session
may be influenced by a pre-existing compatibility override. A successful launch
would not prove app-only admission. Stop the supervised session and establish a
known policy baseline before distinguishing stock, shell-assisted and root modes.
Stopping the controller alone does not reverse that compatibility setting.
Use observed readback and, when appropriate, a controlled reboot with automatic
root resume disabled; do not use an unverified `clear` as exact restoration.

## Recommended next milestone: native cards on the unrooted phone

This is the shortest path to a useful native feature and does not require root
installation. Treat the following as a proposed next implementation/test task,
not an action performed by this review.

1. **Read-only identity capture.** Use the existing
   `work/tests/capture_native_capabilities.py --serial <explicit-serial>` after
   phone testing resumes. It currently accepts only the observed `ruyi`
   `OS3.0.303.0.WNIEUXM` profile. If the phone has updated, inspect the new profile
   rather than bypassing the guard. Compare FlipHome, AOD and the framework to the
   research copies. The helper captures artifact identities; it does not capture
   policy state or live Activity window geometry.
2. **Measure our native launch context.** Record only our Activity's logical
   display ID/flags/state, physical mode, current/max window bounds, density,
   rotation and cutout/system-bar insets. Check folded, unfolded, both cover
   orientations, and Xiaomi's basic/full-screen modes. Keep private raw evidence
   ignored and avoid other-app screenshots/logs.
3. **Resolve the routing finding.** Apply the smallest verified profile change,
   add targeted regression tests, and preserve the explicit off-by-default
   setting plus access to Main. Do not rely on the donor-only special action.
4. **Prove admission separately.** First try selection and launch from stock
   cover Settings with a known policy baseline. If blocked, trace exact EEA
   policy readback/list refresh/restore before implementing the package-specific
   Shizuku operation. Surface missing Shizuku, admission failure and restart
   requirements distinctly. No broad app grants.
5. **Verify full-screen behavior.** Read the EEA framework metadata/property
   types and values. Set only proven activity-scoped configuration; confirm
   widget-strip visibility and camera-safe touch mapping on the phone. A full
   WebView within a smaller app window is not a full-screen native app.
6. **Exercise the product.** Native icon → each card → real actions; Home/Back;
   settings return; fold/unfold with card state retained; lock/Power/timeout;
   process death and reboot/setup recovery. Confirm hidden WebViews are released
   and the supervised pet selection/data stay unchanged.

Deliverable: a current-SHA APK that demonstrably launches from Xiaomi's cover
menu and behaves correctly under stock folding and sleep, with its admission
requirements stated accurately. This should be the next user-visible milestone.

## Root track: validate the hardened backend

The root module should retain its current role. Root is not a prerequisite for
the native card Activity or evidence collection. No root installation is part
of this review; test this track only once the user has separately installed it.

- Verify UID0/SELinux access to private state, shared lifetime flock, app Stop,
  device-state commands and foreground Activity launch on the actual phone.
- Exercise reboot before/after first unlock, unavailable app storage, the bounded
  ten-minute wait, Stop during startup, normal Stop, and module disable/remove.
- Verify update persistence and switching both directions between Shizuku and
  root without deleting the shared lock inode or leaving presentation active.
- Include the current documented Action behavior: retained opt-in after timeout
  or app Stop can require Action to turn it off, then Action again to start.
  Test that explicitly; do not mistake the first toggle for failed startup.
- Record errors and timings with bounded app-scoped diagnostics. Keep root
  support experimental until these pass.

Only after native admission is understood should a separate opt-in restore that
policy after boot. It must not be tied to enabling the open-phone pet session,
continually reapply policy, or launch cards while locked.

## Native-pet track: prove motion, then transactional installation

Reuse `outputs/FlipPets-native-Charlie-proof.zip`; there is no need to repeat
source extraction merely to produce another poster. Keep generation deferred.

1. Verify the exact AOD build and establish the current native selection/history
   baseline. Trace resource readability and the OEM writer's copy operations.
2. With the phone test authorized, stage the known resource under a unique
   identity and open **preview only**. Capture several distinct native-rendered
   pet frames. A poster, changing background or app playback is insufficient.
3. Validate actual translation, both rotations, full animation envelope and
   physical camera clearance. Eight source samples are not every-frame bounds;
   Charlie's source crest clipping remains. Use frame sampling or analysis
   beyond the eight proof frames when defining safe placement.
4. Specify exact before/after selection and history records, owned resources,
   file metadata, interruptions and later-manual-choice protection. Establish
   a proven restore method before applying a template.
5. Then implement an explicit native Apply/Restore flow and test folded
   lockscreen behavior, stock screen-off limits, reboot and recovery.

Deliverable: one genuinely working native folded pet with reliable restoration.
Expand to more compatible donor pets only after this proves the installer and
geometry contract. A single-PAG native import will not automatically carry over
all the app's reactive multi-scene behavior.

## Further work after those proofs

Once native cards work, adding another reviewed offline card should reuse the
same activity and lifecycle. Localized UI/accessibility improvements can follow
without altering preserved original HTML bytes; identify adapted variants as such.
Do not turn Pomodoro into a claimed background alarm without a separate design.

Once native pet installation works, add more validated PAG bundles and an
explicit option to choose the same pet for folded/native and unfolded/app modes.
Keep their geometry and selections independent internally.

Native 2×3 MAML widgets remain a later additive extension if desired. Full 18 Pro
runtime transplantation, generation and unfolded main-off power integration
remain deferred. None is needed to finish the two useful native milestones above.

## Verification performed in this review

- Clean starting checkout; reviewed the five implementation commits after
  `17ddf28`, ending at `c548bc8`.
- Reran 14 routing tests, 20 native-capture guards and five publication guards:
  **39 host checks passed**. Ran an additional two-input Java route probe as
  described above. These checks contacted no Android device.
- Recomputed the APK, module and Charlie bundle SHA-256 values and checked ZIP
  CRCs. All match the handoff. APK:
  `b8fb78cea3e4fe9142106137e28b6f724c40a92f15c0be6428b4304cd03a9a75`;
  module: `95e02bf4b589ed558bec0204c991ca7ac0f8f5a455c426422a2a1cdd3164563b`;
  Charlie: `e78cdfc3597f6592857c405160e59a6f76c110022b30490f8ec5b8aca5cb9842`.
- Verified canonical/embedded/APK controller equality, module-to-APK binding,
  internal module member hashes, and wrapper/state-helper ZIP-to-source equality.
- Checked 12 card evidence report hashes and 14 pet-preparation report hashes;
  overlapping reports are not independent runs. All 14 card and six preparation
  source hash entries match. Root controller/wrapper/state hashes and all eight
  historical root report hashes also match current local files.
- Confirmed the saved reports bind 374 APK checks, 20 gallery checks and six
  virtual-cover checks to the current APK, with zero recorded failures. These
  Android suites were **not rerun** during this review. The prior 151 controller
  checks/eight shell syntax checks remain historical fixture evidence, not real
  KernelSU or EEA firmware validation.

No APK rebuild, deployment, root installation, native admission grant or Apply
was performed. Only this review/next-step documentation was added to the tracked
work, along with the handoff pointer. The next best action is targeted unrooted
native-launch validation, followed by the smallest code changes that evidence
requires.
