import pathlib,zipfile,json,hashlib,shutil,html,base64,datetime
r=pathlib.Path(__file__).resolve().parent;out=r.parent/'outputs';out.mkdir(exist_ok=True)
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while b:=f.read(4*1024*1024):h.update(b)
    return h.hexdigest()
def zip_files(target,items):
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4) as z:
        for p,name in items:z.write(p,str(name).replace('\\','/'))
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
cat=json.loads((r/'app/assets/catalog.json').read_text(encoding='utf-8'))
qa=json.loads((r/'qa-final/qa.json').read_text(encoding='utf-8'))
paths={path for p in cat for path in p['clips'].values()}
assert len(cat)==19 and len(paths)==170
assert qa['tested']==170 and qa['failed']==0
assert {x['path'] for x in qa['results']}==paths
with zipfile.ZipFile(out/'FlipPets.apk') as z:
    assert z.testzip() is None
    assert json.loads(z.read('assets/catalog.json'))==cat
    for path in paths:assert z.read('assets/'+path)==(r/'app/assets'/path).read_bytes()
    assert all(z.getinfo('assets/'+p).compress_type==zipfile.ZIP_STORED for p in paths if p.endswith('.mp4'))

# Module ZIP: root files, POSIX permissions, LF scripts, no system partition overlay.
shutil.copyfile(out/'flip-pets-control.sh',r/'ksu/control.sh')
with zipfile.ZipFile(out/'FlipPets-KernelSU-experimental.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted((r/'ksu').iterdir()):
        info=zipfile.ZipInfo(p.name);info.create_system=3;info.external_attr=((0o100755 if p.suffix=='.sh' else 0o100644)<<16);info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,p.read_bytes().replace(b'\r\n',b'\n'))
with zipfile.ZipFile(out/'FlipPets-KernelSU-experimental.zip') as z:
    assert z.testzip() is None and 'skip_mount' in z.namelist() and not any(n.startswith('system/') for n in z.namelist())

firmwares=[]
for p in sorted((r/'firmware').glob('*.verified.json')):
    f=json.loads(p.read_text());f['official_url']=f"https://bigota.d.miui.com/{f['version']}/{f['name']}";f['downloaded_file_relative_to_outputs']='../work/firmware/'+f['name'];assert pathlib.Path(f['path']).stat().st_size==f['size'];assert f['md5']==f['verified_md5'];firmwares.append(f)
(out/'Firmware-manifest.json').write_text(json.dumps(firmwares,ensure_ascii=False,indent=2),encoding='utf-8')

items=[(p,p.relative_to(r/'original-resources')) for p in (r/'original-resources').rglob('*') if p.is_file()]
items+=[(r/'jars/pandora-subscreencenter.apk','pandora-subscreencenter.apk'),(r/'research/pandora-rearscreen-inventory.json','pandora-rearscreen-inventory.json'),(r/'research/portable-resource-provenance.json','portable-resource-provenance.json')]
zip_files(out/'Original-Xiaomi-Resources.zip',items)

source=[]
for root in [r/'app',r/'ksu']:
    source.extend((p,p.relative_to(r.parent)) for p in root.rglob('*') if p.is_file())
source.extend((p,'outputs/'+p.name) for p in [out/'FlipPets-ADB.ps1',out/'flip-pets-control.sh'])
for name in ['build_apk.py','prepare_catalog.py','check_native.py','download_firmware.py','download_presets.py','read_erofs_file.py','SOURCE-README.txt','CODE-LICENSE.txt']:
    source.append((r/name,'work/'+name))
for p in (r/'tests').glob('*'):
    if p.is_file():source.append((p,'work/tests/'+p.name))
for name in ['portable-resource-provenance.json','ruyi-display_layout_configuration.xml','ruyi-product-device_state_configuration.xml']:
    source.append((r/'research'/name,'work/research/'+name))
source.append((r/'tools/libpag/classes.jar','work/tools/libpag/classes.jar'))
for abi in ['arm64-v8a','x86_64']:
    for p in (r/'tools/libpag/jni'/abi).glob('*.so'):source.append((p,p.relative_to(r.parent)))
