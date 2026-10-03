#!/system/bin/sh
# Temporary presentation mode, stock Android/Xiaomi commands only. No partition writes.
PKG=org.flippets.app
MARK=/data/local/tmp/flip-pets-active
ENABLE=/data/local/tmp/flip-pets-enabled
LOCK=/data/local/tmp/flip-pets-supervisor.lock
STOP=/sdcard/Android/data/org.flippets.app/files/controller-stop
STATUS=/data/local/tmp/flip-pets-status
fail() { echo "ERROR: $*" >&2; exit 1; }
state() { cmd device_state print-state 2>/dev/null | tr -d '\r\n '; }
stop() {
  if [ -f "$MARK" ]; then
    am broadcast --receiver-foreground -a org.flippets.app.STOP_COVER -p "$PKG" >/dev/null 2>&1
    if [ "$(state)" = "5" ]; then cmd device_state state reset || fail "Cannot reset device state"; fi
    rm -f "$MARK"
  else
    echo "No Flip Pets request marker. Leaving other display requests untouched."
  fi
}
verify() {
  [ "$(id -u)" = "2000" ] || fail "This rootless controller requires ADB shell UID 2000"
  [ "$(getprop ro.product.device)" = "ruyi" ] || fail "This controller is only for MIX Flip / ruyi"
  pm path "$PKG" | grep -q '^package:' || fail "Install FlipPets.apk first"
  cmd device_state print-states | grep -q 'identifier=5' || fail "Presentation state 5 is not supported"
  grep -q 'OPENED_PRESENTATION' /odm/etc/displayconfig/display_layout_configuration.xml || fail "Unrecognised display layout; collect diagnostics"
}
unlocked() { dumpsys window policy | grep -Eq '(^|[[:space:]])showing=false|mKeyguardShowing=false'; }
case "${1:-diagnose}" in
diagnose)
  for key in ro.product.device ro.product.model ro.build.version.release ro.build.version.incremental ro.miui.ui.version.name; do echo "$key=$(getprop "$key")"; done
  cmd device_state print-states
  cmd device_state state
  cat /odm/etc/displayconfig/display_layout_configuration.xml
  cmd display get-displays
  dumpsys display
  ;;
stop|disable) rm -f "$ENABLE"; stop; echo "Stopped; supervisor disabled" ;;
status)
  if [ -f "$ENABLE" ] && [ -f "$LOCK/pid" ] && kill -0 "$(cat "$LOCK/pid")" 2>/dev/null; then echo "Supervisor running"; else echo "Supervisor stopped"; fi
  [ ! -f "$STATUS" ] || cat "$STATUS"
  cmd device_state state
  echo "=== Supported states ==="; cmd device_state print-states
  echo "=== Physical display information ==="; cmd display get-displays
  echo "=== Firmware layout ==="; cat /odm/etc/displayconfig/display_layout_configuration.xml 2>/dev/null
  echo "=== Power/keyguard ==="; dumpsys power | grep 'mWakefulness='
  dumpsys window policy | grep -E 'mKeyguardShowing|(^|[[:space:]])showing='
  true
  ;;
supervise)
  verify
  if [ -f "$LOCK/pid" ] && kill -0 "$(cat "$LOCK/pid")" 2>/dev/null; then
    tr '\000' ' ' < "/proc/$(cat "$LOCK/pid")/cmdline" | grep -q 'flip-pets-control.sh run' || fail "Existing PID is not this supervisor"
    echo enabled > "$ENABLE"; rm -f "$STOP"; echo "Supervisor already running"; exit 0
  fi
  rm -f "$LOCK/pid"; rmdir "$LOCK" 2>/dev/null
  umask 077; mkdir "$LOCK" || fail "Cannot acquire supervisor lock"
  echo enabled > "$ENABLE"; rm -f "$STOP"
  command -v nohup >/dev/null 2>&1 || { rm -f "$ENABLE"; rmdir "$LOCK"; fail "nohup is unavailable"; }
  nohup sh "$0" run >/data/local/tmp/flip-pets-supervisor.log 2>&1 </dev/null &
  echo $! > "$LOCK/pid"
  echo "Supervisor enabled; waiting for fully open, awake, unlocked phone. Cable is no longer required."
  ;;
