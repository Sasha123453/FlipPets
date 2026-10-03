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
        *) echo "Committed state: DeviceState{identifier=$(cat "$TEST/state")}";if [ -f "$TEST/override" ];then echo "Base state: DeviceState{identifier=$(cat "$TEST/base")}";echo "Override state: DeviceState{identifier=5}";fi;;
      esac;;
    display:get-displays) echo 'Display id 1: DisplayInfo{displayId 1, real 1392 x 1208, state ON, type INTERNAL}' ;;
  esac
}
pm() { echo package:/fixture/FlipPets.apk; }
grep() {
  case "$*" in *'/odm/etc/displayconfig/display_layout_configuration.xml') /system/bin/grep -q OPENED_PRESENTATION "$TEST/layout";;*) command grep "$@";;esac
}
dumpsys() {
  case "$1" in power) echo "mWakefulness=$(cat "$TEST/wake")";;window) echo "showing=$(cat "$TEST/locked" 2>/dev/null || echo false)";;activity) [ ! -f "$TEST/app_active" ] || echo "org.flippets.app/.PetActivity";;esac
}
am() { if [ "$1" = broadcast ];then rm -f "$TEST/app_active";echo closed >> "$TEST/closed";return;fi;touch "$TEST/app_active";if [ -f "$TEST/reject" ];then echo 'Error: test rejection';else echo "Starting: Intent $*" > "$TEST/launch";cat "$TEST/launch";fi; }
nohup() { :; }
. /data/local/tmp/flip-pets-fixture/control.sh
