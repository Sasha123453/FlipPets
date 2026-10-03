# Анимации штатной блокировки сложенного MIX Flip без root

Исследовано 3 октября 2026 года, включая read-only осмотр подключённого телефона. **Штатный Xiaomi video-wallpaper engine имеет цель `which=8` — внешняя блокировка. Но прямой вариант установки через Shizuku SDK-copy сейчас упирается в файловые ограничения: shell видит каталоги, однако write-access checks возвращают отказ.** Нужен штатный импортёр/provider, записывающий ресурс своим UID, либо настоящий write-FD gateway. Экспорт MP4 и открытие обычного редактора Xiaomi сами по себе не решают задачу.

Текущий режим приложения остаётся прежним: при складывании возвращается штатный экран Xiaomi. В этой работе не менялись настройки телефона, обои, AOD, системные файлы или код APK. Приложение поверх блокировки и принудительное удержание экрана включённым не рассматриваются.

## Что подтверждено

Официальная [FAQ Xiaomi о динамических обоях внешнего экрана](https://www.mi.com/uk/support/faq/details/KA-485441/) исключает пользовательские динамические обои из поддерживаемых возможностей и отдельно указывает шесть встроенных анимированных питомцев блокировки. [Исходная Global-ссылка](https://www.mi.com/global/support/faq/details/KA-485441/) может перенаправлять по региону; UK-страница содержит тот же ответ. Это ограничение штатного пользовательского сценария, а не доказательство отсутствия внутреннего движка.

Официальная [FAQ о своих изображениях AOD](https://www.mi.com/uk/support/faq/details/KA-492713/) подтверждает путь Settings → External screen lock screen → Always-on display → My theme → Custom image. Она подтверждает изображения, а не произвольные анимации или постоянное проигрывание видео в AOD.

Локально изучена скачанная Global-прошивка MIX Flip `OS3.0.303.0.WNIMIXM`. Read-only осмотр реального телефона подтвердил EEA `OS3.0.303.0.WNIEUXM`: фактические WallpaperOS3 и MIUIAod byte-for-byte совпадают с исследованными Global APK. Themes на телефоне обновлён до `3.0.6.8-global`, поэтому его import/provider путь требует отдельного анализа. Источник неизменённых образов: прежняя папка проекта на C:, `work/images/ruyi/{product,system_ext}.img`. Firmware APK и SHA256 находятся в `work/folded-research/provenance.json`; фактические APK и сырые phone dumps — только в игнорируемой `work/phone-qa/native-folded`. Публичный результат без серийного номера и личных путей: [folded-wallpaper-phone-inspection.json](folded-wallpaper-phone-inspection.json).

| Компонент в исследованной прошивке | Подтверждённая роль |
| --- | --- |
| `com.miui.miwallpaper`, WallpaperOS3 `6.3.2-flip-ALPHA-04251408` | Native image/video/sensor/MAML wallpaper engine; отдельные внутренние и внешние цели |
| `com.android.thememanager`, `3.0.5.14-global`, UID `android.uid.theme` | Пользовательские настройки, импорт/применение ресурсов и редакторы |
| `com.miui.aod`, `DEV-FLIP-2335.1.2.1-05070145`, UID `android.uid.system` | Отдельная AOD-система; не наш WallpaperService |
| `com.android.systemui`, MiuiSystemUI | Штатная внешняя блокировка/TinyKeyguard и управление отображением |

## Реальный native API и файловый барьер

Декомпилированный `MiuiWallpaperManager.java` содержит цели:

- `1`: внутренний home;
- `2`: внутренняя блокировка;
- `4`: внешний home;
- **`8`: внешняя блокировка**;
- `15`: все четыре. Для изолированного опыта `15`, `12` и `3` не использовать.

Есть `setMiuiVideoWallpaper(videoPath, thumbnail, which)` и вариант с параметром loop; тип ресурса — `video`. Есть также `setMamlWallpaper`, но он задаёт постер/тип, а не принимает произвольный PAG-файл или весь пакет XML-ресурсов. Клиент привязывается к экспортированному сервису `com.miui.miwallpaper.server.MiuiWallPaperControllerService`, action `android.service.wallpaper.WallPaperControllerService`. У сервиса нет manifest signature-permission на bind, но каждый защищённый Binder-метод проверяет права.

**Запись:** `MiuiWallPaperControllerService.setWallpaper3` вызывает `PermissionUtils.checkSetWallpaperPermission`. В этом APK проверяется только `android.permission.SET_WALLPAPER`. Это обычное Android-разрешение; считать весь native setter исключительно signature API было бы неверно.

**Чтение и backup:** `getMiuiWallpaperType`, `getMiuiWallpaperPath`, `getMiuiWallpaperPreview` и часть других методов требуют `hyper.permission.READ_WALLPAPER` либо системное/whitelist-приложение. В manifest `hyper.permission.READ_WALLPAPER` объявлено signature. Обычному приложению нельзя выдать его через `pm grant`. Наличие Shizuku не меняет подпись APK, хотя вызов из shell-процесса может получить другой результат проверки системного пакета.

**Главное препятствие:** штатный setter возвращает клиенту карту файловых путей, а затем клиент SDK сам копирует MP4 и thumbnail в эти пути. Это не выдача write `ParcelFileDescriptor` обычному приложению. В исследованном коде используются:

```text
/data/system/theme_magic/users/0/wallpaper/video/lock_wallpaper_video_small.mp4
/data/system/theme_magic/users/0/wallpaper/video/lock_wallpaper_thumbnail_small.jpg
/data/system/theme_magic/users/0/wallpaper/data/small_lock.xml
```

Точный первый путь формируется через `ThemeResources.THEME_MAGIC_PATH` и текущий user ID. На реальном телефоне native dump подтвердил цель 8, текущий и default тип `rotation_image`; small MP4/thumbnail отсутствуют. Служебные каталоги и `small_lock.xml` имеют mode `0777` и SELinux type `theme_data_file`, доступны для чтения/stat shell UID 2000. **Проверки `test -w` дали отказ для video/data каталогов и metadata-файла; `test -r` прошли.** Это конкретный контрпример предположению «0777 и Shizuku достаточно». Actual write/create не выполнялись, причину не подменяем проверенным SELinux trace, но прямой native SDK-copy через shell пока блокируется. Проверка `SET_WALLPAPER` сама по себе недостаточна. Изменение типа до возможности записать/откатить файлы способно оставить пустую блокировку.

Штатный сервер имеет FileObserver для каталога video и отдельный KeyguardVideoEngineImpl. Это нормальный путь постоянных обоев: после успешной установки ОС сама хранит ресурс и управляет воспроизведением, без нашего вечного foregroundservice и без необходимости держать Shizuku запущенным для каждого кадра. Этот результат пока является выводом из архитектуры, а не физическим тестом установки собственного ролика.

## Что дают штатные редакторы и темы

В Themes подтверждены exported-компоненты:

- `com.android.thememanager.activity.WallpaperDetailActivity`: action `miui.intent.action.START_WALLPAPER_DETAIL`, поддерживает MIME `video/*` и `image/*`;
- `com.android.thememanager.wallpaper.VideoDetailActivity`: action `miui.intent.action.START_VIDEO_DETAIL`;
- `com.android.thememanager.mine.settings.wallpaper.external.WallpaperExternalPreviewActivity`;
- `com.miui.keyguard.editor.CommonEditorActivity`.

`WallpaperExternalPreviewActivity` читает extras `pageSource` и `externalWallpaperPreviewPath`. В его изученном apply-пути есть bitmap/ImageMatrix и фотографический ресурс. **Это не подтверждение принятия cover MP4.** CommonEditorActivity дополнительно проверяет calling source и различает вызовы SystemUI/Themes; exported не означает свободный доступ ко всем веткам редактора.

Есть exported providers `com.miui.miwallpaper.keyguard.wallpaper`, `com.miui.miwallpaper.wallpaper`, `com.android.thememanager.aod_preview_provider`; часть остальных providers требует `miui.permission.USE_INTERNAL_GENERAL_API`. Ни один изученный manifest/provider пока не подтверждает публичную загрузку собственного внешнего PAG/MAML. В Themes объявлено signature-разрешение `miui.keyguard.editor.WRITE_EDITOR_FILE`. Предлагать `settings put` или `content call` с угаданными ключами как рабочий импорт нельзя.

MRC/MTZ может оказаться подходящим форматом для native MAML, но нужно отдельно подтвердить import/apply именно внешней блокировки на текущем EEA Themes. Обычный импорт темы не доказывает поддержку small-lock и может затронуть другие части темы. Подмена встроенных файлов `/system` или удаление DRM/signature-проверок не входят в rootless-вариант.

## Выбор подхода

| Вариант | Оценка и следующий шаг |
| --- | --- |
| MP4 → штатный пользовательский preview/apply | Самый удобный интерфейс, если фактическая прошивка предлагает внешнюю блокировку для своего видео. FAQ предупреждает, что это не поддерживается штатно; сначала осмотр UI, без автоматического Apply |
| Native `which=8` через фиксированный Shizuku helper | Интерфейс подтверждён на фактическом EEA APK, shell SET_WALLPAPER granted. Но write-access checks служебных путей отказали: прямой SDK-copy непригоден без другого gateway. Helper полезен для read-only диагностики/backup, а не обхода файловых ограничений |
| Native MAML/MTZ с нашими оригинальными PAG | Может сохранить события/реакции лучше записанного видео; внешняя точка импорта и разрешения ещё не найдены. Сейчас это менее готовый вариант |
| Обычный Android WallpaperService | Готов для стандартных живых обоев, но публичный WallpaperManager не предоставляет отдельную Xiaomi-цель `small-lock=8`. Нельзя обещать, что он попадёт на внешнюю блокировку |
| Статичный постер для внешней блокировки/AOD | Поддерживаемый запасной вариант для своего изображения. Он не переносит анимацию |
| Встроенные Xiaomi pets | Рабочая штатная анимация без порта ресурсов 17 Pro; полезна как контрольный образец поведения/отката |

Для первого native video опыта разумен короткий беззвучный MP4 H.264/AVC с JPEG-постером. [Android поддерживает AVC в MP4](https://developer.android.com/media/platform/supported-formats); точные дополнительные ограничения Xiaomi по длительности, размерам, bitrate и профилю в изученных методах не установлены. Не выдавать выбранные параметры экспорта за требования Xiaomi. Композиция должна соответствовать реальному cover `1208×1392`, учитывать камеры и штатные часы; alpha PAG нужно заранее смешать с фоном. MP4 не сохранит интерактивные реакции, динамические часы и переключение состояний.

## Lockscreen и AOD — разные режимы

KeyguardVideoEngineImpl запускает видео, когда блокировка видима и экран включён, и вызывает pause при скрытии/уходе со сцены. Переход к screen-off/AOD имеет отдельную ветку. AOD принадлежит `com.miui.aod`; это не гарантия круглосуточного видео. Требуемое поведение лучше формулировать так: **питомец оживает на пробуждённой внешней блокировке, штатные замок/разблокировка/сон/AOD остаются у ОС**. После возможности native установки можно отдельно проверить однократное проигрывание и `loop=false`.

## Минимальный безопасный осмотр следующего подключения

До любого изменения сверить явно выбранный серийник устройства, модель `ruyi` и build. Ниже команды только читают состояние; dump сохранять локально, без публикации чужих сообщений/личных изображений:

```powershell
$flipPhoneSerial = "YOUR_MIX_FLIP_SERIAL" # из adb devices; никогда не выбирать устройство неявно
adb -s $flipPhoneSerial shell getprop ro.product.device
adb -s $flipPhoneSerial shell getprop ro.build.version.incremental
adb -s $flipPhoneSerial shell pm path com.miui.miwallpaper
adb -s $flipPhoneSerial shell pm path com.android.thememanager
adb -s $flipPhoneSerial shell pm path com.miui.aod
adb -s $flipPhoneSerial shell dumpsys package com.miui.miwallpaper
adb -s $flipPhoneSerial shell dumpsys package com.android.thememanager
adb -s $flipPhoneSerial shell dumpsys package com.android.shell
adb -s $flipPhoneSerial shell dumpsys wallpaper
adb -s $flipPhoneSerial shell dumpsys activity service com.miui.miwallpaper/.server.MiuiWallPaperControllerService
adb -s $flipPhoneSerial shell ls -ldZ /data/system/theme_magic /data/system/theme_magic/users /data/system/theme_magic/users/0 /data/system/theme_magic/users/0/wallpaper /data/system/theme_magic/users/0/wallpaper/video /data/system/theme_magic/users/0/wallpaper/data
adb -s $flipPhoneSerial shell ls -lZ /data/system/theme_magic/users/0/wallpaper/video/lock_wallpaper_video_small.mp4 /data/system/theme_magic/users/0/wallpaper/video/lock_wallpaper_thumbnail_small.jpg /data/system/theme_magic/users/0/wallpaper/data/small_lock.xml
adb -s $flipPhoneSerial shell cmd device_state state
adb -s $flipPhoneSerial shell cmd display get-displays
```

Permission-denied от `ls` — результат исследования, а не повод делать chmod, менять SELinux или системные права. Если actual dump показывает другой user/path, проверять только точный путь из него.

Далее можно снять штатную блокировку/AOD и вручную открыть Settings → External screen lock screen, не применяя оформление. Проверить наличие своего видео и цели «внешняя блокировка», а также сохранённые штатные pets. Фактические APK можно `adb pull` по путям `pm path` и сравнить с локальными; это чтение, не установка donor APK.

Этот минимальный осмотр уже выполнен на EEA телефоне: APK сравнены, цель 8 и текущий/default `rotation_image` получены через native service dump, write-access отказал. `small_lock.xml` прочитан только как XML-конфигурация и сохранён в игнорируемую локальную папку. Изображения/ролики текущих обоев не копировались. Native read-only Binder probe подготовлен отдельно в `work/folded-research/native-probe` (source, build script, DEX и build hashes), затем отдельно запущен в GET-only режиме; bind завершился ошибкой `Unable to find app for caller ... Transport` на стороне AMS. Ни один wallpaper getter не выполнился. Это сбой идентификации/транспортировки caller при bind, не измеренный отказ wallpaper permission. Он использует настоящий UID 2000 и Context `com.android.shell`, bind точного native сервиса и только пять типов getter-методов; timeout 15 секунд, unbind/exit. Подмена системной идентичности и setters исключены из исходника.

Следующий необязательный маленький native probe должен **только читать**: bind exported controller service, `getMiuiWallpaperSdkVersion`, `getMiuiWallpaperSdkVersionCode`, `getMiuiDefaultWallpaperType(8)`; затем документировать permission-result read методов. На этом шаге `setWallpaper*`, `clearWallpaper*`, `onStartCommand` update/clear и прямую замену файлов не вызывать. Binder service endpoint не обязательно зарегистрирован в системном ServiceManager, поэтому угаданный `service call wallpaper` здесь не заменяет app bind.

Только после выяснения доступа: получить полный native backup цели 8 (тип/метаданные/preview/video или исходный preset/resource и настройки), показать проверяемый rollback, затем один короткий опыт собственного MP4 через родной setter. Проверить штатные unlock, camera, clock, fold/unfold, повторное пробуждение, AOD, перезагрузку и энергопотребление. Если полного отката не получается, ограничиться экспортом ролика и штатным preview до подтверждения безопасного применения.

### План восстановления текущего `which=8`

Текущий native dump называет состояние default `rotation_image`. Для полного точного возврата нужны: metadata `small_lock.xml`; два orientation-ресурса `lock_wallpaper_small_0.jpg` и `lock_wallpaper_small_180.jpg`; все параметры which 8 из dump (clock style/type, blur/dark/doodle, pending/last package и предыдущий тип); идентификатор выбранной штатной внешней темы и связанные native editor настройки. AOD отдельно не менять: установка видео на lock не должна обещать замены AOD.

Сейчас сохранены только текстовые metadata/dump; это **не полный backup**. Нельзя считать один `clearWallpaper(8)` точным восстановлением пользовательского внешнего оформления: default resource и выбранные параметры могут различаться. После отдельного разрешения на локальный backup изображений можно проверить их хэши, размеры и связать с metadata, без публикации файлов. Если gateway умеет применить своё видео, он должен уметь восстановить эту rotation-image пару и параметры штатным ресурсным механизмом. Прямой возврат XML-файла не равен обновлению native cache/SystemUI: нужны родной apply/notification flow или подтверждённое native переключение. Пока write-access отказал и gateway не найден, никакого setter/op смены типа не выполнять; read-only probe сам по себе не обеспечивает откат.

## Локальные доказательства

- `work/folded-research/provenance.json`: хэши выбранных firmware APK.
- `WallpaperOS3-manifest.txt`: native services/providers и signature read permission.
- `MIUIThemeManagerGlobal-manifest.txt`: UID theme, exported editors и video MIME-фильтр.
- `MIUIAod-manifest.txt`: отдельный UID/system AOD.
- `MiuiWallpaperManager.java`: цели 1/2/4/8, `setMiuiVideoWallpaper`, клиентская запись файлов.
- `MiuiWallPaperControllerService.java`: Binder permission checks setter/read methods.
- `PermissionUtils.java`: SET_WALLPAPER против signature/whitelist чтения.
- `MiuiWallpaperPathUtils.java`: video-small/thumbnail/data paths.
- `MiuiWallpaperManagerService.java`: FileObserver и native state metadata.
- `WallpaperExternalPreviewActivity.java`, `CommonEditorActivity.java`: реальные extras и ограничения callers.
- `KeyguardVideoEngineImpl.java`: видимость, пауза и screen-off/AOD ветки.

Декомпиляция помогает установить интерфейсы, но сложные восстановленные условия могут содержать ошибки jadx. Для будущей реализации сомнительные branches надо сверять с DEX/фактическим APK и результатами read-only probe на EEA телефоне.

## Gateway-анализ актуального Themes 3.0.6.8: импорт есть, цель 8 не подтверждена

Дополнительно исследован **локально, без запуска UI или setter на телефоне**, APK Themes `3.0.6.8-global`, полученный с текущего EEA устройства: SHA-256 `ab8e25a33b63a8c145a289c478c86c5893f37bbafe755630460bc3efda3f57c7`. Это уточнение к старой firmware-версии 3.0.5.14 выше. Декомпилированы выбранные реальные class definitions из classes6/7/8/11.dex; исходные APK/DEX/Java остаются в игнорируемом `work/folded-research/gateway-current`, не в публичном Source ZIP.

**Результат:** Themes действительно может сам получить MP4 через `content://` и скопировать его своим UID. Однако в прослеженном публичном видео preview/apply путь внешней блокировки `which=8` не найден: lock применяет 2, home 1, both 3. Поэтому этот gateway решает передачу байтов системному приложению, но пока не решает установку на внешнюю блокировку. Прямой клиентский SDK-copy из UID shell тоже нельзя считать рабочим: фактическая read-only проверка показала R=yes/W=no для native small-lock путей, несмотря на mode 0777. Точная причина запрета записи не установлена тестом `test -w`; SELinux — правдоподобная причина, а не доказанный диагноз.

### Реальный MP4 import через OEM Activity

В актуальном manifest `com.android.thememanager.wallpaper.VideoDetailActivity` exported=true, без manifest permission. `onCreate` разбирает action `miui.intent.action.START_VIDEO_DETAIL` и **строковый extra `path`**; из него создаёт VideoInfo.path/previewPath. Для `content://` `VideoDetailFragment.Z2()` вызывает `VideoDetailFragmentVM.v(uri)`. Coroutine `copyVideoFromUri` передаёт URI в `x3.i.j(uri)`, а `x3.i.i(uri,targetPath)` открывает `ContentResolver.openInputStream(uri)`, копирует в temp и переименовывает в файл Themes. Это действительный system-owned copy, а не предположение по MIME-фильтру.

Протокол будущего **preview-only** опыта из нашего foreground Activity:

```java
Intent preview = new Intent("miui.intent.action.START_VIDEO_DETAIL");
preview.setComponent(new ComponentName("com.android.thememanager",
        "com.android.thememanager.wallpaper.VideoDetailActivity"));
preview.putExtra("path", exportedMp4Uri.toString());
preview.setDataAndType(exportedMp4Uri, "video/mp4");
preview.setClipData(ClipData.newRawUri("Flip Pets video", exportedMp4Uri));
preview.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
// Только открыть preview. Никакого автоматического Apply.
startActivity(preview);
```

URI должен выдавать наш узкий read-only provider только для подготовленного ролика: exported=false, grantUriPermissions=true, без экспорта личных фото/общего дерева files. Сам extra `path` не выдаёт URI permission; data/ClipData нужны для стандартного временного grant. После завершения copy/preview выдачу можно закончить. Это соответствует [официальному механизму обмена файлами Android](https://developer.android.com/training/secure-file-sharing/share-file) и [FLAG_GRANT_READ_URI_PERMISSION](https://developer.android.com/reference/android/content/Intent#FLAG_GRANT_READ_URI_PERMISSION). В APK0.7 такого export provider/native preview пока нет; показанный протокол не был запущен на устройстве.

Ограничение существенное: в `VideoDetailFragment.h.doInBackground` действия ведут в `c0.h(path)` для lock, `c0.m(false,path)` для home и `c0.m(true,path)` для обоих. Эти методы вызывают `v.n0(...,2/1/3)`, затем `v.o0` и native SDK `q.N1`; `q.f.A(which)` сохраняет переданный target без превращения 2 в 8. Объявленный `extra_apply_flag` в изученном Activity только записывается helper-методами и не читается для apply. Добавлять ему 8 или придумывать `which=8` extra нельзя: доказанного соответствующего consumer нет. UI выбора внешней цели для этого собственного MP4 также не подтверждён.

### Почему остальные найденные входы пока не подходят

| Вход актуального APK | Что реально делает | Вывод для собственного cover MP4 |
| --- | --- | --- |
| `WallpaperDetailActivity`, START_WALLPAPER_DETAIL, MIME video/* | Принимает file/content URI и создаёт Resource; видео перенаправляется в общий wallpaper workflow | MIME доказывает чтение ресурса, но не isolated target 8; безопасное внешнее apply не подтверждено |
| `WallpaperExternalPreviewActivity` / Fragment | Фото bitmap, ImageMatrix, crop/rotate; VM называет вход photoPath и копирует ресурс из album | Реальный внешний photo editor, не найден MP4 decoder/apply protocol |
| `AodPreviewProvider`, authority `com.android.thememanager.aod_preview_provider` | `call/query/insert` возвращают null, `update/delete` 0; helper с именем setOutLockWallpaperPath не вызывается из call | Не рабочий скрытый setter; похожее имя метода не является контрактом |
| `WallpaperServiceProvider` | Единственный изученный call notify_superwallpaper_restore_default; проверка callingPackage и signature API permission в manifest | Это уведомление об откате, не upload/apply |
| `com.miui.miwallpaper.keyguard.wallpaper` | Перед call проверяет whitelist SystemUI/Themes/Gallery/Settings/Launcher/Carousels/InCall; preview/authority/status/read | Flip Pets и shell не в whitelist; MP4 import отсутствует в разобранном switch |
| `com.miui.miwallpaper.wallpaper` | Проверки поддержки и сведения о Super Wallpaper | Не file/FD upload endpoint |
| Native Binder `IMiuiWallpaperManagerService` | setWallpaper/setWallpaper2/setWallpaper3 возвращают Map; `ParcelFileDescriptor` есть у read-preview методов | Не найден writable FD/URI consumer для target8: SDK возвращает пути, затем **клиент** пишет файлы |
| `CommonEditorActivity` | Exported редактор с отдельной проверкой источника вызова; manifest content-hosts Themes/Gallery | Нельзя выдавать экспортированность за возможность передать произвольный MP4/template8; обход caller checks не входит в rootless-порт |

### Что проверять дальше

1. Сначала read-only Binder probe фактической WallpaperOS3: готовность SDK, разрешённые getter-методы, тип target8. Это полезно для точного backup/rollback, но успешный bind/getter не снимает запрет клиентской записи.
2. Без Apply посмотреть собственный MP4 в настоящем Themes preview через узкий URI grant. Если интерфейс предлагает только внутренний home/lock, остановиться; folding телефона само по себе не меняет hardcoded target2 на 8.
3. Продолжить поиск **именно** system-owned consumer, одновременно принимающего наш URI/FD и isolated external-lock target8, либо штатного импортера external template/resource. Нужно найти выполняемый read/copy/apply код и доступную exported точку, а затем проверить откат. Публичный MAML/MTZ import внешней цели пока также не доказан.

Пока такого consumer нет, native folded animated wallpaper остаётся исследовательским направлением, а обычный folded экран Xiaomi/AOD сохраняется. Rootless открытый режим0.7 работает отдельным Activity и не должен подменять этот native результат. Наличие полного root не делает перенос template автоматически готовым: требуются совместимость формата, резервная копия и отдельные испытания. SELinux/chmod, подпись Xiaomi, выдача себя за whitelist package и запуск внутри UID Themes здесь не используются.

Уточнение отдельного read-only Binder probe: сбой пути bind/AMS до успешной доставки Binder необходимо отделять от отказа permission конкретного wallpaper getter. Такой транспортный сбой не доказывает ни отсутствие READ_WALLPAPER, ни недоступность SET_WALLPAPER; методы setter не проверялись. Native custom folded apply остаётся не реализованным и в готовящемся выпуске0.8.

Финальный статус выпуска0.8: завершается после эмуляторных проверок; на физическом телефоне остаётся0.7. Нативные сложенные анимированные обои не установлены, новых getter/setter/backup опытов для завершения выпуска не проводится.

## Дополнительный кандидат: собственный PAG через настоящий tiny-editor AOD

После анализа Themes найден отдельный, более подходящий путь в фактическом `com.miui.aod` (DEV-FLIP-2335.1.2.1-05070145). Это **кандидат нативного импорта, ещё не доказанная установка**. На телефоне открыт штатный внешний редактор без Apply; локальный анализ кода и JSON ниже не меняет приложение/телефон.

В AOD exported `com.miui.tinykeyguard.editor.HomepageActivity` (action `miui.tinykeyguard.editor`) и `com.miui.tinykeyguard.editor.edit.EditActivity` (action `miui.tinykeyguard.editor.EDIT`). Это отдельный outer editor, а `com.miui.keyguard.editor.EditorActivityForSettings` — общий редактор, работающий также с другим settings JSON. В tiny `EditActivity.f()` есть настоящий вход **строковый extra `param_template_item_json`**, который Gson читает как `com.miui.tinykeyguard.editor.data.template.TemplateItem`.

Для своей анимации код знает `clockInfo.templateId="ai_pets"`, `pets.petCategory=2`, `pets.aiPetsData.resourcePag`, `resourcePic`, `firstFrameCoordinateAxes`, `lastFrameCoordinateAxes`, `bizId`. `TinyEditorAiPetsView.refreshTemplateItem` строит WallpaperInfo0/180 из собственного постера, а `TinyEditorPetsPagView` создаёт `AiPetsPagView`: тот действительно читает переданный PAG path, вместо выбора только шести ROM pets по petType. Имя ai_pets здесь обозначает поддержанный native render/template-формат; облачную AI-генерацию мы не вызываем.

При подтверждении штатного редактора `EditViewModel` вызывает native `TemplateApiImpl.applyTemplate`: сначала `fileCopy`, затем `saveCurrentTemplateToDatabase` в `current_tiny_keyguard_info`, затем история. Native copy копирует AI_PAG в `/data/system/theme_magic/users/<user>/wallpaper/tiny_keyguard/<timestamp>/AI_PAG` и меняет resourcePag на новый путь. В отличие от прямого shell SDK-copy, **писатель здесь системный AOD**. Условие успешного копирования проверено дополнительно в DEX, потому что JADX ошибочно восстановил проверку null: offsets0a06/0a0e пропускают null/blank,0a1e сохраняет успешный новый путь.

Вход файлов **не content URI**: `TemplateFilePathGenerator.copyFile` проверяет `new File(source).exists/length`, затем `FileUtils.copyFile`. Для собственного PAG и постера нужен обычный читаемый путь, например отдельная папка в `/sdcard/Download/FlipPetsNative`, без личных фото и без записи в `/data/system` от shell. Actual manifest подтверждает sharedUserId=`android.uid.system` и WRITE_SECURE_SETTINGS; локальный package dump показывает MANAGE_EXTERNAL_STORAGE granted=true у фактического shared UID, хотя AOD сам не перечисляет его в своём uses-permission. Это сильное подтверждение доступа к shared storage, но успешное чтение именно staged-файла/SELinux/app-op необходимо подтвердить preview. Давать shell UID системного приложения или менять permissions/secure settings от нашего кода не требуется.

Геометрия отличается от нашего PetStage. Native AiPetsPagView создаёт композицию1208×1392, но добавляет исходный PAG только с **translation matrix, без scale**. FrameCoordinateAxes — bbox первого/последнего кадра с полями leftX/leftY/rightX/rightY; его clamp-алгоритм учитывает размеры PAG/постера и обе ориентации0/2. У исходного Charlie pag_0 размер976×596: с таким же постером и bbox0,0,976,596 чистый пересчёт даёт translation232,796 в обеих ориентациях. Файл занимает нижнюю часть canvas; камерную безопасность и совпадение картинки/постера всё равно надо увидеть. Full-cover постер1208×1392 меняет этот расчёт; axes не дают произвольного уменьшения/увеличения файла. Это не перенос всей reactive-цепочки17Pro: native AI path играет один выбранный PAG.

Подготовлен только локальный ignored preview fixture с новым собственным bizId: неизменённый Charlie PAG, PNG-постер из его галерейного thumbnail в976×596 и JSON на основе штатного tiny pet config. Постер тестовый, не точный decoded PAG frame. Apply не запускался; результат предпросмотра описан ниже. JSON wallpaperInfo0/180 допускает null именно в ai_pets import branch: редактор заменит их из resourcePic. FrameCoordinateAxes и aiPetsData должны быть непустыми; native код делает checkNotNull и читает размеры постера.

**Пока только preview/Back.** Снимок текущего `current_tiny_keyguard_info` совпал со схемой TemplateItem, которую читает native loadCurrentTemplate, и содержит исходное built-in splicing-оформление. Его можно передать тем же штатным editor JSON-входом как restore-preview, без прямого settings write. Однако Confirm повторно копирует ресурсы и изменяет timestamp/историю; это кандидат семантического восстановления, а не проверенный точный rollback. Отдельного export/import-save-only без применения не найдено: createHistoryItem вызывается после saveCurrentTemplate. `rollbackAiPetsByBizId` удаляет совпавшие элементы и выбирает первый оставшийся; он не является восстановлением произвольного снимка. CLEAR_ALL_TEMPLATES удаляет историю и для отката не подходит. Перед любым Apply нужно подтвердить возврат через штатный UI и неизменность обоих settings JSON после preview/cancel.

Отдельный GET-only transport впоследствии удалось получить через IActivityManager.peekService: UID2000 получает sdk300341 и default8=`rotation_image`, но protected type/path getters возвращают null. Это не обещает writable FD или полный backup. Старый неудачный bind через AMS, описанный выше, остаётся отдельным транспортным опытом.
## Текущие результаты preview и отложенный TODO

По уточнению пользователя отдельно отложен **нативный lockscreen сложенного телефона**. Позднее после rootless-аудита отдельно отложено продолжение rear pet на раскрытом телефоне при любом выключении main обычной кнопкой питания: пользователь разрешил оставить сложный сценарий на потом. Новые tiny-editor/Apply и power-override опыты не проводятся. Описанный tiny-editor путь **не считается работающей установкой анимированных обоев** и не входит в реализованный функционал Flip Pets0.9.1.

После подготовки собственного Charlie PAG/постера родительский агент открыл штатный tiny-editor preview с `param_template_item_json`. JSON принят, своё изображение Charlie видно; captured preview выглядит преимущественно как плоский постер. **Проигрывание самого PAG не подтверждено. Apply не нажимали.** Значения `current_tiny_keyguard_info` и `all_tiny_keyguard_info` после preview остались byte-for-byte неизменными. Это подтверждает принятие preview-контракта и сохранение текущего выбора в данном опыте, но не подтверждает native AI_PAG copy/apply, безопасный откат или персистентную анимацию.

Публичный контракт/наблюдения без серийного номера, личных путей и settings snapshots: [native-tiny-preview-evidence.json](native-tiny-preview-evidence.json). Локальные prepared fixture, текущие/исторические настройки, выбранная декомпиляция и class-only DEX disassembly остаются в игнорируемых research/phone-qa папках. Системная staging-папка для своего PAG/постера будет убрана родительским агентом; пользовательские обои и история не применялись/не удалялись.

При возобновлении:

- Подтвердить полный native backup и точный/семантический rollback текущего splicing-оформления **до Apply**; сохранить историю и отдельно проверить, что restore-import не создаёт нежелательные копии/изменения. Captured TemplateItem совпадает с native schema, но это ещё не доказательство восстановленного результата.
- Разобраться с плоским preview: действительно ли loaded PAG играет, как native lifecycle/start/freeze работает, и насколько совпадает alpha со сценой. Подготовить точный кадр-постер вместо тестового thumbnail.
- Проверить native PAG translation/геометрию и камеры в обеих ориентациях. AiPetsPagView не масштабирует raw donor; FrameCoordinateAxes не являются свободной transform matrix. Изменения нашего PetStage не решают расположение в системном редакторе.
- Только после подтверждённого отката провести отдельный опыт system-owned copy/выбора/анимации; затем защищённая блокировка, unlock, пробуждение, складывание, AOD и reboot. Нативную per-frame интерактивность17Pro нельзя выводить из того, что editor принимает один PAG.
- Исследовать собственный template/file-формат и несколько оригинальных состояний после возобновления задачи. MAML/template/sensor и одиночный AI-PAG — разные пути; sensor-video в изученном Themes применяет группы main targets, а не доказанную независимую внешнюю цель8.
- **Отдельно отложено после rootless-аудита:** rear pet на раскрытом телефоне при main locked/off с ограниченным временем показа и обычной кнопкой питания. Native preview не доказывает этот сценарий; отдельное питание панели при PMS Awake не доказывает реальный Sleep. [Исследование независимого питания](independent-display-power.md) фиксирует source provenance, аппаратный факт и ограничения. Возвращаться к этому направлению отдельно от folded native import.