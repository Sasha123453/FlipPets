# Раскрытый MIX Flip: основной экран выключен, питомец снаружи

Задача **отложена после проверки rootless-возможностей**: пользователь требует обычную кнопку питания и продолжение при любом выключении основного экрана, разрешив оставить сложный сценарий на потом. Нативный lockscreen **сложенного** телефона был отложен отдельно и раньше: [folded-wallpaper-options.md](folded-wallpaper-options.md). Ниже чтение AOSP/Xiaomi кода и короткий аппаратный опыт родительского агента; этот агент не выполнял телефонных команд. В выпуске0.9 продолжение при main locked/off не заявляется реализованным.

## Вывод

Индивидуально погасить main panel через Shizuku возможно: родительский опыт `cmd display power-off 0` дал logical main0 OFF и cover1 ON, PetActivity оставалась resumed, `mWakefulness=Awake`; сразу выполнен `power-reset 0`. Это доказательство отдельного питания панели, **не** сценария штатной кнопки питания/PowerManager Sleep. Display ID1 в этом опыте и device-state5 — разные значения; cover ID следует определять каждый раз по реальному display.

Надёжное продолжение после настоящего Power-button Sleep без WakeLock/KEEP_SCREEN_ON/wakeUp пока не доказано. Простого requestDisplayPower(cover,STATE_ON) недостаточно. Решение: оставить сценарий отложенным. Физический override или lockNow+main-off не выпускается как аналог17Pro. При возвращении к задаче нужны доступная штатная per-group политика и проверка keyguard/таймаута/пробуждения; текущего доказательства для надёжного rootless-режима нет.

## Что делают команды Android16

