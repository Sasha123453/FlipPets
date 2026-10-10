#!/system/bin/sh
MODDIR=${0%/*}
exec /system/bin/sh "$MODDIR/module-control.sh" toggle
