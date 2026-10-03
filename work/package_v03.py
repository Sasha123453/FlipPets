"""Rootless release; preserve original artwork and bind evidence to this APK."""
import pathlib,zipfile,json,hashlib,html,base64,shutil
R=pathlib.Path(__file__).resolve().parent;OUT=R.parent/'outputs';Q=R/'qa-v03'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while b:=f.read(4*1024*1024):h.update(b)
    return h.hexdigest()
def pack(dest,items):
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
        for p,name in items:z.write(p,str(name).replace('\\','/'))
    with zipfile.ZipFile(dest) as z:assert z.testzip() is None
catalog=read(R/'app/assets/catalog.json');paths={v for p in catalog for v in p['clips'].values()}
assert len(catalog)==30 and len(paths)==170
binary=sha(OUT/'FlipPets.apk')
qa={name:read(Q/'device-files'/name) for name in ['qa.json','composition-qa.json','ui-switch-qa.json']}
for name,count in [('qa.json',170),('composition-qa.json',68),('ui-switch-qa.json',15)]:
    assert qa[name]['apkSha256']==binary and qa[name]['tested']==count and qa[name]['failed']==0
assert {x['path'] for x in qa['qa.json']['results']}==paths
assert (OUT/'flip-pets-control.sh').read_bytes()==(R/'app/assets/controller.sh').read_bytes()
with zipfile.ZipFile(OUT/'FlipPets.apk') as z:
    assert z.testzip() is None
    assert read(R/'app/assets/catalog.json')==json.loads(z.read('assets/catalog.json'))
    files=[p for p in (R/'app/assets').rglob('*') if p.is_file()]
    for p in files:assert z.read('assets/'+p.relative_to(R/'app/assets').as_posix())==p.read_bytes(),p
    for path in paths:
        if path.endswith('.mp4'):assert z.getinfo('assets/'+path).compress_type==zipfile.ZIP_STORED
for scene in read(R/'research/composition-provenance.json'):
    for path,expected in scene['assets'].items():assert sha(R/'app/assets'/scene['assetRoot']/path)==expected
profile=read(Q/'resource-profile.json');assert profile['apkSha256']==binary
controller=read(R/'qa-final/controller-tests.json');supervisor=read(R/'qa-v02/supervisor-tests.json')
assert all(x['ok'] for x in supervisor['results'])
verification=dict(version='0.4',apkSha256=binary,catalogSets=30,originalClips=170,pagClips=sum(p.endswith('.pag') for p in paths),mp4Clips=sum(p.endswith('.mp4') for p in paths),offlineCompositions=11,originalImages=497,compiledNinePatches=110,originalFonts=5,
    environment='Android 16 / API 36 x86_64 emulator; virtual displays only; MIX Flip not connected',
    assetTests=qa,allApkAssetsByteIdenticalToSources=True,compositionImageHashesVerified=True,
    apkSignature='apksigner verify: v3 RSA-3072 local certificate; zipalign -P 16; 16KiB ELF LOAD alignment both ABIs',
    controllerFixtureTests=controller,supervisorFixtureTests=supervisor,
    shizuku='Actual official Shizuku shell server and UserService tested on emulator; UID 2000 verified; request from app allowed; non-ruyi start refused; status/stop checked. Fold/display commands themselves use fixtures.',
    resourceProfile=profile,lifecycle=read(Q/'lifecycle.json'),
    hardwareUnverified='Simultaneous physical displays, Xiaomi activity allowstart, keyguard parsing, fold/sleep timing, physical camera cutouts, hardware video decode, battery and temperature on MIX Flip require a real phone.',
    firmware=read(OUT/'Firmware-manifest.json'),coverage=read(R/'research/MRC-coverage.json'),fontProvenance=read(R/'research/font-provenance.json'))
