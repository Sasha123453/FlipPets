## Импорт18Pro для1.1

- [x] Проверить payload metadata и полные product/system_ext partition hashes; whole OTA ZIP остаётся неполным и не проверенным.
- [x] Сравнить41 MRC по байтам и MAML. Все12 Charlie PAG идентичны17Pro: срез причёски не исправлен.
- [x] Выборочно добавить4 canonical Butterflycarp сцены, Vortex фон и эффект карточки:6 distinct media, без дублей других encoded variants.
- [x] Реально декодировать9 исходных PAG и2 MP4 кадра. Это source evidence; final APK runtime checks отдельно.
- [ ] Проверить новые сцены, fade transitions и размещение возле камер на реальном MIX Flip.
- [ ] Дополнительные темы: CN18Pro содержит online rear-screen магазин. Исследовать легальный выбранный файл/экспорт и безопасный offline import поддерживаемого MRC. Не обещать магазин на EEA MIX или автоматически исполнять неизвестные MAML.

# Flip Pets — текущие задачи

## Resumed implementation — 11 October 2026

- [x] First KernelSU hardening step: bounded first-unlock/storage wait, separate
  unattended resume preserving Stop, and child startup acknowledgement.
- [x] Step 2: exact root process/boot receipts, PID reuse protection and serialized
  module Action/boot/disable, with stale-boot and timeout/failure regression cases.
- [x] Step 3 source/fixture work: private persistent root state, root/shell lifetime
  serialization, explicit legacy migration, live module-disable monitoring and
  acknowledged manual watchers. Physical root verification remains separate.
- [ ] Verify root UID/SELinux, boot/first unlock/update/disable/fold on an actual
  rooted MIX Flip after assembly. Keep the ZIP experimental until that evidence.
- [x] Step4 current APK:374 renderer/UI/native-card checks,20 gallery and6 virtual-cover checks passed, plus14 route and5 packager cases. Physical testing remains deferred.
- [x] Native-launch card Activity, separate storage/navigation and opt-in observed-context routing. Actual EEA policy/admission/continuity remains a device gate.
- [ ] Exact EEA FlipHome/continuity contract and native pet motion/restore proof
  remain device-work gates. No generation backend work is required.

## Мини-приложения и свой питомец

- [x] Заполнить весь cover оригинальным responsive Canvas без чёрных полей; проверить реальные PixelCopy-снимки.
- [x] Извлечь шесть штатных firmware MAML-карточек и подтвердить JsCanvas/QuickJS runtime; исходные три публичных примера в этих пакетах не найдены.
- [ ] Найти проверенный MTZ/export именно Воды/Слов/Pomodoro и сравнить с публичными HTML; перенос native runtime ещё не выполнен.

- [x] Вместо собственного прототипа перенести3 оригинальных публичных HTML-карточки Xiaomi: Фокус/Вода/Слова, с source SHA, явным Apply/Cancel, офлайн-изоляцией и освобождением скрытого рендера.
- [ ] При необходимости отдельно локализовать китайские подписи/словарь и адаптировать Canvas accessibility, не называя изменённый вариант побайтно оригинальным.
- [ ] Проверить новый UI, касания возле камер и расход на физическом MIX Flip.
- [x] Подготовить первый KernelSU controller-модуль без framework/power/lockscreen изменений; root пока не установлен, phone QA отсутствует.
- [ ] После появления KernelSU проверить UID0/SELinux/boot/Stop и точную EEA power-group политику, прежде чем обещать folded/main-off работу.
- [x] Проследить донорский AI Companion image→image→video pipeline.
- [ ] Отложено пользователем: генератор и результат «фото → свой анимированный питомец», включая альтернативные backend. Root не заменяет сервис Xiaomi; генерация не блокирует нативных питомцев из донорских ресурсов или приложения.
- [x] Исследовать варианты root/non-root без реализации: `docs/native-cover-root-and-rootless-agent-plan.md`. Подтверждён код native launcher/2X3 MAML host в Global FlipHome; точный EEA APK и физическая работа ещё не проверены.

## Сейчас: геометрия раскрытого MIX Flip, без root

