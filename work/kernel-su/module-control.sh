#!/system/bin/sh
# First-stage root alternative only. Never change display layout, wakefulness or keyguard.
MODDIR=${0%/*}
CONTROLLER=$MODDIR/flip-pets-control.sh
ENABLED=$MODDIR/session-enabled
OWNED=$MODDIR/session-owned
STOP=/sdcard/Android/data/org.flippets.app/files/controller-stop
APPFILES=${STOP%/*}
RUNTIME=/data/local/tmp/flip-pets-enabled
MARK=/data/local/tmp/flip-pets-active
LOCK=/data/local/tmp/flip-pets-supervisor.lock
[ "$(id -u)" = 0 ] || { echo "KernelSU root required" >&2; exit 1; }
owns_supervisor() {
  [ -f "$OWNED" ] && [ -r "$LOCK/pid" ] || return 1
  process=$(cat "$LOCK/pid")
  case "$process" in ''|*[!0-9]*) return 1 ;; esac
  kill -0 "$process" 2>/dev/null || return 1
  grep -Eq '^Uid:[[:space:]]+0[[:space:]]' "/proc/$process/status" || return 1
  tr '\000' ' ' < "/proc/$process/cmdline" | grep -Fq "$CONTROLLER run"
}
stale_owned_lock() {
  [ -f "$OWNED" ] && [ -r "$LOCK/pid" ] || return 1
  [ "$(stat -c '%u' "$LOCK/pid")" = 0 ] || return 1
  process=$(cat "$LOCK/pid")
  case "$process" in ''|*[!0-9]*) return 1 ;; esac
  ! kill -0 "$process" 2>/dev/null
}
disable_session() {
  rm -f "$ENABLED"
  if owns_supervisor; then
    /system/bin/sh "$CONTROLLER" disable
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
  [ "$(getprop ro.product.device)" = ruyi ] || { echo "Only MIX Flip / ruyi" >&2; return 1; }
  module_available || return 1
  pm path org.flippets.app | grep -q '^package:' || { echo "Install FlipPets.apk first" >&2; return 1; }
  storage_ready || { echo "Open Flip Pets once and unlock storage first" >&2; return 1; }
  if [ "$launch" = resume ]; then
    [ -f "$ENABLED" ] || return 1
    [ ! -e "$STOP" ] || { rm -f "$ENABLED"; echo "Stopped by user"; return 1; }
  fi
  if { [ -f "$RUNTIME" ] || [ -f "$MARK" ] || [ -d "$LOCK" ]; } && ! owns_supervisor && ! stale_owned_lock; then
    echo "Stop the existing ADB/Shizuku session in Flip Pets before enabling KernelSU." >&2
    return 1
  fi
  # resume is unattended and never clears Stop. supervise is explicit Action only.
  /system/bin/sh "$CONTROLLER" "$launch" || { rm -f "$ENABLED"; return 1; }
  module_available && [ ! -e "$STOP" ] || {
    /system/bin/sh "$CONTROLLER" disable
    rm -f "$ENABLED" "$OWNED"
    return 1
  }
  umask 077
  echo enabled > "$ENABLED"
  echo owned > "$OWNED"
  echo "Enabled. Root controller waits for open, awake and unlocked phone."
}
case "${1:-status}" in
  toggle) if [ -f "$ENABLED" ]; then disable_session; else enable_session supervise; fi ;;
  boot)
    [ -f "$ENABLED" ] || exit 0
    # Up to ten minutes for first unlock/app storage. Action, disable and remove
    # cancel the wait. Timeout retains opt-in but never starts an outer retry loop.
    attempts=0
    while ! storage_ready; do
      [ -f "$ENABLED" ] && module_available || exit 0
      [ "$attempts" -lt 120 ] || { echo "Storage unavailable; unlock then use Action" >&2; exit 1; }
      sleep 5; attempts=$((attempts+1))
    done
    [ -f "$ENABLED" ] && module_available || exit 0
    [ ! -e "$STOP" ] || { rm -f "$ENABLED"; echo "Stopped by user"; exit 0; }
    enable_session resume
    ;;
  disable) disable_session ;;
  status) /system/bin/sh "$CONTROLLER" status ;;
  *) echo "Usage: module-control.sh toggle|boot|disable|status" >&2; exit 1 ;;
esac
