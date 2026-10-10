#!/system/bin/sh
[ "$KSU" = "true" ] || [ "$KSU" = "1" ] || abort "This package targets KernelSU."
[ "$(getprop ro.product.device)" = "ruyi" ] || abort "Only Xiaomi MIX Flip (ruyi) is supported."
ui_print "Flip Pets experimental controller · no framework or partition changes"
ui_print "Install the matching FlipPets.apk separately; no app data is replaced."
ui_print "After reboot, use Action to opt in. Folding, lock and sleep stay stock."
ui_print "Independent rear-screen power is NOT implemented by this module."
set_perm_recursive "$MODPATH" 0 0 0755 0644
for script in "$MODPATH"/*.sh; do set_perm "$script" 0 0 0755; done