- [x] Версия1.0: варианты «С часами» и «Без часов» без дублирования ресурсов.
  «С часами» сохраняет точный автоматический размер0.9.1. «Без часов» увеличивает
  питомца справа с сохранением пропорций; круглые питомцы ограничены шириной.
  Масштаб и X/Y — отдельно для каждого питомца и варианта. В диалоге используется
  существующий предпросмотр; внешний экран меняется только после «Применить».
  Отмена сбрасывает черновик, «Автоматически» сбрасывает ручные значения выбранного
  варианта. Фото, композиции и Flowing glitter не затрагиваются.
- [x] Версия1.0: свежая проверка19 настоящих элементов/действий диалога
  `run_pet_layout_qa.py`,268 render/UI/utility и6 lifecycle проверок точного APK SHA.
  Исходная геометрия прошла1 076 assertions. Оба варианта сохраняются после
  завершения процесса и повторного запуска; проверены реальные UI и5 скриншотов.
  Эмулятор не подтверждает размещение у физических камер.
- [ ] Проверить новый крупный режим и ручные настройки на телефоне во всех
  сценах, после складывания и повторного запуска. Текущие проверки1.0 — эмулятор.
- [x] Установить1.0 обновлением на MIX Flip и проверить version/code/SHA APK.
  Это подтверждение установки, не физической геометрии новых режимов.
- [x] Обновить размер и положение перенесённых питомцев: справа и снизу,
  с запасом от камер. Особенно проверить Charlie на всех сценах и касаниях.
  0.9.1 использует постоянный subject focus, увеличивает питомцев на10%
  относительно промежуточной0.9 и убирает прямоугольное отсечение декораций.
  Проверка всех движений у физических камер остаётся открытой.
- [ ] Charlie: верх причёски срезан в отдельных исходных кадрах pag_0.
  Пользователь подтвердил срез при движении, размер0.9.1 подходит. Отдельный
  libpag probe воспроизводит срез, padding64px обоих контейнеров не восстанавливает
  пиксели. Конечный кадр1.0 целый. Не считать причёску исправленной.
- [x] Предпросмотр имеет пропорции реального внешнего экрана1208:1392
  и использует ту же геометрию, что внешний сеанс и PAG WallpaperService.
  Мягкая граница сцены Lola/Coco пока только в Activity; обычные MP4-обои
  используют прежний direct-Surface путь. Нативный folded engine сюда не входит.
- [ ] Проверить изменение размеров/поворот, переключение сцен и возврат после
  складывания; положение не должно прыгать. Измерять силуэт по оригинальным
  PAG, сохранять одну область на набор, не пересчитывать масштаб каждый кадр.
- [ ] Отложено после уточнения пользователя: питомец на раскрытом телефоне
  при **любом** выключении основного экрана, включая Power и таймаут. Отдельная
  кнопка приложения не подходит. Это отдельная задача от folded wallpaper.
  Нужен явный выбор режима и ограниченного времени показа, например10/30/60секунд.
  Сохранять защищённую блокировку, не использовать wake lock/KEEP_SCREEN_ON,
  не выдавать просто выключенную панель при awake/unlocked устройстве за AOD.
- [ ] Проверить питание дисплеев и пробуждение физической кнопкой. Краткий
  опыт `cmd display power-off 0` дал основнойOFF и внешнийON; после опыта
  выполнен `power-reset 0`. PowerManager при этом **Awake**, защищённая
  блокировка и нормальное нажатие Power в таком режиме ещё не подтверждены.
- [x] Историческая эмуляторная QA и целевые проверки на телефоне относятся
  к точному SHA0.9.1:268 render/UI/utility проверок,582 геометрических
  assertions,6 lifecycle проверок. Телефон: установка/hash, оба окна, FGS,
  геометрия Charlie и короткий CPU/PSS; новый fold/reboot не подтверждены.
- [ ] MP4-аватары: непрозрачная прямоугольная рамка исходного видео ещё видна.
  Продумать естественное заполнение фона отдельно от размещения PAG-питомцев.

## На потом: нативная блокировка сложенного телефона

Отложено по просьбе пользователя03.10.2026. Не применять новый шаблон автоматически.

- Найден реальный tiny editor: `com.miui.tinykeyguard.editor.edit.EditActivity`,
  action `miui.tinykeyguard.editor.EDIT`, STRING extra `param_template_item_json`.
  Формат `TemplateItem`: `clockInfo.templateId=ai_pets`, `pets.petCategory=2`,
  `aiPetsData.resourcePag/resourcePic`, first/lastFrameCoordinateAxes.
