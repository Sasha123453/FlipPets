"""Real stock collection Apply/Cancel and screenshots on guarded emulator only."""
from device_qa import *
from run_gallery_qa import ui,bounds,click
import hashlib,json


def main():
    guard();assert shell('getprop ro.hardware').strip() in ('ranchu','goldfish')
    binary=hashlib.sha256((ROOT.parent/'outputs/FlipPets.apk').read_bytes()).hexdigest()
    installed=shell('pm path org.flippets.app').strip().removeprefix('package:');assert shell('sha256sum '+installed).split()[0]==binary
    print(adb('install','--no-incremental','-r',ROOT/'uiqa-build/uiqa.apk'),flush=True)
    old_size=re.search(r'Override size:\s*(\d+x\d+)',shell('wm size'));old_density=re.search(r'Override density:\s*(\d+)',shell('wm density'))
    rows=[];original=None;changed=False
    def check(name,ok):rows.append(dict(test=name,ok=bool(ok)));print(name,ok,flush=True);assert ok,name
    def button(text):
        for _ in range(12):
            target=next((n for n in ui().iter('node') if n.get('text')==text),None)
            if target is not None:click(target);return
            shell('input -d 0 swipe 900 2400 900 1000 250')
        raise AssertionError('Button not found')
    def selected():
        for _ in range(5):
            nodes=list(ui().iter('node'));index=next((i for i,n in enumerate(nodes) if n.get('text')=='СЕЙЧАС НА ЭКРАНЕ'),None)
            if index is not None:return next(n.get('text') for n in nodes[index+1:] if n.get('text'))
            shell('input -d 0 swipe 900 800 900 2600 400')
        raise AssertionError('Main selection label not visible after bounded scrolling')
    def count(n):
        texts=[x.get('text','') for x in ui().iter('node')]
        return any(t.startswith('Найдено: '+str(n)+' ·') for t in texts) if n else any(t.startswith('Ничего не найдено') for t in texts)
    def action(number):click(next(n for n in ui().iter('node') if n.get('resource-id')=='android:id/button'+str(number)))
    def card(title):
        for _ in range(25):
            target=next((n for n in ui().iter('node') if title+'.' in n.get('content-desc','') and n.get('class')=='android.widget.LinearLayout'),None)
            if target is not None:click(target);return
            shell('input -d 0 swipe 800 2500 800 1300 250')
        raise AssertionError('Card not found')
    def search(value):
        click(next(n for n in ui().iter('node') if n.get('class')=='android.widget.EditText'));shell('input keycombination KEYCODE_CTRL_LEFT KEYCODE_A');shell('input keyevent KEYCODE_DEL')
        if value:shell('input text '+value)
        shell('input keyevent KEYCODE_BACK');time.sleep(.2)
    try:
        shell('wm size 1224x2912');shell('wm density 520');shell('am force-stop org.flippets.app');shell('am start -W --display 0 -n org.flippets.app/.MainActivity -f 0x10008000');time.sleep(2)
        original=selected();button('Выбрать оформление');button('MIX Flip');check('collection_six',count(6))
        search('Flip');check('source_search_scoped',count(6));search('Pomodoro');check('search_excludes_other_collection',count(0));search('')
        card('Капибара');check('stock_opens_explicit_apply',any(n.get('resource-id')=='android:id/button1' for n in ui().iter('node')));action(2)
        button('Готово');check('cancel_keeps_selection',selected()==original)
        button('Выбрать оформление');button('MIX Flip');card('Капибара');action(1);changed=True;check('apply_selects_open_mode',selected()=='Капибара');screenshot('mixflip-capybara-main')
        button('Питомцы на штатной блокировке');check('native_controls_separate',any('3 питомцев' in n.get('text','') for n in ui().iter('node')));action(2);shell('input -d 0 swipe 900 800 900 2500 250');check('native_dialog_does_not_select_pet',selected()=='Капибара')
    finally:
        if changed and original:
            shell('input -d 0 keyevent KEYCODE_BACK');shell('am start -W --display 0 -n org.flippets.app/.MainActivity -f 0x10008000');time.sleep(1);button('Выбрать оформление')
            if original in ('Девон-рекс','Капибара','Выдра','Бишон-фризе','Сиамская кошка','Чёрная пантера'):button('MIX Flip')
            card(original)
            if any(n.get('resource-id')=='android:id/button1' for n in ui().iter('node')):action(1)
            check('selection_restored',selected()==original)
        shell('wm size '+(old_size[1] if old_size else 'reset'));shell('wm density '+(old_density[1] if old_density else 'reset'));shell('am force-stop org.flippets.app');adb('uninstall','org.flippets.uiqa',check=False)
        (QA/'device-files/mixflip-gallery-qa.json').write_text(json.dumps(dict(apkSha256=binary,tested=len(rows),failed=sum(not r['ok'] for r in rows),results=rows),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
