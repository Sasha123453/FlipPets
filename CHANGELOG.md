# Changes

## 0.8

- Bounded cover-display readiness/startup retry after unfolding; steady polling
  remains2seconds. Addresses0.7 trace evidence: the first state5 request rolled
  back to3, then the supervisor waited10seconds before restarting.
- Fresh exact-SHA268-check emulator QA is pending. Version0.8 is not being installed
  or tested on the phone for this release; the phone remains on0.7.
  No claim of instant fold recovery or uninterrupted rootless reboot startup.
- Release packaging validates versionCode8 and keeps0.7 physical/runtime/profile
  evidence with its original SHA as historical, separately from new0.8 results.

## 0.7

- Material You settings/gallery with system tonal colors and light/dark support.
- Optional compact battery, media and visual timer/stopwatch overlays; default off.
  Media controls use the existing notification listener; timer has no audio/background alarm.
- Separate cover task and user-enabled foreground session with a quiet Stop notification;
  settings-task dismissal is separated from the cover session. No wake lock or hidden rendering.
- Optional on-change hinge fade: exposed angle sensor, otherwise discrete Xiaomi flip status;
  no claim of continuous angle from discrete states, and no fade when neither is available.
- Emulator utility QA restores preferences and uses an actual synthetic MediaSession.
- New release packager requires fresh SHA-bound 170/68/15/15 QA and keeps historical
  physical/resource/lifecycle evidence under its original SHA.
- Limited current0.7 EEA phone validation: installed APK hash, Shizuku UID2000,
  simultaneous panels/state5, foreground service and real hinge-angle sensor registration.
  The user confirmed Main-task dismissal retained the session. Fold return was
  intermittent: immediate or about20seconds; readiness retry is addressed in0.8.
  Utility controls and long battery/stability testing remain pending. Rootless Shizuku needs restarting after reboot; foreground
  service does not bypass HyperOS force-stop.

## 0.6 (intermediate local build)

Material You interface work; superseded by 0.7 packaging and validation.

## 0.5

- Classic pets play once and hold, based on nine inspected original MAML scripts.
- Reactive gesture/touch clips play once; the return timer follows the clip duration.
- Optional calm mode holds Bubbles/Roe after one cycle.
- Cover layout is reapplied explicitly; configuration/geometry/playback events are logged.
- Physical MIX Flip testing: two screens, fold return, Shizuku shell UID 2000,
  hardware decoding, photo import and persistence after app restart/source deletion.
- Repeated 170 clip, 68 composition and 15 UI checks on standard Android 16.
- Phone process CPU: approximately 39% of one core at 30fps continuous playback,
  approximately 0.16% while holding a frame, each sampled for 12 seconds.

## 0.4 baseline

Rootless resource port with 30 catalogue entries, 170 original clips, offline
compositions, gallery/favorites, private photo import, diagnostic export, optional
live wallpaper and guarded Shizuku cover controller.