- Штатный AOD имеет MANAGE_EXTERNAL_STORAGE и умеет копировать plain-file PAG
  своим UID через `TemplateApiImpl.fileCopy`; content:// в этой ветке не поддержан.
- На EEA HyperOS3.0.303 родной редактор принял наш JSON и показал Charlie
  в предпросмотре. **Проигрывание PAG не подтверждено**: видимый кадр может быть
  poster. Apply/Добавить не нажимались. Текущий шаблон и история сравнивались
  побайтно до/после и остались прежними. Временные файлы с телефона удалены.
- [ ] Подтвердить декодирование/движение в родном preview отдельно от poster.
- [ ] Проверить размер и координаты native PAG: AI-engine создаёт1208×1392,
  исходный976×596 переносит без масштабирования. Области first/last задают
  перенос, а не произвольный zoom.
- [ ] Подготовить и проверить точное восстановление текущего шаблона, ресурсов
  и истории **до Apply**. Повторное применение исходного JSON — пока только
  кандидат семантического восстановления, не доказанный точный rollback.
- [ ] Затем реализовать удобный optional export/import; проверить folded lock,
  пробуждение, AOD, поворот, перезагрузку и ресурсы. Обои lock и AOD — разные
  механизмы; наличие анимированных обоев не доказывает непрерывную анимацию AOD.

Публичные детали: [исследование](docs/folded-wallpaper-options.md) и
[санитизированный контракт preview](docs/native-tiny-preview-evidence.json).
Локальные приватные snapshots/fixtures находятся в игнорируемом
`work/phone-qa/native-folded`; декомпиляция и GET-only probe — в
`work/folded-research`. Их не включать в Git/Source ZIP.

Prototype `work/folded-research/native-pag-wrap.py` добавляет внешнюю PAG-композицию
1208×1392 с постоянным переносом/масштабом, сохраняя исходное тело файла побайтно.
Загрузка libpag1208×1392 и восемь различных видимых кадров подтверждены
изолированным эмуляторным probe; native engine ещё не проверен. Оригинальные файлы не заменять.

Результаты независимого питания и причины отсрочки: [power policy](docs/independent-display-power.md).

## Следующая версия: оригинальные ресурсы Xiaomi18Pro

После новой инструкции пользователя «Тяни из18про»04.10.2026 загрузка и read-only
research возобновлены. **Baseline1.0 не менять.** Выпуск1.1 рассматривается только
для действительно новых совместимых ресурсов; apply/catalog/runtime пока не разрешены.

- [x] Найден официальный hongkong OTA OS4.0.15.0.XFRCNXM; metadata подтверждает
  pre-devicehongkong и SDK37. Payload metadata SHA проверен, но полный ZIP и
  итоговые partition SHA **не проверены**.
- [x] Downloader остановлен с checkpoint:16 640 chunks по256KiB, около4.0625GiB.
  product+system_ext требуют20 561 chunks; служебные диапазоны считаются отдельно.
  Неполный sparse ZIP/checkpoint/metadata/partition plan остаются в ignored
  `work/firmware`; не удалять перед продолжением и не использовать для прошивки.
- [x] Готов `work/prepare_donor18.py` с read-only plan, media SHA dedup и сохранением
  текущего каталога. Восемь synthetic importer tests прошли; actual18Pro artwork
  ещё не извлечён/не импортирован/не декодирован.
- [ ] Загрузка возобновлена; дождаться verified-extraction JSON обоих разделов:
  `python -X utf8 work/fetch_donor18.py --partitions product system_ext --workers 8`.
- [ ] Создать EROFS product listing, запустить только import-plan. Exact media aliases
  не добавляют оформление; partial overlap использует старые asset paths. Baseline
  содержит170 сценариев/ссылок, но142 уникальных media SHA — считать новизну по SHA.
- [ ] Сопоставить original18 MAML states/hold с17Pro; отдельно сравнить Charlie и
  срез причёски. Совпадающие файлы не являются новым исправлением. Новые политики
  не подменять выдуманным loop или названиями событий без actual mapping.
- [ ] Выбрать действительно новые ресурсы, подготовить настоящие thumbnails,
  затем selective apply, durations/state/geometry и свежие QA точного нового APK.
  Firmware/MRC/APK raw extraction остаётся ignored; source/provenance публичны
  только для выбранных ресурсов. На телефон donor APK не устанавливать.

Полные имена checkpoint, hash limits и команды продолжения:
[donor18-resource-import.md](docs/donor18-resource-import.md).