run)
  verify
  trap 'rm -f "$ENABLE"; stop; rm -f "$LOCK/pid"; rmdir "$LOCK" 2>/dev/null; exit' HUP INT TERM EXIT
  misses=0; failures=0; probes=0
  while [ -f "$ENABLE" ]; do
    [ ! -f "$STOP" ] || break
    status=$(cmd device_state state 2>/dev/null)
    if [ -f "$MARK" ] && ! echo "$status" | grep -q 'Override state:.*identifier=5'; then
      am broadcast --receiver-foreground -a org.flippets.app.STOP_COVER -p "$PKG" >/dev/null 2>&1; rm -f "$MARK"
    fi
    base_open=0
    if echo "$status" | grep -q 'Base state:.*identifier=3'; then base_open=1; elif ! echo "$status" | grep -q 'Override state:' && echo "$status" | grep -q 'Committed state:.*identifier=3'; then base_open=1; fi
    if [ "$base_open" = 0 ] || ! dumpsys power | grep -q 'mWakefulness=Awake' || ! unlocked; then
      stop >/dev/null; echo waiting > "$STATUS"; misses=0
    elif echo "$status" | grep -q 'Override state:' && [ ! -f "$MARK" ]; then
      echo 'Another client owns an override; waiting without changing it' > "$STATUS"
    elif [ ! -f "$MARK" ]; then
      if FP_SUPERVISED=1 sh "$0" start > "$STATUS" 2>&1; then failures=0; misses=0; else failures=$((failures+1)); sleep 10; fi
      [ "$failures" -lt 3 ] || { echo 'Three launch failures; disabled. Collect diagnostics before trying again.' > "$STATUS"; break; }
    else
      # If our cover activity disappeared, retry with a bounded delay, not every poll.
      probes=$((probes+1))
      if [ "$probes" -ge 5 ]; then
        probes=0
        if dumpsys activity activities | grep -q "$PKG/.PetActivity"; then misses=0; else misses=$((misses+1)); fi
      fi
      if [ "$misses" -ge 2 ]; then stop >/dev/null; misses=0; fi
    fi
    sleep 2
  done
  rm -f "$ENABLE"; stop >/dev/null; rm -f "$LOCK/pid"; rmdir "$LOCK" 2>/dev/null
  trap - HUP INT TERM EXIT
  ;;
watch)
  # Stop our override when the hinge leaves fully open or the phone goes to sleep.
  while [ -f "$MARK" ]; do
    status=$(cmd device_state state 2>/dev/null)
    if ! echo "$status" | grep -q 'Override state:.*identifier=5'; then rm -f "$MARK"; break; fi
    if ! echo "$status" | grep -q 'Base state:.*identifier=3'; then stop; break; fi
    if ! dumpsys power | grep -q 'mWakefulness=Awake'; then stop; break; fi
    sleep 2
  done
  ;;
start)
  verify
  current=$(state)
  if [ "$current" = "5" ] && [ -f "$MARK" ]; then echo "Already active"; exit 0; fi
  unlocked || fail "Unlock the phone first; if already unlocked collect diagnostics"
  [ "$current" = "3" ] || fail "Open and unlock the phone first (expected state 3, got $current)"
  cmd device_state state | grep -q 'Override state:' && fail "Another app already owns a state override"
  umask 077
  # Scope this runtime compatibility override to our package; never enable all installed apps.
  dumpsys window -setForceDisplayCompatMode "$PKG" allowstart >/dev/null 2>&1
  cmd device_state state 5 || fail "ADB denied presentation state; collect diagnostics"
  echo active > "$MARK"
  rollback() { cmd device_state state reset >/dev/null 2>&1; rm -f "$MARK"; }
  trap 'rollback; exit 1' HUP INT TERM
  tries=0
  while [ "$(state)" != "5" ] && [ "$tries" -lt 20 ]; do sleep 0.25; tries=$((tries+1)); done
  if [ "$(state)" != "5" ]; then rollback; fail "State 5 did not activate"; fi
  displays=$(cmd display get-displays)
  id=$(echo "$displays" | grep -E 'real (1392 x 1208|1208 x 1392)' | sed -n 's/.*displayId \([0-9][0-9]*\),.*/\1/p' | head -n 1)
  case "$id" in ''|0|*[!0-9]*) rollback; fail "No independent 1392x1208 cover display found";; esac
  result=$(am start --display "$id" -n "$PKG/.PetActivity" -f 0x18000000 --ez coverSession true 2>&1)
  echo "$result"
  echo "$result" | grep -Eiq 'error:|exception|permission denial' && { rollback; fail "Activity launch was rejected"; }
  trap - HUP INT TERM
  if [ "${FP_SUPERVISED:-0}" = "1" ]; then :; elif command -v nohup >/dev/null 2>&1; then
    nohup sh "$0" watch >/data/local/tmp/flip-pets-watch.log 2>&1 </dev/null &
  else
    echo "No nohup available: use Stop before folding or locking."
  fi
  echo "Started on display $id. To restore normal folding: sh $0 stop"
  ;;
*) fail "Usage: sh $0 diagnose|start|supervise|status|stop" ;;
esac
