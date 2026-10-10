#!/system/bin/sh
# First-stage root alternative only. Never change display layout, wakefulness or keyguard.
MODDIR=${0%/*}
CONTROLLER=$MODDIR/flip-pets-control.sh
ENABLED=$MODDIR/session-enabled
OWNED=$MODDIR/session-owned
STOP=/sdcard/Android/data/org.flippets.app/files/controller-stop
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
enable_session() {
  [ "$(getprop ro.product.device)" = ruyi ] || { echo "Only MIX Flip / ruyi" >&2; return 1; }
  [ ! -f "$MODDIR/disable" ] && [ ! -f "$MODDIR/remove" ] || return 1
  pm path org.flippets.app | grep -q '^package:' || { echo "Install FlipPets.apk first" >&2; return 1; }
  [ -d /sdcard/Android/data/org.flippets.app/files ] || { echo "Open Flip Pets once and unlock storage first" >&2; return 1; }
  if { [ -f "$RUNTIME" ] || [ -f "$MARK" ] || [ -d "$LOCK" ]; } && ! owns_supervisor && ! stale_owned_lock; then
    echo "Stop the existing ADB/Shizuku session in Flip Pets before enabling KernelSU." >&2
    return 1
  fi
  # Only a successful explicit Action clears the app's Stop request.
  /system/bin/sh "$CONTROLLER" supervise || return 1
  umask 077
  echo enabled > "$ENABLED"
  echo owned > "$OWNED"
  echo "Enabled. Root controller waits for open, awake and unlocked phone."
}
case "${1:-status}" in
  toggle) if [ -f "$ENABLED" ] && [ ! -f "$STOP" ]; then disable_session; else enable_session; fi ;;
  boot)
    [ -f "$ENABLED" ] || exit 0
    # Respect Stop across reboot. Never clear it during unattended startup.
    [ ! -f "$STOP" ] || { rm -f "$ENABLED"; exit 0; }
    enable_session
    ;;
  disable) disable_session ;;
  status) /system/bin/sh "$CONTROLLER" status ;;
  *) echo "Usage: module-control.sh toggle|boot|disable|status" >&2; exit 1 ;;
esac
