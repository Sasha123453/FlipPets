# Ресурсы Xiaomi18Pro: импорт без дублирования

**Отложено по просьбе пользователя04.10.2026 до следующей версии. В Flip Pets1.0 ресурсы18Pro не импортируются.** Downloader остановлен с сохранением checkpoint; новый каталог, runtime и APK этим исследованием не менялись.

Источник исследования — официальный OTA `hongkong-ota_full-OS4.0.15.0.XFRCNXM-user-17.0-6aad32ed35.zip`, [Xiaomi CDN](https://bigota.d.miui.com/OS4.0.15.0.XFRCNXM/hongkong-ota_full-OS4.0.15.0.XFRCNXM-user-17.0-6aad32ed35.zip). Уже прочитанная OTA metadata указывает `pre-device=hongkong`, SDK37 и внутренний incremental `17OS4.0.260925.013226048.QCPECN.S`; это отдельно от публичного имени версии. Загрузка выбранных разделов ещё не означает проверенный полный flashable ZIP.

Новые ресурсы ещё не извлечены и не добавлены в приложение. План и финальная фактическая provenance формируются после получения разделов с проверенными payload operation hashes, partition size и SHA256. Новые APK донора не устанавливаются на MIX Flip.

## Сохранённая точка остановки

В ignored `work/firmware` сохранены:

- `hongkong-ota_full-OS4.0.15.0.XFRCNXM-user-17.0-6aad32ed35.partial.zip` — разреженный **неполный** ZIP. Его логический размер12 318 005 426B не означает, что все байты скачаны.
- Соответствующий `.partial.ranges.json`:16 640 завершённых chunks по262 144B (256KiB),4 362 076 160B, около4.0625GiB checkpointed ranges. Для объединения product+system_ext требуется20 561 chunks; checkpoint включает также служебные диапазоны, поэтому простой процент этих двух чисел не является проверкой разделов.
- `hongkong-partition-plan.json`, `hongkong-metadata.txt`, `hongkong-payload_properties.txt.txt`. SHA256 payload metadata сверен downloader с `METADATA_HASH=jTPDhEq9RsMeblfMxie2J0RsuGM+CoFNlMSTA0r73EM=`. Сама OTA metadata text имеет SHA256 `c0f345141d17ce06c167511a2c6dae46f9ff4446670b5d9b7dae22def1989f57`; это отдельные хеши разных данных.

**Полный ZIP и итоговые product/system_ext partition SHA пока не проверены.** Checkpoint подтверждает получение диапазонов по протоколу загрузчика; hash всей partition будет проверен только после завершения выбранных диапазонов и extraction. Не использовать `.partial.zip` для прошивки и не помечать его как verified firmware.

## Что сохраняется

`work/prepare_donor18.py` читает текущий каталог, не пересоздаёт старые entries и не сортирует их. Существующие id, compositions, duration/playback metadata и настройки сохраняются. Обычный `prepare_catalog.py` здесь повторно не запускается: он пересоздаёт каталог из прежних двух источников.

Текущий baseline0.9.1 содержит30 оформлений,170 ссылок на клипы и170 разных путей. Сравнение байтов даёт **142 уникальных PAG/MP4 SHA256**. Это разные показатели: номер сценария и название файла не доказывают новую анимацию. Старый каталог на этом этапе не сокращается.

## Правила новизны

- Полностью совпадающий набор media SHA256 считается source alias. Новый каталог entry и новый animation count для него не создаются, даже если OTA/MRC UUID, metadata или версия отличаются. Отличия MAML остаются исследовательским фактом.
- При частичном совпадении повторный media payload использует уже существующий asset path. Новый файл копируется только для нового SHA256; новый вариант MAML может ссылаться одновременно на старые и новые состояния.
- `newUniqueMedia` считается отдельно от `mediaReferencesAfterImport` и количества оформлений. Одинаковые байты внутри разных сцен/питомцев также не повышают unique count.
- Копируемые PAG/MP4 остаются побайтно оригинальными. Манифест MAML и SHA MRC, каждого media и используемого thumbnail фиксируются. Неизвестные состояния или native effects не переименовываются в поддержанную реакцию без кода-основания.

## Совместимость поведения

Оригинальное MAML finite hold принимается для известных классических семейств только при `PagView loop=1` и `onComplete→FrameRate0` без нового play. Такие семейства сохраняют классический prefix (`bird-hongkong` и т.п.). Для reactive scenes импорт требует совпадающего state contract с уже используемым MAML. Новые условия/числовые mapping, конечный playback неизвестного семейства и видео сначала остаются в research: текущий Java player не получает выдуманный loop.

Этот фильтр подтверждает только сопоставление локального поведения. Он не запускает Xiaomi MAML engine, не переносит автоматически backend18Pro, secure lockscreen, датчики донора или независимую power-group политику.

## Использование импортера

Эти команды — шаги будущего возобновления, сейчас они не выполняются.

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

Пять synthetic filesystem tests в `work/tests/test_donor18_import.py` проходят: finite hold, отказ неизвестной конечной политики, ZIP path traversal, повторное использование общего clip/alias/no baseline mutation и отказ apply до подтверждённого provenance. Они проверяют импорт данных, не декодирование Xiaomi artwork, не HyperOS и не реальный телефон. Новые resource/runtime QA выполняются отдельно на окончательном APK.

## Точные шаги возобновления в следующей версии

1. Работать из `E:\FlipPets`; сохранить существующие `.partial.zip`, `.ranges.json` и partition plan вместе. Не удалять checkpoint и не выдавать длину разреженного файла за downloaded bytes. Проверить, что downloader всё ещё использует тот же source URL, archive size и совместимый chunk size.
2. Возобновить только после возвращения пользователя к задаче: `python -X utf8 work/fetch_donor18.py --partitions product system_ext --workers 8`. Число workers можно уменьшить при повторных CDN timeout; это не меняет source/hash-проверку. Скрипт пропускает checkpointed ranges, сверяет payload metadata, проверяет operation/final partition SHA и создаёт `work/images/hongkong/product.verified-extraction.json` и аналогичный system_ext proof. При hash mismatch остановиться; не писать provenance-флаги вручную.
3. После verified partition создать listing без полного распаковывания: `work\tools\erofs\extract.erofs.exe -i work\images\hongkong\product.img -p > work\research\hongkong-product-list.txt`. Проверить реальные rear-screen content/meta/preview пути; если формат или расположение изменились, адаптировать extractor до копирования public assets.
4. Запустить приведённый выше **plan** `prepare_donor18.py --image ... --listing ...`. Проверить каждое решение: exact alias, partial reuse, unique hash delta и неподдержанные MAML state mapping. Сравнить новые XML с17Pro, включая finite hold/reactive actions и Charlie. APK/native effects исследовать локально отдельно; на телефон APK донора не устанавливать.
5. Для выбранных реально новых ресурсов подготовить gallery thumbnail, проверить размеры/последние кадры/alpha и только затем выполнить `--select UUID --apply`. Сохранить source hashes и MAML; не запускать старый `prepare_catalog.py` поверх изменённого каталога. Если новых animation SHA нет, так и сообщить, без повышения counts из-за18Pro metadata.
6. После интеграции отдельно измерить длительности новых клипов, проверить реальные state mapping и geometry, обновить QA-counts по фактическим сценариям. Сборка, emulator/physical проверки и Source/evidence packaging должны относиться к новому точному APK SHA; пять importer tests не заменяют эти проверки. Сохранять rootless fold/lock/sleep политику по умолчанию.
