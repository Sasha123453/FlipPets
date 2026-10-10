# Native-launch cards: app implementation and device gates

Flip Pets now has a separate ordinary `CoverAppsActivity` for the three bundled
public Xiaomi HTML cards. It uses normal Activity/Recents behavior and the same
code for rooted and unrooted phones. It does not join the supervised pet task,
CoverGuard, hinge fade or display-state ownership. The session Stop receiver closes
only controlled pet activities. Back/Home and the stock system manage these cards.

## Setup and selection

Main → **Карточки в штатном внешнем меню** offers an explicit, off-by-default
choice to open cards when the ordinary Flip Pets launcher entry runs on the cover.
Apply saves that choice; Cancel does not. The user must select the normal Flip Pets
entry in Xiaomi's native cover-app settings if that firmware admits it. The separate
**Открыть карточки отдельно** action opens the same foreground surface for ordinary
use and testing; it does not establish Xiaomi launcher admission.

Routing checks `ruyi`, a non-default display, the observed 1208×1392 physical mode
(either orientation), secure/protected-buffer/presentation flags, a sufficiently
large current window, and awake/unlocked state. It does not assume display ID 1
or interpret a narrow Main window as a cover. These dimensions and public flags
come from historical EEA MIX Flip display observations; their combination is a
conservative routing profile, not proof of a native launcher integration. Unknown
contexts retain Main. An explicit settings entry bypasses routing. On unfolding,
the system can retain the card activity and it remeasures rather than forcing a
display transition or returning to the gallery.

Native card navigation uses `native-cards` preferences and
`https://native-cards.flippets.invalid`. The open-phone supervised card selection
uses its existing preferences and origin. Browsing native cards does not select a
card for the pet session. Original HTML and attribution remain unchanged. Their
own localStorage keeps water, vocabulary and Pomodoro state across reconstruction;
Pomodoro still has no background alarm.

## Rendering and lifecycle

The original CANVAS_W=976 contract uses CANVAS_H from measured host bounds before
the initial native WebView load. Rotation captures a new response height. Artwork
fills the window; navigation uses actual system-bar/cutout insets. Insets do not
prove physical camera clearance where HyperOS does not report the cameras.

The WebView exists only while the activity is resumed, focused, awake and unlocked.
It is destroyed on pause/focus loss and rebuilt from saved card data on return.
There is no wake lock, keep-screen-on, turn-screen-on, show-when-locked, supervisor,
foreground service or global WebView timer control. File/content/network access,
external navigation and permissions remain blocked; there is no native JS bridge.

## Verification and remaining work

`work/tests/run_native_apps_qa.py` exercises the actual activity on the explicitly
identity-checked emulator. It sends card MotionEvents through the Activity view
tree, copies rendered window pixels with PixelCopy, and checks navigation/storage
isolation, rotation, Activity reconstruction, real shell StopCover broadcast,
settings Back, Home/re-entry and force-stop/process reconstruction. A random origin
isolates QA data. Its private checkpoint keeps the original native selection and
an app-private comparison digest alongside test checkpoint data; it is deleted
after restoration. The host
temporarily isolates/restores this app's real notification listener because its
reconnection independently updates the pet revision. No notification contents are
collected. `run_native_route_tests.py` separately checks the pure profile predicate.

Exact EEA FlipHome/continuity APK/JAR identities, stock admission/list refresh,
full-screen/widget-strip behavior, both physical rotations/cameras, real fold
continuity, secure lock/Power/timeout and reboot recovery remain phone tests.
The inspected Global FlipHome cannot certify those EEA contracts. No speculative
manifest types or special-action entry was added for the new activity.

Package-specific shell admission and independent root boot restoration require a
verified policy reader, exact prior-policy receipt and restore semantics. They are
not enabled by this candidate. Root does not broaden this activity's lifecycle or
make unverified native admission successful. The open-session root module and
native tiny-keyguard pet motion/apply/restore remain separate capabilities; see
`native-cover-capabilities.json` and the integration plan.