Shell `power-off` передаёт STATE_OFF, `power-reset` — STATE_UNKNOWN. Reset означает возврат к рассчитанному системой состоянию, а не обязательное включение. История изменения команды прямо объясняет, почему прежнее power-on не подходило для спящего экрана. [AOSP ShellCommand](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/display/DisplayManagerShellCommand.java), [исходный commit power-reset](https://android.googlesource.com/platform/frameworks/base/+/a8458cd441e838c29087077dd6510543f394ee63).

В Android16 DMS requestDisplayPower вызывает физический device request напрямую, используя сохранённые brightness и desired-state; mDisplayStates и PowerManager wakefulness этим не меняются. Binder метод защищён MANAGE_DISPLAYS, shell UID имеет это разрешение в локальном dump. Интерфейс принимает state int, включая STATE_ON, хотя shell CLI предлагает только OFF/reset. В случае cached OFF brightness может оставаться BRIGHTNESS_OFF_FLOAT: запрос ON сам не создаёт нормальную яркость. Команда также не имеет lease/TTL/death-cleanup. Следующий штатный state/brightness update может заменить override; при одинаковом cached request update может вообще пропускаться. Поэтому нельзя обещать сброс «при любом событии» или сохранение «до нашего таймера». [AOSP16 DisplayManagerService, requestDisplayPower и requestDisplayStateInternal](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-16.0.0_r3/services/core/java/com/android/server/display/DisplayManagerService.java).

LocalDisplayAdapter публикует новое device state и выполняет SurfaceControl/backlight операцию. Это объясняет наблюдаемый physical/logical OFF, но не превращает вызов в goToSleep. Platform main-branch используется здесь как дополнительное описание адаптера; vendor Android16 может отличаться. [LocalDisplayAdapter](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/display/LocalDisplayAdapter.java).

## Почему настоящий Sleep сложнее

PMS рассчитывает wakefulness, user-activity timeout, display policy и suspend blockers для power groups. Физический DMS override обходит этот расчёт: при sleep/doze CPU может перейти в suspend, Handler-таймер/декодер не получает гарантированного времени исполнения. Это архитектурный вывод, не измеренная остановка именно MIX. Обычный foreground service сам по себе не держит CPU или экран. [Android16 PowerManagerService](https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-16.0.0_r3/services/core/java/com/android/server/power/PowerManagerService.java).

Keyguard visibility также проверяется отдельно для каждого display. ShowWhenLocked может сделать Activity допустимой поверх keyguard, но не доказывает resumed/CPU-active состояние при sleep и не снимает secure keyguard основного экрана. AOD имеет собственную ветку видимости. Ни dismissKeyguard, ни TURN_SCREEN_ON не нужны для сохранения основной защиты. [AOSP KeyguardController](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/wm/KeyguardController.java).

Наш текущий controller намеренно требует awake+unlocked, а PetActivity не заявляет showWhenLocked. Его остановка при настоящем lock/sleep сейчас предусмотрена кодом; удаление этой проверки само по себе не создаёт независимое питание. MIX layout5 делает cover follower main через leadDisplayAddress. Это подтверждает связь яркости в конфигурации, но само по себе не является dump-доказательством точного powerGroup состава. [Локальная ruyi layout](../work/research/ruyi-display_layout_configuration.xml).

## Чем отличается штатный rear backend Xiaomi

Происхождение framework проверено по уже загруженным образам, без новых загрузок. В обоих случаях файл `/framework/miui-services.jar` извлечён из `system_ext.img`; размер, SHA256 и byte identity сверены. [Машиночитаемый inventory](framework-power-provenance.json).

| Исходник | Архив OTA / записанная версия | JAR bytes / SHA256 |
| --- | --- | --- |
| MIX Flip ruyi **Global**, не фактический EEA framework | `ruyi_global-ota_full-OS3.0.303.0.WNIMIXM-user-16.0-0200f61ca8.zip` | 12 557 750 / `3ee0c554ec6f92da3176e258781bd5dca269fea921ba893a8af8bce4177a329b` |
| Xiaomi17Pro pandora **CN**, настоящий donor framework | `pandora-ota_full-OS3.0.319.0.WBLCNXM-user-16.0-2d01cf4d66.zip` | 12 754 786 / `0ca8bee568f2d4607aa6393764338d5b52fcd0101cdce49c39d8051a3fdc4c70` |

Существовавший `work/jars/miui-services.jar` совпадает именно с ruyi Global. Его нельзя называть donor17Pro. Фактический телефон — MIX Flip EEA HyperOS3.0.303.0.WNIEUXM/Android16; его framework JAR не извлечён и не сопоставлен с Global. Совпадение отдельных AOD/Wallpaper APK не доказывает совпадение framework. OTA metadata содержит внутренние incremental `16OS3.1.260805.171151286.QCPEGL.S` у ruyi и `16OS3.1.260824.101335611.QCPECN.S` у pandora; inventory хранит их отдельно от имён архивов, не подменяя одно другим.

Проверены `PowerManagerServiceImpl` из обоих JAR и display/cover ветки. Они используют `MiuiMultiDisplayTypeInfo.isIndependentRearDevice()`: отдельный rear powerGroup1, `rear_doze_always_on`, `subscreen_display_time`, отдельные rear wake/sleep и power-key события. `updateSecondaryDisplayScreenOffTimeoutLocked()` читает значение с fallback10000ms только при independent-rear gate; одноимённая default-константа15000ms сама по себе не определяет этот consumer. Это подтверждает наличие OEM-архитектуры отдельного rear timeout, но не обязательные десять секунд в любой настройке17Pro и не активную group1 на MIX.

В **обоих** JAR convenience `wakeUpSecondaryDisplay(IBinder,long,int,String)` и `goToSleepSecondaryDisplay(long,String)` имеют пустые тела. Название метода/Binder code16777212 не является рабочим API; отдельная boolean-ветка sleep обращается к group1 только при independent-rear gate. Перенос settings `subscreen_display_time` не активирует неподдержанный тип устройства. Декомпиляция и JAR сохранены только в ignored `work/folded-research/independent-power`; приложение не менялось.

## Как подтвердить точное поведение17Pro позже

Официальный Xiaomi отчёт подтверждает Dynamic Back Display, персонализацию AI-wallpaper и динамические уведомления, но не длительность нашего конкретного pet loop. [Xiaomi Q3 report](https://ir.mi.com/static-files/e4830480-8ce9-45f8-a09d-64e40b2bdfac). Общая справка Xiaomi описывает AOD-режимы «10 секунд после касания», Always и Scheduled; это **не** специфическое доказательство непрерывного pet playback на17Pro. [Общая справка AOD](https://www.mi.com/my/support/article/KA-33164/).

При доступе к настоящему17Pro надо записать ROM и реальные rear/AOD настройки, затем обычной кнопкой питания заблокировать main, отдельно разбудить rear штатным жестом из его UI и измерить idle cutoff. Проверить, что main остаётся защищённым; снять, играет ли питомец постоянно, один раз или только реагирует на touch/movement. Повторить с доступными вариантами AOD и разными rear timeout, если такие пункты действительно есть. Независимое rear UI, его wake/timeout и статический AOD — отдельные наблюдения. До этого 1:1 lifecycle/жесты/вечный loop не заявляются подтверждёнными.

## Что проверять только при возобновлении

- Разделять три случая: main физически OFF при PMS Awake; secure main locked при PMS Awake; настоящий пользовательский Power-button sleep/doze. Первый случай уже коротко подтверждён, остальные требуют отдельных фактов.
- Сохранять основной secure keyguard; проверять resumed/visible cover, actual display state/brightness и powerGroup/wakefulness, а не только exit0 команды. ShowWhenLocked не равен разблокировке.
- Для исследовательского override иметь заранее подготовленный power-reset main и восстановление только своего device-state request в finally/stop. Reset должен возвращать текущую системную политику, не принудительно будить экран. TTL в DMS отсутствует; нельзя оставлять main override при потере процесса/сеанса.
- Не заменять настоящее Sleep многократными ON/brightness polling, WakeLock или wakeUp. lockNow+main-off при Awake может менять смысл первой кнопки питания: система считает group бодрствующей и сначала отправляет её спать, хотя пользователь уже видит чёрный main. Такой режим нельзя молча выпускать как обычное выключение.
- Для требуемого естественного поведения нужен доступный OEM/per-group механизм либо доказанный совместимый policy route. Пока rootless такого маршрута не подтверждено. Короткий эксперимент с panel override полезен для исследования, но не доказывает надёжный автоматический режим10секунд.