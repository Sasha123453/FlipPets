"""Real gallery UI and rendered-window evidence on guarded emulator-5554 only.

Run separately from other device suites. Restores the selected design, touched
favorite and display/font overrides. Does not read/import any private photo.
"""
from device_qa import *
import device_qa
import argparse
import hashlib
import json


def ui(name='ui'):
    # Capture current accessibility windows without uiautomator's idle wait:
    # an animated WebView need not ever become globally idle.
    remote = '/sdcard/Android/data/org.flippets.uiqa/files/primary-ui.xml'
    for attempt in range(3):
        shell('rm -f '+remote)
        output = shell('am instrument -w org.flippets.uiqa/.DumpUi')
        assert 'Own primary display UI captured.' in output, output
        adb('pull', remote, QA/(name+'.xml'))
        tree = ET.parse(QA/(name+'.xml')).getroot()
        if tree.find('node') is not None:
            return tree
        time.sleep(.2)
    raise RuntimeError('Own window accessibility root was not ready')


device_qa.ui = ui


def bounds(node):
    return tuple(map(int, re.findall(r'\d+', node.get('bounds'))))


def click(node):
    x, y, right, bottom = bounds(node)
    assert right > x and bottom > y
    shell(f'input -d 0 tap {(x + right)//2} {(y + bottom)//2}')
    time.sleep(.4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--windows-only", action="store_true", help="Check only large-font and small-window gallery layouts")
    args = parser.parse_args()
    guard()
    assert shell('getprop ro.hardware').strip() in ('ranchu', 'goldfish')
    apk = ROOT.parent / 'outputs/FlipPets.apk'
    binary = hashlib.sha256(apk.read_bytes()).hexdigest()
    installed = shell('pm path org.flippets.app').strip().removeprefix('package:')
    assert shell('sha256sum ' + installed).split()[0] == binary
    helper = ROOT/'uiqa-build/uiqa.apk'
    print(adb('install', '--no-incremental', '-r', helper), flush=True)
    old_size = re.search(r'Override size:\s*(\d+x\d+)', shell('wm size'))
    old_density = re.search(r'Override density:\s*(\d+)', shell('wm density'))
    old_font = shell('settings get system font_scale').strip()
    old_overlay = shell('settings get global overlay_display_devices').strip()
    assert old_overlay in ('', 'null'), 'Run with no pre-existing virtual display'
    rows, images = [], []
    original, favorite_changed, selection_restored = None, False, False

    def check(name, passed):
        rows.append(dict(test=name, ok=bool(passed)))
        print(name, bool(passed), flush=True)
        assert passed, name

    def shot(name):
        screenshot(name)
        images.append(dict(file=name+'.png', sha256=hashlib.sha256((QA/(name+'.png')).read_bytes()).hexdigest()))

    def start():
        shell('am force-stop org.flippets.app')
        # Clear only our stale Main QA task/launch extras.
        for block in shell('am stack list').split('RootTask'):
            tasks = [line for line in block.splitlines() if 'taskId=' in line]
            identity = re.search(r'^\s+id=(\d+)\b', block)
            if identity and tasks and all('org.flippets.app/.MainActivity' in line or 'org.flippets.app/org.flippets.app.MainActivity' in line for line in tasks):
                shell('am stack remove '+identity[1])
        shell('am start --display 0 -n org.flippets.app/.MainActivity -f 0x10008000')
        deadline = time.monotonic()+30
        while time.monotonic() < deadline:
            try:
                if any(n.get('text') == 'СЕЙЧАС НА ЭКРАНЕ' for n in ui('gallery-ready').iter('node')):
                    return
            except RuntimeError:
                # Font/window changes recreate Main and its accessibility root.
                # Retry a fresh snapshot within the launch deadline, never stale XML.
                pass
            time.sleep(.3)
        raise TimeoutError('Main window did not become ready')

    def selected():
        tree = ui('gallery-main')
        nodes = list(tree.iter('node'))
        i = next(i for i, n in enumerate(nodes) if n.get('text') == 'СЕЙЧАС НА ЭКРАНЕ')
        return next(n.get('text') for n in nodes[i+1:] if n.get('text'))

    def open_gallery():
        for _ in range(8):
            tree = ui('gallery-launch')
            target = next((n for n in tree.iter('node') if n.get('text') == 'Выбрать оформление'), None)
            if target is not None:
                click(target)
                return
            size = shell('wm size').strip().splitlines()[-1].split(':')[-1].strip()
            w, h = map(int, size.split('x'))
            shell(f'input -d 0 swipe {w//2} {h*4//5} {w//2} {h//3} 300')
        raise AssertionError('Gallery button not found')

    def choose(name, row=0):
        for direction in (1, -1):
            for _ in range(7):
                tree = ui('gallery-controls')
                scrolls = [n for n in tree.iter('node') if n.get('class') == 'android.widget.HorizontalScrollView']
                area = scrolls[row]
                target = next((n for n in area.iter('node') if n.get('text') == name and bounds(n)[2]-bounds(n)[0] > 30), None)
                if target is not None:
                    click(target)
                    return
                x, y, right, bottom = bounds(area)
                left, end = x+20, right-20
                if direction < 0:
                    left, end = end, left
                shell(f'input -d 0 swipe {end} {(y+bottom)//2} {left} {(y+bottom)//2} 250')
        raise AssertionError('Chip not found: '+name)

    def count(name, expected):
        texts = [n.get('text', '') for n in ui('gallery-count').iter('node')]
        passed = any(t.startswith(f'Найдено: {expected} ·') for t in texts) if expected else any(t.startswith('Ничего не найдено') for t in texts)
        check(name, passed)

    def search(value):
        field = next(n for n in ui().iter('node') if n.get('class') == 'android.widget.EditText')
        click(field)
        shell('input keycombination KEYCODE_CTRL_LEFT KEYCODE_A')
        shell('input keyevent KEYCODE_DEL')
        if value:
            assert value.isascii() and value.isalnum()
            shell('input text '+value)
        shell('input keyevent KEYCODE_BACK')
        time.sleep(.3)

    def favorite():
        return next(n for n in ui().iter('node') if n.get('content-desc', '').endswith(': Pomodoro Xiaomi'))

    def card(title):
        return next(n for n in ui().iter('node') if title+'.' in n.get('content-desc', '') and n.get('class') == 'android.widget.LinearLayout')

    def dialog_button(number):
        # Material accessibility exposes transformed ALL-CAPS button labels.
        target = next(n for n in ui().iter('node') if n.get('resource-id') == f'android:id/button{number}' and n.get('package') == 'org.flippets.app')
        click(target)

    def select_title(title, apply=False):
        open_gallery()
        for _ in range(30):
            tree = ui()
            target = next((n for n in tree.iter('node') if title+'.' in n.get('content-desc', '') and n.get('class') == 'android.widget.LinearLayout'), None)
            if target is not None:
                click(target)
                if apply:
                    dialog_button(1)
                return
            shell('input -d 0 swipe 700 2600 700 1300 250')
        raise AssertionError('Design not found: '+title)

    try:
        shell('wm size 1224x2912'); shell('wm density 520')
        shell('settings put system font_scale 1.0')
        if not args.windows_only:
            start(); original = selected(); open_gallery()
            count('all_collection', 36)
            for name, expected in [('18 Pro', 6), ('Свои', 4), ('Архив Xiaomi', 8), ('17 Pro', 18)]:
                choose(name); count('collection_'+name, expected)
            choose('18 Pro'); choose('Мини-приложения', 1); count('18pro_mini_intersection', 3)
            choose('17 Pro'); count('17pro_mini_empty', 0)
            choose('Свои'); count('personal_mini_empty', 0)
            choose('18 Pro'); search('Pomodoro'); count('scoped_search', 1)
            star = favorite()
            original_favorite = star.get('content-desc', '').startswith('Убрать')
            click(star); favorite_changed = True
            choose('Избранное', 1); count('favorites_search_intersection', 0 if original_favorite else 1)
            choose('17 Pro'); count('favorites_stay_in_collection', 0)
            choose('18 Pro'); choose('Все типы', 1)
            click(favorite()); favorite_changed = False
            check('favorite_restored', favorite().get('content-desc', '').startswith('Убрать') == original_favorite)
            click(card('Pomodoro Xiaomi'))
            check('mini_opens_preview', any(n.get('resource-id') == 'android:id/button1' and n.get('text', '').casefold() == 'На внешний экран'.casefold() for n in ui().iter('node')))
            for name, label in [('focus', 'Фокус'), ('water', 'Вода'), ('words', 'Слова')]:
                tap_text(label); shot('mini-dialog-'+name)
            dialog_button(2); check('cancel_keeps_selection', selected() == original)
            select_title('Pomodoro Xiaomi', apply=True)
            check('apply_selects_mini', selected() == 'Pomodoro Xiaomi')
            shot('mini-applied-main')
            shell('settings put global overlay_display_devices 1208x1392/520')
            time.sleep(2)
            display = max(map(int, re.findall(r'mDisplayId=\s*(\d+)', shell('dumpsys display'))))
            assert display > 0
            physical = re.search(r'Display (\d+) \(Virtual display\): displayName="Overlay #1"', shell('dumpsys SurfaceFlinger --display-id'))[1]
            shell(f'am start --display {display} -n org.flippets.app/.PetActivity -f 0x18008000')
            time.sleep(2)
            check('virtual_cover_activity_visible', any(f'displayId={display} ' in b and 'org.flippets.app.PetActivity' in b and 'visible=true' in b for b in shell('am stack list').split('RootTask')))
            for label, x in [('focus', 560), ('water', 800), ('words', 1050)]:
                shell(f'input -d {display} tap {x} 130')
                time.sleep(1)
                name = 'mini-virtual-cover-'+label
                shell(f'screencap -d {physical} -p /sdcard/flip-card-cover.png')
                adb('pull', '/sdcard/flip-card-cover.png', QA/(name+'.png'))
                images.append(dict(file=name+'.png', sha256=hashlib.sha256((QA/(name+'.png')).read_bytes()).hexdigest()))
            shell('settings put global overlay_display_devices ""')
            start()
            select_title('Charlie')
            check('pet_selection_clears_mini', selected() == 'Charlie')
            # Original selection is restored by real gallery selection below.
            select_title(original, original in ('Pomodoro Xiaomi', 'Вода Xiaomi', 'Слова Xiaomi'))
            check('normal_selection_and_restore', selected() == original)
            open_gallery(); choose('18 Pro'); shot('gallery-main-18pro')
            tap_text('Готово')
        else:
            start(); original = selected()
        for size, font, label in [('1224x2912', '1.3', 'large-font'), ('1208x1392', '1.0', 'small-window')]:
            shell('wm size '+size); shell('settings put system font_scale '+font)
            start(); open_gallery(); choose('18 Pro'); shot('gallery-'+label)
            check(label+'_grid_visible', any(n.get('class') == 'android.widget.GridView' and bounds(n)[3] > bounds(n)[1] for n in ui().iter('node')))
            tap_text('Готово')
    except Exception as error:
        rows.append(dict(test='unexpected_error', ok=False, detail=type(error).__name__+': '+str(error)))
        raise
    finally:
        try:
            if original is not None:
                shell('wm size 1224x2912'); shell('settings put system font_scale 1.0')
                start()
                if favorite_changed:
                    open_gallery(); search('Pomodoro'); click(favorite())
                    favorite_changed = False
                    tap_text('Готово')
                if selected() != original:
                    select_title(original, original in ('Pomodoro Xiaomi', 'Вода Xiaomi', 'Слова Xiaomi'))
                selection_restored = selected() == original
                assert selection_restored
        except Exception as error:
            rows.append(dict(test='cleanup_restore', ok=False, detail=str(error)))
        shell('am force-stop org.flippets.app', check=False)
        adb('uninstall', 'org.flippets.uiqa', check=False)
        shell('settings '+('delete global overlay_display_devices' if old_overlay == 'null' else 'put global overlay_display_devices ""'), check=False)
        shell('wm size '+(old_size[1] if old_size else 'reset'), check=False)
        shell('wm density '+(old_density[1] if old_density else 'reset'), check=False)
        shell('settings '+('delete system font_scale' if old_font == 'null' else 'put system font_scale '+old_font), check=False)
        report = dict(apkSha256=binary, environment='Guarded Android emulator; real UI input and screencap, not physical MIX Flip', originalSelection=original, tested=len(rows), failed=sum(not r['ok'] for r in rows), results=rows, images=images, cleanup=dict(favoriteRestored=not favorite_changed, selectionRestored=selection_restored))
        (QA/('gallery-windows-qa.json' if args.windows_only else 'gallery-qa.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    assert not report['failed'], report


if __name__ == '__main__':
    main()
