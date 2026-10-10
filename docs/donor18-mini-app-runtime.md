# 18 Pro mini-app files and runtime

Read-only audit on 2026-10-10 of the already verified `hongkong`
OS4.0.15.0.XFRCNXM product/system_ext resources. The complete OTA is still
incomplete and unverified. No donor APK was installed and no account or online
download API was used.

The firmware contains an actual card runtime, different from Flip Pets' WebView
host. `subscreencenter.apk` includes `JsCanvasScreenElement`, `QuickJsBridge` and
`libquickjs_canvas.so`. The element reads inline MAML `<Script>` text or locale
`.js` variants, creates a QuickJS runtime, supplies canvas dimensions and executes
frames against Android Canvas. The same native library bytes occur in the donor
Themes APK. Themes' `RearScreenAiAppMamlView` loads MTZ resources through
`ZipResourceLoader` and `ScreenElementRoot`.

This verifies a native JavaScript Canvas path in the donor code. It does not
establish that every card uses it, that the public HTML examples equal downloadable
MTZ resources, or that this runtime can be dropped into MIX Flip without adapting
its dependencies and lifecycle.

The built-in catalogue `/media/rearscreen/appcard/default/rearScreen.json` has
four categories and six packages:

| Category | Built-in cards |
|---|---|
| Weather/calendar | Desk calendar, Upcoming events |
| Tools | Incognito mode |
| Smart car/home | Xiaomi Home camera, Xiaomi car |
| Lifestyle | Stocks |

All six packages were extracted from the product image after rechecking the
complete image SHA-256, checked for ZIP CRC errors, and inventoried recursively.
They contain MAML manifests and supporting resources, with no HTML/JS members.
Neither `subscreencenter.apk` nor `MIUIThemeManager.apk` has standalone HTML/JS
members either. Water, Vocabulary and Pomodoro were not found in these packages.
This is a bounded search, not proof of absence from every APK, online catalogue or
user-downloaded resource.

Xiaomi's public catalogue frontend explicitly directs 18 Pro users to
Rear screen → AI-generated app cards → Featured apps for its 100 preset examples.
The public records for IDs 1/3/5 supply HTML preview URLs, with no corresponding
native MTZ URL or Themes product ID. This supports their advertised availability,
but does not prove the preview HTML equals a device-side resource package.

The donor also has an online AI-app route,
`GET native/page/v3/AI_GENERATED_APP`, product detail/subject routes, a provider
which resolves `downloadUrl`, and an MTZ download/extraction helper. Access,
authentication requirements, matching product IDs and package equality remain
unverified. A verified downloaded package or user-provided export would be the
next source for those specific cards. Do not present the existing public HTML as
firmware extracts or replace them with unrelated stock widgets automatically.

Sanitized hashes and source anchors:
[`hongkong-mini-app-runtime.json`](../work/research/hongkong-mini-app-runtime.json).
Extracted packages, full inventories and decompiled evidence stay ignored under
`work/extracted/hongkong`. The QuickJS library has not been bundled into Flip Pets.
