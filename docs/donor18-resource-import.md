# Ресурсы Xiaomi18Pro: импорт без дублирования

**Исследование возобновлено04.10.2026 после новой инструкции пользователя «Тяни из18про».** Прежняя отсрочка отменена для загрузки/исследования. Выпуск1.0 остаётся baseline; следующий выпуск1.1 рассматривается только при наличии действительно новых совместимых ресурсов. Первоначальный read-only аудит завершён; после проверки новых ресурсов выполнен выборочный импорт для1.1.

Источник исследования — официальный OTA `hongkong-ota_full-OS4.0.15.0.XFRCNXM-user-17.0-6aad32ed35.zip`, [Xiaomi CDN](https://bigota.d.miui.com/OS4.0.15.0.XFRCNXM/hongkong-ota_full-OS4.0.15.0.XFRCNXM-user-17.0-6aad32ed35.zip). Уже прочитанная OTA metadata указывает `pre-device=hongkong`, SDK37 и внутренний incremental `17OS4.0.260925.013226048.QCPECN.S`; это отдельно от публичного имени версии. Загрузка выбранных разделов ещё не означает проверенный полный flashable ZIP.

Выбранные разделы проверены по payload operation hashes, partition size и SHA256. Из них выполнен выборочный импорт для1.1, описанный ниже; исходные APK донора не устанавливаются на MIX Flip.

## Историческая точка остановки и возобновление

Ниже snapshot checkpoint на момент прежней остановки. Загрузка уже возобновлена из него; текущий прогресс нужно читать из `.ranges.json`, не из этих исторических чисел. В ignored `work/firmware` сохранены:

- `hongkong-ota_full-OS4.0.15.0.XFRCNXM-user-17.0-6aad32ed35.partial.zip` — разреженный **неполный** ZIP. Его логический размер12 318 005 426B не означает, что все байты скачаны.
- Соответствующий `.partial.ranges.json`:16 640 завершённых chunks по262 144B (256KiB),4 362 076 160B, около4.0625GiB checkpointed ranges. Для объединения product+system_ext требуется20 561 chunks; checkpoint включает также служебные диапазоны, поэтому простой процент этих двух чисел не является проверкой разделов.
- `hongkong-partition-plan.json`, `hongkong-metadata.txt`, `hongkong-payload_properties.txt.txt`. SHA256 payload metadata сверен downloader с `METADATA_HASH=jTPDhEq9RsMeblfMxie2J0RsuGM+CoFNlMSTA0r73EM=`. Сама OTA metadata text имеет SHA256 `c0f345141d17ce06c167511a2c6dae46f9ff4446670b5d9b7dae22def1989f57`; это отдельные хеши разных данных.

**На прежней точке остановки полный ZIP и итоговые product/system_ext partition SHA ещё не были проверены.** Checkpoint подтверждает получение диапазонов по протоколу загрузчика; hash всей partition будет проверен только после завершения выбранных диапазонов и extraction. Не использовать `.partial.zip` для прошивки и не помечать его как verified firmware.

## Что сохраняется

`work/prepare_donor18.py` читает текущий каталог, не пересоздаёт старые entries и не сортирует их. Существующие id, compositions, duration/playback metadata и настройки сохраняются. Обычный `prepare_catalog.py` здесь повторно не запускается: он пересоздаёт каталог из прежних двух источников.

Сохранённый baseline1.0 содержит30 оформлений,170 ссылок на клипы и170 разных путей. Сравнение байтов даёт **142 уникальных PAG/MP4 SHA256**. Это разные показатели: номер сценария и название файла не доказывают новую анимацию. Старый каталог на этом этапе не сокращается.

## Правила новизны

- Полностью совпадающий набор media SHA256 считается source alias. Новый каталог entry и новый animation count для него не создаются, даже если OTA/MRC UUID, metadata или версия отличаются. Отличия MAML остаются исследовательским фактом.
- При частичном совпадении повторный media payload использует уже существующий asset path. Новый файл копируется только для нового SHA256; новый вариант MAML может ссылаться одновременно на старые и новые состояния.
- `newUniqueMedia` считается отдельно от `mediaReferencesAfterImport` и количества оформлений. Одинаковые байты внутри разных сцен/питомцев также не повышают unique count.
- Копируемые PAG/MP4 остаются побайтно оригинальными. Манифест MAML и SHA MRC, каждого media и используемого thumbnail фиксируются. Неизвестные состояния или native effects не переименовываются в поддержанную реакцию без кода-основания.

## Совместимость поведения

Оригинальное MAML finite hold принимается для известных классических семейств только при `PagView loop=1` и `onComplete→FrameRate0` без нового play. Такие семейства сохраняют классический prefix (`bird-hongkong` и т.п.). Для reactive scenes contract schema2 сравнивает полные Function/Trigger/ExternalCommands command trees, event/state indices, If/Loop ancestry, play/pause targets, delays, callback links и транзитивные state bindings с уже используемым MAML. Требуется pag_0..15 и только известный дополнительный nfc_pin_show; иные state files блокируются до review. Это консервативная проверка: неподтверждённое эквивалентное поведение также может быть отклонено. Новые условия/числовые mapping, конечный playback неизвестного семейства и видео сначала остаются в research: текущий Java player не получает выдуманный loop.

Этот фильтр подтверждает только сопоставление локального поведения. Он не запускает Xiaomi MAML engine, не переносит автоматически backend18Pro, secure lockscreen, датчики донора или независимую power-group политику.

## Использование импортера

Downloader уже возобновлён родительским агентом. Команды read-only extraction/plan выполняются только после его image-ready сигнала и hash evidence. Selective apply ниже описан как будущий отдельный шаг, сейчас не разрешён.

После получения `product.img`, его `product.verified-extraction.json` и EROFS listing:

```text
python -X utf8 work/prepare_donor18.py --image work/images/hongkong/product.img --listing work/research/hongkong-product-list.txt
```

Это извлекает только rear-screen content/meta/preview в ignored `work/extracted/hongkong/rearscreen` и записывает там `import-plan.json`. Указанный image предварительно сверяется с partition proof. Сам каталог и public assets при планировании не изменяются.

Выбор проверенного MRC и применение:

```text
python -X utf8 work/prepare_donor18.py --select MRC_UUID --apply
```

Без `--select` применяются все совместимые кандидаты из плана. `--apply` требует точный официальный source URL и verified partition evidence. Thumbnail берётся из реального built-in preview; его resample в WebP — обработка галерейной картинки, не новый animation frame. Если native preview не найден, применяется только подготовленный путь проверки реального кадра; временный `--allow-missing-thumbnail` не означает завершённую галерею. Original archives, APK, firmware и private dumps остаются ignored. Публичными становятся только выбранные app assets, соответствующий MAML и `work/research/hongkong-resource-provenance.json`.

## Отдельная проверка Charlie

Новый Charlie следует сравнить по SHA каждого состояния с17Pro, а не только по названию. Если SHA совпадает, срез гребня нельзя считать исправленным новой прошивкой. Если файлы изменились, нужны реальные размеры, крайние позы и последние действительные кадры; `.98` не является универсальным последним кадром. Сравниваются alpha/внутренние masks/child offsets исходного PAG и наш стабильный transform. Outer padding уже не восстановил отсутствующие пиксели старого материала. Переход на произвольную позу для скрытия среза не выдаётся за перенос поведения18Pro.

## Проверки импортера

Восемь synthetic filesystem tests в `work/tests/test_donor18_import.py` проходят: finite hold, отказ неизвестной конечной политики и indirect completion replay, ZIP path traversal, повторное использование общего clip/alias/no baseline mutation, отказ apply до provenance, а также обнаружение изменения event indices/actions/delays/conditions/dependent constants/callback links. Они проверяют импорт данных, не декодирование Xiaomi artwork, не HyperOS и не реальный телефон. Новые resource/runtime QA выполняются отдельно на окончательном APK.

## Точные шаги продолжения для следующей версии

1. Работать из `E:\FlipPets`; сохранить существующие `.partial.zip`, `.ranges.json` и partition plan вместе. Не удалять checkpoint и не выдавать длину разреженного файла за downloaded bytes. Проверить, что downloader всё ещё использует тот же source URL, archive size и совместимый chunk size.
2. Возобновить только после возвращения пользователя к задаче: `python -X utf8 work/fetch_donor18.py --partitions product system_ext --workers 8`. Число workers можно уменьшить при повторных CDN timeout; это не меняет source/hash-проверку. Скрипт пропускает checkpointed ranges, сверяет payload metadata, проверяет operation/final partition SHA и создаёт `work/images/hongkong/product.verified-extraction.json` и аналогичный system_ext proof. При hash mismatch остановиться; не писать provenance-флаги вручную.
3. После verified partition создать listing без полного распаковывания: `work\tools\erofs\extract.erofs.exe -i work\images\hongkong\product.img -p > work\research\hongkong-product-list.txt`. Проверить реальные rear-screen content/meta/preview пути; если формат или расположение изменились, адаптировать extractor до копирования public assets.
4. Запустить приведённый выше **plan** `prepare_donor18.py --image ... --listing ...`. Проверить каждое решение: exact alias, partial reuse, unique hash delta и неподдержанные MAML state mapping. Сравнить новые XML с17Pro, включая finite hold/reactive actions и Charlie. APK/native effects исследовать локально отдельно; на телефон APK донора не устанавливать.
5. Для выбранных реально новых ресурсов подготовить gallery thumbnail, проверить размеры/последние кадры/alpha и только затем выполнить `--select UUID --apply`. Сохранить source hashes и MAML; не запускать старый `prepare_catalog.py` поверх изменённого каталога. Если новых animation SHA нет, так и сообщить, без повышения counts из-за18Pro metadata.
6. После интеграции отдельно измерить длительности новых клипов, проверить реальные state mapping и geometry, обновить QA-counts по фактическим сценариям. Сборка, emulator/physical проверки и Source/evidence packaging должны относиться к новому точному APK SHA; восемь importer tests не заменяют эти проверки. Сохранять rootless fold/lock/sleep политику по умолчанию.

## Фактические результаты read-only аудита после возобновления

Оба раздела уже извлечены и проверены: product SHA256 `f63831fadeddfd4b52407ff22e02ac8d17cce6ceb474c951c4fc13c214d09f63`, system_ext `bd32916b4010f90ebaa077ef8685b9c6a84b57e0416e4645f6bae3bf072e239d`. Operation hashes/final partition hashes подтверждены downloader; полный sparse ZIP по-прежнему не verified. Машиночитаемый итог: [hongkong-readonly-findings.json](../work/research/hongkong-readonly-findings.json).

В41 MRC:16 exact media-set aliases,2 набора только из уже имеющихся байтов,20 без PAG/MP4,3 группы новых media с отдельной политикой. Из13 новых ссылок в этих группах **9 уникальных media SHA**, потому что четыре p_carp файла повторяются в multi-ratio archive. Автоматический compatibility plan пока не импортирует ни одного entry; это не отсутствие полезных новых файлов. Проверка против всех локальных17Pro/archived MRC также не нашла эти9 SHA.

| Реальный материал | Уникальная новизна | Native policy и предлагаемый перенос |
| --- | --- | --- |
| Vortex core,119f090b… | 1 MP4 | `VideoCommand config loop=1 scaleMode=2`, play при normal resume, pause при inactive/AOD. Это фон под отдельными PNG стрелками, датой и батареей; один MP4 нельзя называть полным переносом native часов. |
| Butterfly carp,6eca3137… | 4 PAG p_carp | Те же байты, что pag_488x298 в следующем archive. Не создавать вторую копию в gallery/count. |
| Butterfly carp,e23e7933… | 4 новых hongkong456 +4p_carp488 +4старыхq_carp452 | Один набор с явными layout variants. Source ratio<1.55 выбирает456,1.55–1.61→452,>=1.61→488. В source это не event states питомца и не непрерывный repeat одного файла. |
| SubscreenCenter `assets/pin_show.pag` | Ещё1 PAG вне MRC | НовыйSHA566424b867d98bf5e84f8eb8afa6f368332fb7877b5a7378503943358ae159b2. `M.j.run case7` загружает его через SmartAssistantPanel. Название файла не доказывает NFC, разблокировку или универсальный pet appearance trigger. |

Carp init выбирает random0..3. В awake/non-paused `onUpdate` после progress689/719 для сцен0/1,570/600 для2,566/596 для3 устанавливает is_hidden и запускает fade-out500ms. Callback выбирает другую сцену random с максимум10 попытками, ставит progress0/play и возвращает alpha255 за300ms после100ms задержки. Pause ставит progress1/pause/FrameRate0; AOD допускает завершение и hold. Для адаптации нужен explicit scene-cycle policy с этим переходом, а не `repeatCount0`. Физический камерный clearance и исходные PAG размеры подтвердит отдельный render probe; ratio в MAML не является измерением MIX camera cutout.

Charlie12 PAG сравнивались по **номеру состояния и байтам**, все совпали с текущим bird-pandora. Новый донор не исправляет исходный срез гребня. Новых уникальных reactive pets/states в этих MRC не найдено.

В APK16 embedded ZIP templates `smart_assistant` (alarm/music/timer/phone/live_update и другие): MAML и PNG, без PAG/MP4 внутри. Они могут дать оригинальный source UI для отдельного будущего native-style card исследования; наличие ZIP не переносит Xiaomi backend/права/data-binding автоматически. Native thumbnail metadata указывает generic preview filename, но embedded/extracted preview не найден: для выбранных новых сцен ещё нужны настоящие rendered-frame gallery thumbs.

Рекомендация для следующего шага: выбрать одну Butterfly carp adaptation с4native hongkong scenes и вариантом488 без duplication; отдельно Vortex background/полные часы по доступной реализации. Pin effect — только явно обозначенный просмотр после render проверки и уточнения callback lifecycle. Baseline1.0 IDs/defaults, source media bytes и folded/lock/sleep политика сохраняются. Apply, runtime и catalogue в этом read-only аудите не менялись.

## Выборочный импорт1.1

`prepare_donor18_port.py` проверил исходный каталог1.0 по SHA, ZIP CRC/source archive hashes, оба partition proofs и реальные PAG/video probes, затем добавил3 entries/6 unique media и29 оригинальных clock PNG. `hongkong-selected-port-provenance.json` фиксирует каждый archive/member/destination hash и rendered-thumbnail lineage. Первые30 entries сравнены без изменений.33 entries/176 paths/148 unique media hashes — разные показатели.

Butterflycarp использует только canonical hongkong456x298 (PAG912x596);488-вариант исследован и декодирован, но не выдаётся за дополнительные четыре сцены. Часы адаптированы из29 исходных PNG. Runtime переносит progress thresholds/500ms out/100ms delay after load/300ms in через JavaCarpSequence; это не Folme engine. Vortex переносится только как видеофон912x596/5s, без native аналоговых clock/date/battery overlays. pin_show — одноразовый ручной эффект появления SmartAssistant карточки, не платёж/NFC.

Отдельный stock online-магазин rear-screen подтверждён кодом Themes11.5.3.1: [маршруты и ограничения](online-rearscreen-themes.md). Online API/login/download не выполнялись, автоматический importer отсутствует.