zip_files(out/'FlipPets-Source.zip',source)

verification={
    'created':datetime.datetime.now().astimezone().isoformat(),
    'apk_sha256':digest(out/'FlipPets.apk'),
    'catalog_sets':len(cat),'clips':len(paths),'pag_clips':sum(p.endswith('.pag') for p in paths),'mp4_clips':sum(p.endswith('.mp4') for p in paths),
    'asset_qa':{'tested':qa['tested'],'failed':qa['failed'],'environment':'Android 16 / API 36, x86_64 emulator, PAG software decoder','method':'Each PAG rendered offscreen and each MP4 decoded at timeline positions 0.2 and 0.7; visible frames with differing SHA-256 pixels'},
    'apk_asset_integrity':'All 170 packaged clips equal the tested files byte for byte; APK and ZIP CRC checks pass',
    'apk_signature':'APK Signature Scheme v3; local RSA-3072 certificate; apksigner verify passed',
    'alignment':'APK zipalign -P 16 passed; both native libraries on both ABIs have 16384-byte ELF LOAD alignment',
    'ui_validation':{'two_displays':'MainActivity RESUMED on display 0; PetActivity RESUMED on display 3 (1208x1392 virtual display)','other_main_app':'Android Settings RESUMED on display 0 while PetActivity remains RESUMED on display 3','wallpaper':'Applied on emulator; both PAG with original clock/background and MP4 surface rendering observed','notification_listener':'System bound the notification listener on emulator; a synthetic notification posted; actual device event scenarios still require testing'},
    'controller_fixture_tests':json.loads((r/'qa-final/controller-tests.json').read_text()),
    'kernel_su':'Script syntax and ZIP structure validated; no real device installation or root-mode test',
    'hardware_validation':'Not performed: user MIX Flip is not connected; simultaneous physical displays and fold/sleep watcher behavior on HyperOS are unverified',
    'firmware_downloads':firmwares,
    'archive_presets':json.loads((r/'original-resources/archived-presets/provenance.json').read_text()),
    'selected_partition_extraction_evidence':[json.loads(p.read_text()) for p in (r/'images').rglob('*.verified-extraction.json')]
}
(out/'Verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf-8')
evidence=[(out/'Verification.json','Verification.json')]
for p in (r/'qa-final').glob('*'):
    if p.is_file():evidence.append((p,'emulator/'+p.name))
for name in ['ruyi-display_layout_configuration.xml','ruyi-product-device_state_configuration.xml','ruyi-DeviceStateManagerShellCommand.java','portable-resource-provenance.json','pandora-rearscreen-inventory.json']:
    evidence.append((r/'research'/name,'firmware-analysis/'+name))
evidence.append((r/'logs/build-release.log','build-release.log'))
zip_files(out/'Verification.zip',evidence)
shutil.copyfile(r/'qa-final/two-displays.png',out/'preview-two-displays.png')

def img(path):return 'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
cards=[]
for i,p in enumerate(cat):
    kind={'reactive':'Автоматические реакции','ambient':'Оригинальные сцены','video':'Видео'}[p['kind']]
    source='Из ROM 17 Pro' if p['source'].startswith('Xiaomi 17 Pro') else 'Из публичного архива пресетов'
    cards.append(f'<article><div class="thumb" style="background:linear-gradient({html.escape(p["gradientFrom"])},{html.escape(p["gradientTo"])})"><img src="{img(r/"qa-final"/f"pet-{i}.png")}" alt="{html.escape(p["name"])}"></div><h3>{html.escape(p["name"])}</h3><p>{kind} · {len(p["clips"])} клипов</p><small>{source}</small></article>')
