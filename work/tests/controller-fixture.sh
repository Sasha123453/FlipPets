#!/system/bin/sh
# Stub only command outputs, inside a dedicated emulator fixture directory.
TEST=/data/local/tmp/flip-pets-fixture
getprop() { case "$1" in ro.product.device) cat "$TEST/device";; esac; }
cmd() {
  case "$1:$2" in
    device_state:print-state) cat "$TEST/state";;
    device_state:print-states) echo "DeviceState{identifier=5, name='OPENED_PRESENTATION'}";;
    device_state:state)
      case "$3" in
        5) echo 5 > "$TEST/state";touch "$TEST/override";;
        reset) cat "$TEST/base" > "$TEST/state";rm -f "$TEST/override";echo reset >> "$TEST/resets";;
        *) echo "Committed state: DeviceState{identifier=$(cat "$TEST/state")}";if [ -f "$TEST/override" ];then echo "Base state: DeviceState{identifier=$(cat "$TEST/base")}";echo "Override state: DeviceState{identifier=$(cat "$TEST/state")}";fi;;
      esac;;
    display:get-displays)
      remaining=$(cat "$TEST/display_off_reads" 2>/dev/null || echo 0)
      if [ "$remaining" -gt 0 ]; then
        echo $((remaining-1)) > "$TEST/display_off_reads";echo OFF > "$TEST/display_state"
      else echo ON > "$TEST/display_state"; fi
      echo "display $(cat "$TEST/display_state")" >> "$TEST/events"
      echo "Display id 1: DisplayInfo{displayId 1, real 1392 x 1208, state $(cat "$TEST/display_state"), type INTERNAL}" ;;
  esac
}
pm() { echo package:/fixture/FlipPets.apk; }
grep() {
  case "$*" in *'/odm/etc/displayconfig/display_layout_configuration.xml') /system/bin/grep -q OPENED_PRESENTATION "$TEST/layout";;*) command grep "$@";;esac
}
dumpsys() {
  case "$1" in power) echo "mWakefulness=$(cat "$TEST/wake")";;window)
    if [ "$2" = -setForceDisplayCompatMode ];then echo "compat $(cat "$TEST/display_state" 2>/dev/null || echo UNKNOWN)" >> "$TEST/events";else echo "showing=$(cat "$TEST/locked" 2>/dev/null || echo false)";fi;;
    activity) [ ! -f "$TEST/app_active" ] || echo "org.flippets.app/.PetActivity";;esac
}
am() {
  if [ "$1" = broadcast ];then rm -f "$TEST/app_active";echo closed >> "$TEST/closed";return;fi
  echo launch >> "$TEST/launches";echo "launch $(cat "$TEST/display_state")" >> "$TEST/events"
  remaining=$(cat "$TEST/reject_count" 2>/dev/null || echo 0)
  if [ -f "$TEST/reject" ] || [ "$remaining" -gt 0 ];then
    [ "$remaining" -le 0 ] || echo $((remaining-1)) > "$TEST/reject_count"
    if [ -f "$TEST/foreign_on_reject" ];then echo 4 > "$TEST/state";fi
    echo 'Error: fixture launch refusal';return 0
  fi
  if [ "$(cat "$TEST/display_state")" != ON ];then echo 'Error: launch attempted before display ON';return 1;fi
  touch "$TEST/app_active";echo "Starting: Intent $*" > "$TEST/launch";cat "$TEST/launch"
}
nohup() { :; }
. /data/local/tmp/flip-pets-fixture/control.sh
