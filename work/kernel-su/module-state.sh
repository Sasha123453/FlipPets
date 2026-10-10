#!/system/bin/sh
# Sourced only by root-owned module scripts. Durable consent is outside updates.
STATE=/data/adb/flippets-controller
state_private_dir() {
  [ -d "$1" ] && [ ! -L "$1" ] && [ "$(stat -c '%u:%a' "$1")" = '0:700' ]
}
state_root_file() {
  [ -f "$1" ] && [ ! -L "$1" ] && [ "$(stat -c '%u' "$1")" = 0 ] || return 1
  mode=$(stat -c '%a' "$1")
  case "$mode" in ''|*[!0-7]*|*[2367][0-7]|*[2367]) return 1 ;; esac
}
state_initialize() {
  # /data/adb is supplied by KernelSU, never created or chmodded by this module.
  [ -d /data/adb ] && [ ! -L /data/adb ] && [ "$(stat -c '%u' /data/adb)" = 0 ] || return 1
  parent_mode=$(stat -c '%a' /data/adb)
  case "$parent_mode" in ''|*[!0-7]*|*[2367][0-7]|*[2367]) return 1 ;; esac
  if [ ! -e "$STATE" ] && [ ! -L "$STATE" ]; then
    mkdir -m 700 "$STATE" || return 1
  fi
  state_private_dir "$STATE" || return 1
  # An interrupted first installation is safely initialized with no opt-in.
  if [ ! -e "$STATE/schema" ] && [ ! -L "$STATE/schema" ]; then
    for path in "$STATE/session-enabled" "$STATE/session-owned" "$STATE/session-cancel" "$STATE/runtime"; do
      [ ! -e "$path" ] && [ ! -L "$path" ] || return 1
    done
    (set -C; printf '1\n' > "$STATE/schema") || return 1
  fi
  state_root_file "$STATE/schema" && [ "$(cat "$STATE/schema")" = 1 ] || return 1
  for path in "$STATE/session-enabled" "$STATE/session-owned" "$STATE/session-cancel" "$STATE/session-transition"; do
    [ ! -e "$path" ] && [ ! -L "$path" ] || state_root_file "$path" || return 1
  done
  if [ ! -e "$STATE/runtime" ] && [ ! -L "$STATE/runtime" ]; then mkdir -m 700 "$STATE/runtime" || return 1; fi
  state_private_dir "$STATE/runtime"
}
umask 077
state_initialize || { echo 'Unsafe or unknown persistent root state; refusing operation' >&2; exit 1; }