(OUT/'Verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copyfile(Q/'resource-profile.json',OUT/'resource-profile.json')
evidence=[(OUT/'Verification.json','Verification.json')]+[(p,'emulator/'+p.relative_to(Q).as_posix()) for p in Q.rglob('*') if p.is_file() and 'device-files/files/' not in p.relative_to(Q).as_posix()]
evidence += [(R/'qa-v02/supervisor-tests.json','tests/supervisor-tests.json'),(R/'qa-final/controller-tests.json','tests/controller-tests.json'),(R/'logs/build-v03.log','build-v03.log')]
for n in ['ruyi-display_layout_configuration.xml','ruyi-product-device_state_configuration.xml','ruyi-DeviceStateManagerShellCommand.java','MRC-coverage.json','composition-provenance.json','font-provenance.json','portable-resource-provenance.json']:
    evidence.append((R/'research'/n,'firmware-analysis/'+n))
pack(OUT/'Verification.zip',evidence)
source=[(p,p.relative_to(R.parent)) for p in (R/'app').rglob('*') if p.is_file()]
for n in ['build_apk.py','prepare_catalog.py','prepare_compositions.py','inspect_compositions.py','check_native.py','download_firmware.py','download_presets.py','read_erofs_file.py','SOURCE-README.txt','CODE-LICENSE.txt','package_v03.py']:
    source.append((R/n,'work/'+n))
source += [(p,'work/tests/'+p.name) for p in (R/'tests').glob('*') if p.is_file()]
source += [(p,'work/research/'+p.name) for p in (R/'research').glob('*') if p.is_file() and (p.suffix=='.json' or p.name.startswith('ruyi-'))]
source += [(p,p.relative_to(R.parent)) for p in (R/'tools/libpag').rglob('*') if p.is_file() and (p.suffix in ('.jar','.so') or 'license' in p.name.lower())]
source += [(p,p.relative_to(R.parent)) for p in (R/'tools/shizuku').glob('*') if p.is_file() and p.suffix in ('.jar','.pom','.aar')]
source += [(OUT/n,'outputs/'+n) for n in ['flip-pets-control.sh','FlipPets-ADB.ps1','START-HERE.txt']]
pack(OUT/'FlipPets-Source.zip',source)
original=[(p,p.relative_to(R/'original-resources')) for p in (R/'original-resources').rglob('*') if p.is_file()]
original += [(R/'jars/pandora-subscreencenter.apk','pandora-subscreencenter.apk')]
original += [(p,'fonts/'+p.name) for p in (R/'app/assets/fonts').iterdir() if p.is_file()]
original += [(R/'research'/n,n) for n in ['MRC-coverage.json','font-provenance.json','composition-provenance.json','pandora-rearscreen-inventory.json','portable-resource-provenance.json']]
pack(OUT/'Original-Xiaomi-Resources.zip',original)
escape=html.escape
cards=[]
for p in catalog:
    image=R/'app/assets/thumbs'/(p['id']+'.webp');encoded=base64.b64encode(image.read_bytes()).decode()
    kind='Композиция · настройки, текст, фото' if p['kind']=='composition' else str(len(p['clips']))+' оригинальных сцен'
    cards.append(f'<article><img loading="lazy" src="data:image/webp;base64,{encoded}" alt="{escape(p["name"])}"><h3>{escape(p["name"])}</h3><p>{kind}</p></article>')
rows=''.join(f'<tr><td>{escape(x["scenario"])}</td><td>{x.get("cpuPercentOneCore",0):.2f}%</td><td>{x.get("pssKiB",0)/1024:.1f} МиБ</td></tr>' for x in profile['results'])
firmwares=''.join(f'<li>{escape(f["device"])} · <a href="{f["official_url"]}">{escape(f["version"])}</a> · {f["size"]/1e9:.2f} ГБ, MD5/SHA-256 проверены.</li>' for f in verification['firmware'])
page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Flip Pets 0.4 — перенос и проверка</title><style>
*{box-sizing:border-box}body{margin:0;background:#0d1722;color:#e3ebef;font:16px/1.55 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:40px 24px}h1{font-size:clamp(32px,5vw,56px);line-height:1.12}h2{margin-top:42px}a{color:#c3ec79}small,p{color:#b7c9d5}.hero{background:linear-gradient(130deg,#1d3145,#253529);border-radius:24px;padding:24px}nav{display:flex;gap:18px;flex-wrap:wrap}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px}article{background:#1a2a3b;border-radius:18px;padding:14px}article img{width:100%;height:180px;object-fit:contain}h3{font-size:17px;margin:12px 0 4px}article p{font-size:13px;margin:0}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;text-align:left;border-bottom:1px solid #344254}.notice{border-left:4px solid #e9c56d;padding:12px 18px;background:#2b2b29;border-radius:8px}.scroll{overflow-x:auto}code{background:#223448;padding:3px 6px;border-radius:4px}img.screen{max-width:320px;width:100%;border-radius:16px}
</style><main><div class="hero"><small>XIAOMI 17 PRO → MIX FLIP · БЕЗ ROOT</small><h1>30 оформлений.<br>Оригинальная графика Xiaomi.</h1><p>170 исходных PAG/MP4-клипов, 11 адаптированных композиций, 497 изображений, 110 штатных NinePatch и пять оригинальных шрифтов. Галерея с поиском, категориями и избранным. Настройки сохраняются по ID оформления.</p><nav><a href="FlipPets.apk">Скачать APK 0.4</a><a href="START-HERE.txt">Инструкция</a><a href="FlipPets-Source.zip">Исходники</a><a href="Verification.zip">Проверки</a></nav></div>
<p class="notice">Приложение и ресурсы проверены в эмуляторе. Работа двух физических экранов на конкретной HyperOS пользователя ещё не подтверждена. Это перенос ресурсов и адаптация поведения; полной копии системных функций 17 Pro здесь нет.</p>
<h2>Как пользоваться</h2><ol><li>Установи FlipPets.apk и выбери оформление в галерее. Проверь полноэкранный просмотр.</li><li>Установи <a href="https://shizuku.rikka.app/download/">официальный Shizuku</a>, выполни сопряжение и запуск через беспроводную отладку по <a href="https://shizuku.rikka.app/guide/setup/">инструкции</a>.</li><li>В Flip Pets нажми «Два экрана · Shizuku», разреши доступ. Полностью раскрой и разблокируй телефон. Постоянный ПК не требуется.</li><li>Складывание, сон или блокировка закрывают только наш внешний сеанс и снимают наш запрос режима. В сложенном состоянии — штатный интерфейс/AOD Xiaomi. «Стоп» выключает контроллер.</li></ol>
<p>После перезагрузки набор, избранное, сцены и фото сохраняются, но Shizuku и контроллер нужно включить снова. <a href="https://shizuku.rikka.app/guide/setup/">Shizuku через ADB требует повторного запуска после перезагрузки</a>. При завершении процесса системой тоже может понадобиться повторное включение. Абсолютная устойчивость к ограничениям HyperOS не подтверждена.</p>
<h2>Что перенесено</h2><p>Bubbles/Roe реагируют на зарядку, низкий заряд и касания, а с отдельным доступом — на уведомления, музыку и шаги. Остальные питомцы показывают исходные сцены. Lumi/Peeko — видео без диалогового ИИ. Аналоговые часы, силикон, градиент, волокно дракона, упругие цифры Stretch, локальный шагомер, подпись, бумажный фон, локальный кинокалендарь и фото используют оригинальную графику. Пружина и гравитационные эффекты адаптированы; системный Folme/шейдер Xiaomi не воспроизведён полностью.</p><p>Фото выбираются штатным файловым диалогом и копируются в закрытую папку приложения. Можно добавить прозрачный передний PNG-слой, изменить масштаб и сдвиг. Шагомер считает события, полученные во время видимого экрана/обоев; истории Mi Fitness нет. Автоматических Douban, облачной погоды, AI-генерации, AON-жестов, платежей и игровых сервисов нет. Полная таблица 42 исходных пресетов находится в Verification.json.</p>
<div class="grid">@@CARDS@@</div>
<h2>Пропорции MIX Flip</h2><p>Адаптация проверена для внешнего 1392×1208, его поворота 1208×1392 и основного 1224×2912. Это разрешения из <a href="https://www.mi.com/global/product/xiaomi-mix-flip/specs/">официальных характеристик MIX Flip</a>. Часы/цифры масштабируются равномерно, фотографии заполняют область с обрезкой. Есть поле слева под камеры и учёт сообщённого системой выреза. Точные физические границы камер и ориентацию нужно сверить на телефоне.</p>
<h2>Расход ресурсов</h2><p>Условия: Android 16, x86_64, два виртуальных ядра, SwiftShader и программный PAG-декодер. 100% CPU — одно ядро. Каждый сценарий измерен 12 секунд после прогрева. PSS — память процесса приложения; расход системных MediaCodec/SurfaceFlinger и память GPU хоста не включены. Эти результаты не измеряют батарею MIX Flip и не сравнивают порт с настоящим 17 Pro.</p><div class="scroll"><table><tr><th>Сценарий</th><th>CPU</th><th>PSS</th></tr>@@ROWS@@</table></div>
<p>Временный Java-мост Shizuku завершается после каждой команды. Скрытый экран прекращает рендеринг, освобождает декодеры, датчик наклона работает только у блёсток. Галерея останавливает предпросмотр. Статичные композиции обновляются при смене настроек/времени; битмапы обоев повторно используются и ограничены длинной стороной 1536 пикселей. Частоту PAG можно выбрать: 12/20/30 кадров/с, по умолчанию 20. Частота MP4 задаётся оригинальным файлом.</p>
<p>На физическом телефоне приложение разрешает аппаратные декодеры; при несовместимости доступен программный режим. <a href="https://pag.io/docs/en/api-instructions.html">libpag поддерживает аппаратное декодирование и программный резерв</a>. Фактически выбранный декодер и эффект для батареи нужно проверить на MIX Flip. После 20 переключений память не росла монотонно; снимки и интервалы в <a href="resource-profile.json">полном профиле</a>. Длительной проверки утечек на физическом устройстве ещё нет.</p>
<h2>Проверки именно этого APK</h2><ul><li>170/170 клипов: видимые и разные кадры в двух точках времени.</li><li>68/68 проверок композиций: все 497 PNG, 110 скомпилированных NinePatch, пять шрифтов, три пропорции, настройки текста/цвета/пружины, закрытый импорт фото и EXIF.</li><li>15/15 переходов между PAG, MP4, часами и фото.</li><li>11 сценариев автономного контроллера с подставными системными сигналами; восемь проверок одноразового запуска/отката.</li><li>Настоящий Shizuku UserService: UID 2000, запрос доступа, status/stop, отказ запуска на чужой модели.</li><li>Журнал ошибок сохраняется через штатный файловый диалог без root; сохранены события, ответы Shizuku и собственный logcat. Перезапуск, скрытие/возобновление, галерея и живые обои: результаты в Verification.json.</li><li>Подпись APK проверена; zipalign/ELF совместимы с 16 КиБ страницами, arm64-v8a и x86_64. Все файлы assets APK совпали с исходниками.</li></ul>
<p>SHA-256 APK: <code>@@SHA@@</code>. Каждый результат декодирования содержит этот хеш. Подробные данные, XML интерфейса, скриншоты, логи и профиль сохранены в <a href="Verification.zip">Verification.zip</a>.</p>
<h2>Прошивки и оригиналы</h2><ul>@@FIRMWARES@@</ul><p>Обе прошивки уже скачаны полностью в work/firmware; ссылки и проверенные хеши — в <a href="Firmware-manifest.json">манифесте</a>. Прошивка 17 Pro использована только как донор. <a href="Original-Xiaomi-Resources.zip">Оригинальные ресурсы</a> содержат исходные MRC/MRM, метаданные и шрифты. Artwork/шрифты Xiaomi сохраняют права своих владельцев; MIT-лицензия относится к нашему коду.</p></main></html>'''
page=page.replace('@@CARDS@@',''.join(cards)).replace('@@ROWS@@',rows).replace('@@SHA@@',binary).replace('@@FIRMWARES@@',firmwares)
(OUT/'report.html').write_text(page,encoding='utf-8')
names=[p for p in OUT.iterdir() if p.is_file() and p.name!='checksums.sha256' and 'KernelSU' not in p.name]
(OUT/'checksums.sha256').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(names)),encoding='utf-8')
print(json.dumps(dict(apkSha256=binary,sets=len(catalog),clips=len(paths),qaPassed=True,outputFiles=len(names)),indent=2))
