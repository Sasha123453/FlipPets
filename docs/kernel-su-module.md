# KernelSU: экспериментальная альтернатива контроллера

## Ownership and module transitions — development step 2

The root wrapper now stores PID, process start time and boot ID instead of a
Boolean ownership marker. It verifies root file/process ownership and exact
NUL-delimited interpreter/controller/`run` arguments. An extra argument or reused
PID cannot authorize stopping another process. Receipt-bound stale root files can
be cleaned without killing that PID or resetting device state.

Boot, Action and disable serialize through Android `flock` with a bounded
30-second acquisition wait. Detached controller children do not inherit the lock.
A disable publishes a new cancellation generation before waiting, so in-progress
Start cannot overwrite it. Stale boot cleanup rechecks generations under the lock
before deleting opt-in. Module directory/control files must be root-owned,
regular/non-symlink where appropriate, and not writable by group/others.

Disable waits up to 16 seconds for its exactly identified process to exit. If it
times out, the receipt remains and Action retries Stop rather than replacing the
child. If receipt persistence fails after startup ACK, an exact in-memory snapshot
can stop that still-identical process. If identity cannot be verified, startup
fails and asks for Flip Pets Stop rather than stopping an unknown process.

Legacy `owned` / `enabled` markers do not establish this receipt/generation
contract. Boot does not silently migrate them into new consent; use explicit
Action. Opt-in still lives in the module directory, so update persistence remains
unfinished. Android `flock` availability and physical UID0/SELinux behavior are not
yet verified on the phone. Shared root/shell runtime paths and post-start module
disable monitoring are the next milestones; keep this candidate experimental.

This module-only step leaves the APK and canonical/embedded controller bytes
unchanged. The matching APK is included with each reviewed development prerelease.
The wrapper fixtures now use real emulator `/proc` identities, background children
and `flock`, with UID ownership/storage and Android controller commands stubbed.
They cover concurrent Actions, boot/Action, newer disable during Start, stale boot,
extra argv, live PID reuse, stop timeout/retry and receipt-write failure.

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

The first step left process ownership/serialization unfinished; step 2 above now
hardens module transitions and identity. Shared root/shell file ownership,
cross-backend serialization, opt-in migration outside the replaceable module
directory, continuous module-disable handling and rooted MIX Flip testing remain
unfinished. Do not install this candidate merely to test these source changes.

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
