# KernelSU: экспериментальная альтернатива контроллера

10.10.2026 пользователь разрешил root-модуль как альтернативу ADB/Shizuku и
уточнил, что root пока отсутствует, планируется KernelSU. Существующий rootless
путь остаётся по умолчанию. Root на телефон не устанавливался.

`python -X utf8 work/build_kernel_su_module.py` создаёт
`outputs/FlipPets-KernelSU-experimental.zip`. Это первый этап: supervisor от UID0
вместо Shizuku UID2000, с теми же проверками ruyi/display layout, bounded retries,
fold/lock/sleep и собственными marker/Stop. Root-копия controller генерируется
из текущего canonical script с явной заменой UID-проверки, не развивается отдельно.
Canonical outputs/controller и embedded asset остаются идентичны.

Модуль не содержит APK, framework/partition overlays, sepolicy rules, системных
properties или изменения secure keyguard. Script-only модуль не требует
metamodule для system mounts: [официальная инструкция KernelSU](https://kernelsu.org/guide/module.html).
Отсутствие system mounts — свойство этого модуля; оно не подтверждает совместимость
со всеми версиями KernelSU/HyperOS. Физическая проверка пока невозможна без root.

После появления KernelSU:

1. Установить matching FlipPets.apk как обновление, открыть Main и разрешить
   уведомление внешнего сеанса обычным диалогом Android.
2. Остановить ранее включённый ADB/Shizuku-сеанс в приложении. Модуль отказывается
   перехватывать найденные markers/lock другого контроллера.
3. В KernelSU установить ZIP, перезагрузить, нажать **Action** для явного включения.
   Установка сама не включает внешний экран. Action повторно выключает сеанс.
4. Разрешённый сеанс пытается возобновиться после boot-completed. App Stop
   сохраняется и учитывается после перезагрузки; для нового старта нужен Action.
   Удаление модуля останавливает только сеанс, помеченный как его собственный.

На данный момент это кандидат без проверки UID0/SELinux/boot на MIX Flip.
Командные fixtures и shell syntax не доказывают реальный privileged launch.

**Модуль не решает независимое питание внешнего экрана.** Как и rootless путь,
он показывает наше приложение при открытом, awake и unlocked телефоне. Для
сложенного lockscreen или продолжения после настоящего Power/timeout потребуется
отдельное исследование OEM power groups/framework на точном EEA build с root,
проверкой безопасного возврата. Не включать repeated wake/ON/brightness hacks,
не подменять secure sleep выключением панели. См.
[предыдущий power audit](independent-display-power.md).
