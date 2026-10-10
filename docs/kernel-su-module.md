# KernelSU: экспериментальная альтернатива контроллера

## Development hardening — 11 October 2026

Implementation has resumed with the boot/startup part of the native integration
plan. This remains an experimental candidate, not a reliable root release.

- Boot requires `cmd user is-user-unlocked 0` to report true and the app's external
  files directory to be accessible. It checks every five seconds for at most ten
  minutes. Unknown/unavailable storage never means permission to resume.
- Boot uses canonical `resume`, which never removes `controller-stop`. An explicit
  Action uses `supervise`, which clears the previous Stop once. A subsequent Stop
  cancels startup; the child acknowledges only after verification and trap setup.
- Action while opted in switches the session off, even if an app Stop already
  exists. If storage timed out, unlock/open Flip Pets and use Action to turn the
  retained opt-in off, then Action again to explicitly start. No outer retry loop
  circumvents the controller's launch-failure limit.
- Module disable/remove or Action opt-out cancels the storage wait. A flag seen
  immediately after startup acknowledgement tears down that new session.

Outstanding: serialize boot/Action/Stop transitions, exact process identity and
PID reuse, opt-in migration outside the replaceable module directory, root-to-shell
file ownership, continuous module-disable handling after startup, and rooted
MIX Flip testing. The current marker/UID/command-line ownership check is still
experimental. Do not install this candidate merely to test these source changes.

Command verification: `work/tests/run_kernel_su_boot_tests.py` exercises wrapper
branches with rebased paths and stubbed UID/storage/controller on emulator-5554.
`run_supervisor_tests.py` and its `--kernel-su` variant exercise actual generated
controller logic with stock command responses stubbed. Neither proves SELinux,
first-unlock mount behavior or physical fold handling.

## Original candidate and installation

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