firmware_rows=''.join(f'<tr><td>{"17 Pro · China · pandora" if f["device"]=="pandora" else "MIX Flip · Global · ruyi"}</td><td><a href="{f["official_url"]}">{f["version"]}</a></td><td>{f["size"]/1e9:.2f} ГБ</td></tr>' for f in firmwares)
page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Flip Pets — результат переноса</title><style>
*{box-sizing:border-box}body{margin:0;background:#111923;color:#edf1f6;font:16px/1.6 "Segoe UI",sans-serif}main{max-width:1080px;margin:auto;padding:46px 24px}h1{font-size:clamp(32px,6vw,60px);line-height:1.05;margin:12px 0 24px}h2{font-size:27px;margin:48px 0 16px}h3{margin:12px 0 4px}p{max-width:900px}a{color:#c4f56b}small,.muted{color:#b3bfcb}.badge{color:#c4f56b;text-transform:uppercase;letter-spacing:2px}.metrics{display:flex;flex-wrap:wrap;gap:12px;margin:28px 0}.metrics div{background:#203041;border-radius:16px;padding:16px 24px}.metrics b{font-size:30px;display:block}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px}.grid article{background:#203041;padding:14px;border-radius:16px}.thumb{height:280px;border-radius:10px;overflow:hidden}.thumb img{width:100%;height:100%;object-fit:contain}.grid p{margin:0;font-size:14px}.note{padding:18px 22px;background:#253447;border-left:4px solid #c4f56b;border-radius:6px}table{width:100%;border-collapse:collapse}td,th{padding:12px;text-align:left;border-bottom:1px solid #34465b}code{background:#203041;padding:3px 6px;border-radius:4px}pre{padding:16px;background:#203041;overflow:auto;border-radius:10px}.shot{max-width:330px;width:100%;border-radius:16px}ul{padding-left:22px}li{margin:8px 0}details{margin:16px 0}summary{cursor:pointer;color:#c4f56b}.downloads{display:flex;flex-wrap:wrap;gap:12px}.downloads a{padding:10px 16px;background:#203041;border-radius:10px;text-decoration:none}
</style><main><div class="badge">Локальный перенос · 3 октября 2026</div><h1>Питомцы 17 Pro<br>для MIX Flip</h1><p>Собрано приложение без root с оригинальными анимациями Xiaomi, отдельным экраном и живыми обоями. Для двух физических экранов подготовлен запуск штатного режима через ADB и запасной модуль KernelSU.</p>
<div class="metrics"><div><b>19</b>наборов</div><div><b>170</b>клипов</div><div><b>170 / 170</b>отрисованы в эмуляторе</div><div><b>ADB</b>первый вариант запуска</div></div>
<div class="note">Главное ограничение: настоящий MIX Flip ещё не подключался. Код и ресурсы проверены на Android 16 с виртуальными экранами. Работа обоих физических дисплеев на установленной у тебя сборке HyperOS остаётся первым аппаратным тестом.</div>
<h2>Что взять для первой пробы</h2><div class="downloads"><a href="FlipPets.apk">APK · 257 МиБ</a><a href="START-HERE.txt">Инструкция</a><a href="FlipPets-ADB.ps1">Скрипт ADB</a><a href="FlipPets-KernelSU-experimental.zip">KernelSU · экспериментальный</a></div><p>Сначала установи APK и проверь Bubbles или Roe в полноэкранном просмотре. Затем подключи USB, собери диагностику и попробуй <code>Start</code> при полностью раскрытом и разблокированном телефоне. Получать root для этой первой пробы не нужно. Все команды и возврат режима описаны в <a href="START-HERE.txt">инструкции</a>.</p>
<h2>Что работает в приложении</h2><table><tr><th>Функция</th><th>Реализация</th></tr><tr><td>Оригинальная графика</td><td>19 наборов PAG/MP4, включая питомцев, Lumi, Peeko, блёстки и системные эффекты. Файлы клипов не перерисованы.</td></tr><tr><td>Автоматические события</td><td>У Bubbles и Roe: зарядка, низкий заряд, уведомления, активная музыка, ходьба/бег. Музыке и уведомлениям нужен доступ к уведомлениям, шагам — разрешение и датчик.</td></tr><tr><td>Касания и сцены</td><td>Оригинальные клипы выбираются вручную или касанием. Жесты и NFC представлены как просмотр графики; распознавание жестов камерой и платёжная интеграция отсутствуют.</td></tr><tr><td>Часы и фон</td><td>Использованы исходные цифры/шрифты/фоны, расположение адаптировано под экран MIX Flip. Для некоторых наборов применён обычный шрифт. Компоновка требует проверки относительно физических камер.</td></tr><tr><td>Живые обои</td><td>Штатный WallpaperService Android. PAG с фоном/часами и MP4 протестированы на эмуляторе. Видео в обоях масштабируется с обрезкой; в полноэкранном просмотре сохраняет весь кадр.</td></tr><tr><td>Два экрана</td><td>Независимая PetActivity на втором доступном дисплее. Основной экран остаётся для других приложений. Физический второй дисплей должен открыть HyperOS.</td></tr></table>
<p>Полный системный перенос «один в один» не завершён: нет диалогового ИИ Xiaomi, AON-распознавания камерой, автоматической погоды, игровых виджетов, NFC-платежей и подключения к фирменным службам. У блёсток доступны четыре оригинальных эффекта со встроенным фоном; выбор собственных фотографий и управление наклоном не перенесены. Lumi и Peeko воспроизводят оригинальные видео без ИИ. Панда и Peanut в скачанных наборах не найдены.</p>
<p>Формат результата — APK и живые обои. Готовой MTZ-темы для импорта в Global Themes нет: перенос MRC сам по себе не воспроизводит системные привязки, доверие пакетов и управление дисплеями. Простая подмена SubScreenCenter 17 Pro в MIX Flip также не выполнена: она требует анализа зависимостей и фактической прошивки телефона.</p>
<h2>Почему есть шанс обойтись ADB</h2><p>В ODM-конфигурации исследованного MIX Flip режим <code>OPENED_PRESENTATION</code>, идентификатор <code>5</code>, включает оба встроенных дисплея и оставляет внутренний главным. В PRODUCT-конфигурации он помечен <code>PROPERTY_APP_INACCESSIBLE</code>, поэтому APK не может запросить его сам. При этом извлечённый из той же прошивки <code>DeviceStateManagerShellCommand</code> использует <code>Binder.clearCallingIdentity()</code> перед запросом состояния. Это подтверждает наличие системного пути через <code>cmd device_state state 5</code>, но не результат на твоём аппарате.</p>
<p>Контроллер проверяет модель <code>ruyi</code> и наличие режима, подбирает ID внешнего экрана по разрешению, запускает собственный APK и отменяет запрос при ошибке. Отдельный процесс проверяет складывание и засыпание с интервалом около двух секунд. Запрос временный, без автозапуска после перезагрузки. Модуль KernelSU вызывает тот же путь с root и не изменяет разделы или ядро. Он пока не проверен на устройстве; root не является гарантией, что иной отказ прошивки исчезнет.</p>
<h2>Прошивки и происхождение ресурсов</h2><table><tr><th>Аппарат</th><th>Официальный пакет</th><th>Размер</th></tr>FIRMWARE_ROWS</table><p>Оба полных ZIP скачаны, MD5 совпадает с опубликованными значениями, SHA-256 сохранён. Пути файлов и хеши: <a href="Firmware-manifest.json">Firmware-manifest.json</a>. ROM 17 Pro используется как донор ресурсов, а не как прошивка для MIX Flip.</p>
<p>Из PRODUCT 17 Pro извлечены 31 MRC и 31 MRM заднего экрана, а из SubScreenCenter — два дополнительных PAG. Часть новых питомцев находится в отдельном <a href="https://github.com/NekoStash/REAREye-Preset-Resources/tree/131660290ad7c7c5577c1adf741bc3afbf5044c7">публичном архиве пресетов Xiaomi</a>: скачаны 11 MRC и 11 MRM, проверены размеры и Git blob SHA-1 по зафиксированному коммиту. Эти пресеты не выдаются за извлечённые из выбранного ROM. Полностью совпадающие наборы исключены из каталога.</p>
<h2>Каталог оригинальных клипов</h2><p class="muted">Кадры получены из файлов на эмуляторе; это не фотографии экрана MIX Flip. Цвет фона карточек взят из пресета. «Классический» обозначает отдельный вариант из ROM, а не дубликат нового набора.</p><div class="grid">CARDS</div>
<h2>Что проверено</h2><ul><li>Все 170 файлов загружаются и дают видимые, различающиеся кадры в двух точках времени. Ошибок: 0. Для PAG использован программный декодер; аппаратный режим Snapdragon ещё не проверен.</li><li>В итоговом APK клипы побайтово совпадают с протестированными. MP4 упакованы без сжатия, чтобы Android мог открыть их через файловый дескриптор.</li><li>APK установился на Android 16; подпись v3, выравнивание ZIP и ELF для 16 КиБ проверены.</li><li>Две Activity одновременно RESUMED на двух виртуальных экранах. При открытии Android Settings на основном экране PetActivity остаётся RESUMED на втором.</li><li>Живые обои PAG и MP4 применены на эмуляторе; проверено переключение между ними. Служба уведомлений связалась с Android; полноценные сценарии музыки и уведомлений на HyperOS требуют телефона.</li><li>Тесты приоритетов событий, истечения реакций и устранения дублирующихся шагов от двух экранов прошли.</li><li>Восемь проверок ADB-контроллера с моделированными ответами команд: запуск, выбор дисплея, остановка, складывание, засыпание, откат ошибки, чужой запрос и неверная модель.</li><li>Проверены синтаксис shell/PowerShell и структура ZIP KernelSU. Установка модуля на устройство не выполнялась.</li></ul>
<details><summary>Скриншоты проверки двух экранов и обоев</summary><p>Полупрозрачный прямоугольник — виртуальный внешний экран Android Emulator.</p><img class="shot" src="TWO_SHOT" alt="Приложение на двух виртуальных экранах"><img class="shot" src="OTHER_SHOT" alt="Android Settings на основном экране, питомец на втором"><img class="shot" src="WALL_SHOT" alt="Живые обои с коалой и оригинальными часами"></details>
<h2>Оставшиеся проверки на телефоне</h2><p>Точная версия и регион установленной HyperOS; допуск ADB к состоянию 5; независимость внешнего экрана от внутреннего; запуск приложения на нём; складывание, сон и возврат обычного режима; камеры и вырезы; аппаратный PAG/MP4-декодер; шаги, музыка и уведомления; нагрев и расход батареи. Для первого теста оставь USB подключённым. Если Start не сработает, нужны <code>phone-diagnostics.txt</code> и полный текст ошибки — инструкция содержит Stop и аварийный reset.</p>
<h2>Исходники и доказательства</h2><div class="downloads"><a href="FlipPets-Source.zip">Исходники и ресурсы APK</a><a href="Original-Xiaomi-Resources.zip">Исходные Xiaomi-ресурсы</a><a href="Verification.zip">Отчёт и доказательства проверок</a><a href="Verification.json">JSON проверок</a><a href="checksums.sha256">SHA-256 готовых файлов</a></div>
<p>Сборка локальная, без INTERNET-разрешения. Тексты уведомлений не сохраняются. Содержимое ресурсных архивов остаётся собственностью исходных авторов; лицензия локального кода не распространяется на графику Xiaomi. <a href="https://github.com/Tencent/libpag/tree/v4.5.98">libpag 4.5.98</a> и лицензии зависимостей включены в исходники и APK. Модуль оформлен по <a href="https://kernelsu.org/guide/module.html">документации KernelSU</a>, адаптация приложения учитывает <a href="https://dev.mi.com/xiaomihyperos/documentation/detail?pId=2026">документацию Xiaomi для внешнего экрана</a>.</p></main></html>'''
for key,value in {'FIRMWARE_ROWS':firmware_rows,'CARDS':''.join(cards),'TWO_SHOT':img(r/'qa-final/two-displays.png'),'OTHER_SHOT':img(r/'qa-final/main-other-app.png'),'WALL_SHOT':img(r/'qa-wallpaper-pag.png')}.items():page=page.replace(key,value)
(out/'report.html').write_text(page,encoding='utf-8')
hashes=[]
for p in sorted(out.iterdir()):
    if p.is_file() and p.name!='checksums.sha256':hashes.append(digest(p)+'  '+p.name)
(out/'checksums.sha256').write_text('\n'.join(hashes)+'\n',encoding='utf-8')
print(json.dumps({'sets':len(cat),'clips':len(paths),'qa_failed':qa['failed'],'files':[{'name':p.name,'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file()]},ensure_ascii=False,indent=2))
