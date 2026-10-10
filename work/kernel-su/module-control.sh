#!/system/bin/sh
# First-stage root alternative only. Never change display layout, wakefulness or keyguard.
MODDIR=${0%/*}
CONTROLLER=$MODDIR/flip-pets-control.sh
ENABLED=$MODDIR/session-enabled
OWNED=$MODDIR/session-owned
CANCEL=$MODDIR/session-cancel
TRANSITION=$MODDIR/session-transition
STOP=/sdcard/Android/data/org.flippets.app/files/controller-stop
APPFILES=${STOP%/*}
RUNTIME=/data/local/tmp/flip-pets-enabled
MARK=/data/local/tmp/flip-pets-active
LOCK=/data/local/tmp/flip-pets-supervisor.lock
[ "$(id -u)" = 0 ] || { echo "KernelSU root required" >&2; exit 1; }
umask 077
not_publicly_writable() {
  permissions=$(stat -c '%a' "$1")
  case "$permissions" in ''|*[!0-7]*|*[2367][0-7]|*[2367]) return 1 ;; esac
}
root_file() { [ -f "$1" ] && [ ! -L "$1" ] && [ "$(stat -c '%u' "$1")" = 0 ] && not_publicly_writable "$1"; }
secure_module() {
  [ -d "$MODDIR" ] && [ ! -L "$MODDIR" ] && [ "$(stat -c '%u' "$MODDIR")" = 0 ] || return 1
  # mksh does not consistently interpret a leading zero as octal.
  not_publicly_writable "$MODDIR" || return 1
  for path in "$ENABLED" "$OWNED" "$CANCEL" "$TRANSITION"; do
    [ ! -e "$path" ] && [ ! -L "$path" ] || root_file "$path" || return 1
  done
}
secure_module || { echo "Unsafe module control paths; refusing root operation" >&2; exit 1; }
proc_start() {
  # Strip comm through its final ')': process names may contain spaces or ')'.
  start=$(sed 's/.*) //' "/proc/$1/stat" 2>/dev/null | cut -d ' ' -f 20)
  case "$start" in ''|*[!0-9]*) return 1 ;; esac
  echo "$start"
}
boot_id() { cat /proc/sys/kernel/random/boot_id; }
command_matches() {
  # Compare NUL-delimited argv bytes, not a command-line substring.
  actual=$(sha256sum "/proc/$1/cmdline" 2>/dev/null); actual=${actual%% *}
  for interpreter in sh /system/bin/sh; do
    wanted=$(printf '%s\000%s\000%s\000' "$interpreter" "$CONTROLLER" run | sha256sum)
    [ "$actual" != "${wanted%% *}" ] || return 0
  done
  return 1
}
snapshot_supervisor() {
  [ -d "$LOCK" ] && [ ! -L "$LOCK" ] && [ "$(stat -c '%u' "$LOCK")" = 0 ] || return 1
  root_file "$LOCK/pid" && root_file "$LOCK/ready" || return 1
  process=$(cat "$LOCK/pid")
  case "$process" in ''|0|1|*[!0-9]*) return 1 ;; esac
  [ "$(cat "$LOCK/ready")" = "$process" ] && kill -0 "$process" 2>/dev/null || return 1
  [ "$(stat -c '%u' "/proc/$process")" = 0 ] || return 1
  started=$(proc_start "$process") || return 1
  command_matches "$process" || return 1
  [ "$(proc_start "$process")" = "$started" ] || return 1
  printf '%s %s %s\n' "$process" "$started" "$(boot_id)"
}
read_receipt() {
  root_file "$OWNED" || return 1
  read -r owned_pid owned_start owned_boot extra < "$OWNED"
  case "$owned_pid:$owned_start" in *[!0-9:]*|:*|*:) return 1 ;; esac
  [ "$owned_pid" -gt 1 ] || return 1
  [ -n "$owned_boot" ] && [ -z "$extra" ] || return 1
}
process_receipt_alive() {
  [ "$(boot_id)" = "$3" ] || return 1
  kill -0 "$1" 2>/dev/null && [ "$(stat -c '%u' "/proc/$1")" = 0 ] || return 1
  [ "$(proc_start "$1")" = "$2" ] && command_matches "$1"
}
receipt_process_alive() {
  read_receipt && process_receipt_alive "$owned_pid" "$owned_start" "$owned_boot"
}
stop_captured_supervisor() {
  # A receipt write may fail (for example full storage). An in-memory receipt
  # may stop only the still-identical process observed immediately after ACK.
  [ -n "$receipt" ] && [ "$(snapshot_supervisor)" = "$receipt" ] || return 1
  read -r captured_pid captured_start captured_boot <<EOF
$receipt
EOF
  /system/bin/sh "$CONTROLLER" disable 9>&- || return 1
  waits=0
  while process_receipt_alive "$captured_pid" "$captured_start" "$captured_boot"; do
    [ "$waits" -lt 64 ] || return 1
    sleep 0.25; waits=$((waits+1))
  done
}
owns_supervisor() {
  read_receipt || return 1
  [ "$(snapshot_supervisor)" = "$owned_pid $owned_start $owned_boot" ]
}
record_supervisor() {
  receipt=$(snapshot_supervisor) || return 1
  printf '%s\n' "$receipt" > "$OWNED.$$" && mv -f "$OWNED.$$" "$OWNED" || return 1
  owns_supervisor
}
stale_owned_lock() {
  read_receipt || return 1
  [ -d "$LOCK" ] && [ ! -L "$LOCK" ] && [ "$(stat -c '%u' "$LOCK")" = 0 ] || return 1
  root_file "$LOCK/pid" && [ "$(cat "$LOCK/pid")" = "$owned_pid" ] || return 1
  if [ "$(boot_id)" = "$owned_boot" ] && kill -0 "$owned_pid" 2>/dev/null; then
    current_start=$(proc_start "$owned_pid") || return 1
    [ "$current_start" != "$owned_start" ] || return 1
  fi
  # No killing or display reset for a dead process or a reused PID. Only our
  # receipt-bound root-owned files may be removed; shell/unknown files block it.
  for path in "$RUNTIME" "$MARK" "$LOCK/ready"; do
    [ ! -e "$path" ] && [ ! -L "$path" ] || root_file "$path" || return 1
  done
  return 0
}
clear_stale_owned_lock() {
  stale_owned_lock || return 1
  rm -f "$RUNTIME" "$MARK" "$LOCK/pid" "$LOCK/ready" || return 1
  rmdir "$LOCK" || return 1
  rm -f "$OWNED"
}
cancel_generation() {
  if [ -f "$CANCEL" ]; then cat "$CANCEL"; else echo none; fi
}
advance_cancel() {
  generation=$(cat /proc/sys/kernel/random/uuid) || return 1
  [ -n "$generation" ] || return 1
  printf '%s\n' "$generation" > "$CANCEL.$$" && mv -f "$CANCEL.$$" "$CANCEL" || return 1
  rm -f "$ENABLED"
}
release_transition() { flock -u 9 9>&9 2>/dev/null; exec 9>&-; }
acquire_transition() {
  command -v flock >/dev/null 2>&1 || { echo "Android flock unavailable; refusing concurrent root control" >&2; return 1; }
  exec 9>> "$TRANSITION" || return 1
  waits=0
  # Android mksh marks extra descriptors close-on-exec unless explicitly passed.
  until flock -n 9 9>&9; do
    [ "$waits" -lt 120 ] || { exec 9>&-; echo "Controller transition busy; retry Action" >&2; return 1; }
    sleep 0.25; waits=$((waits+1))
  done
  trap 'release_transition' EXIT
  trap 'exit 1' HUP INT TERM
}
disable_session() {
  rm -f "$ENABLED"
  if owns_supervisor; then
    # Detached canonical children must never inherit the transition flock fd.
    /system/bin/sh "$CONTROLLER" disable 9>&- || return 1
    waits=0
    while receipt_process_alive; do
      [ "$waits" -lt 64 ] || { echo "Owned supervisor is still stopping; receipt retained" >&2; return 1; }
      sleep 0.25; waits=$((waits+1))
    done
  fi
  rm -f "$OWNED"
}
storage_ready() {
  # Boot-completed does not establish credential-encrypted storage availability.
  [ "$(cmd user is-user-unlocked 0 2>/dev/null)" = true ] || return 1
  [ -d "$APPFILES" ] && [ -r "$APPFILES" ] && [ -x "$APPFILES" ] || return 1
  ls -A "$APPFILES" >/dev/null 2>&1 || return 1
  if [ -e "$STOP" ]; then [ -f "$STOP" ] && [ -r "$STOP" ] || return 1; fi
  return 0
}
module_available() { [ ! -f "$MODDIR/disable" ] && [ ! -f "$MODDIR/remove" ]; }
enable_session() {
  launch=${1:-supervise}
  expected_generation=$2
  [ "$(getprop ro.product.device)" = ruyi ] || { echo "Only MIX Flip / ruyi" >&2; return 1; }
  module_available || return 1
  pm path org.flippets.app | grep -q '^package:' || { echo "Install FlipPets.apk first" >&2; return 1; }
  storage_ready || { echo "Open Flip Pets once and unlock storage first" >&2; return 1; }
  [ "$(cancel_generation)" = "$expected_generation" ] || { echo "Cancelled by a newer disable request"; return 1; }
  if [ "$launch" = resume ]; then
    [ -f "$ENABLED" ] || return 1
    [ ! -e "$STOP" ] || { rm -f "$ENABLED"; echo "Stopped by user"; return 1; }
  fi
  if { [ -e "$RUNTIME" ] || [ -e "$MARK" ] || [ -e "$LOCK" ]; } && ! owns_supervisor; then
    clear_stale_owned_lock || {
      echo "Stop the existing or unverified ADB/Shizuku/root session before enabling KernelSU." >&2
      return 1
    }
  fi
  # resume is unattended and never clears Stop. supervise is explicit Action only.
  /system/bin/sh "$CONTROLLER" "$launch" 9>&- || { rm -f "$ENABLED"; return 1; }
  record_supervisor || {
    rm -f "$ENABLED"
    stop_captured_supervisor || echo "Cannot verify startup cleanup; use Flip Pets Stop before retrying" >&2
    echo "Startup has no durable verified process receipt" >&2
    return 1
  }
  module_available && [ ! -e "$STOP" ] && [ "$(cancel_generation)" = "$expected_generation" ] || {
    disable_session
    return 1
  }
  printf '%s\n' "$expected_generation" > "$ENABLED"
  # A disable can publish cancellation while waiting for this flock.
  [ "$(cancel_generation)" = "$expected_generation" ] || { disable_session; return 1; }
  echo "Enabled. Root controller waits for open, awake and unlocked phone."
}
invocation_generation=$(cancel_generation)
case "${1:-status}" in
  toggle)
    acquire_transition || exit 1
    if [ -f "$ENABLED" ] || receipt_process_alive; then advance_cancel && disable_session; else enable_session supervise "$invocation_generation"; fi
    ;;
  boot)
    [ -f "$ENABLED" ] || exit 0
    expected_generation=$(cat "$ENABLED")
    if [ "$expected_generation" != "$invocation_generation" ]; then
      acquire_transition || exit 1
      # A stale boot must never delete opt-in published by a newer Action.
      if [ "$(cat "$ENABLED" 2>/dev/null)" = "$expected_generation" ] && [ "$(cancel_generation)" = "$invocation_generation" ]; then
        rm -f "$ENABLED"; echo "Legacy/cancelled opt-in; use explicit Action"
      fi
      exit 0
    fi
    # Up to ten minutes for first unlock/app storage. Action, disable and remove
    # cancel the wait. Timeout retains opt-in but never starts an outer retry loop.
    attempts=0
    while ! storage_ready; do
      [ -f "$ENABLED" ] && module_available && [ "$(cancel_generation)" = "$expected_generation" ] || exit 0
      [ "$attempts" -lt 120 ] || { echo "Storage unavailable; unlock then use Action" >&2; exit 1; }
      sleep 5; attempts=$((attempts+1))
    done
    [ -f "$ENABLED" ] && module_available || exit 0
    acquire_transition || exit 1
    [ "$(cat "$ENABLED" 2>/dev/null)" = "$expected_generation" ] && [ "$(cancel_generation)" = "$expected_generation" ] || exit 0
    [ ! -e "$STOP" ] || { rm -f "$ENABLED"; echo "Stopped by user"; exit 0; }
    enable_session resume "$expected_generation"
    ;;
  disable) advance_cancel && acquire_transition && disable_session ;;
  status) if owns_supervisor; then echo "Verified owned root supervisor"; else echo "No verified owned root supervisor"; fi; /system/bin/sh "$CONTROLLER" status 9>&- ;;
  *) echo "Usage: module-control.sh toggle|boot|disable|status" >&2; exit 1 ;;
esac
