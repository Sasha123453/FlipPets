"""Choose default no-card view through actual app settings, emulator only."""
from device_qa import *
guard()
shell('input -d 0 keyevent KEYCODE_WAKEUP');shell('wm dismiss-keyguard');shell('cmd statusbar collapse')
shell('am start --display 0 -n org.flippets.app/.MainActivity');time.sleep(1)
found=False
for _ in range(8):
    tree=ui('visual-settings-v09')
    if any(n.get('text')=='Настройки и доступы' for n in tree.iter('node')):found=True;break
    shell('input -d 0 swipe 610 2380 610 800 350');time.sleep(.3)
assert found
tap_text('Настройки и доступы');tap_text('Визуальный таймер');tap_text('Выключена')
shell('input -d 0 keyevent KEYCODE_BACK')
print('Optional card set none through real app UI')
