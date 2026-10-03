# Changes

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
