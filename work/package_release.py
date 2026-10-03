"""Package release 0.8 only after fresh, successful APK-bound emulator QA.

No device/network operations. Public bundles use explicit allowlists; historical
results retain their own SHA and never become evidence for the current APK.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import html
import json
import pathlib
import re
import struct
import subprocess
import zipfile

WORK = pathlib.Path(__file__).resolve().parent
ROOT = WORK.parent
OUT = ROOT / "outputs"
VERSION = "0.8"
VERSION_CODE = 8
COUNTS = {"qa.json": 170, "composition-qa.json": 68,
          "ui-switch-qa.json": 15, "utility-qa.json": 15}
RESEARCH = ["MRC-coverage.json", "composition-provenance.json", "font-provenance.json",
            "portable-resource-provenance.json", "native-playback-evidence.json",
            "pandora-rearscreen-inventory.json", "ruyi-display_layout_configuration.xml",
            "ruyi-product-device_state_configuration.xml", "ruyi-device_state_configuration.xml",
            "ruyi-DeviceStateManagerShellCommand.java"]
HISTORICAL = {"hardware-validation.json": "Physical MIX Flip version 0.5; not 0.8 hardware QA",
              "resource-profile.json": "Earlier emulator resource profile; not a current 0.8 profile",
              "lifecycle.json": "Earlier emulator lifecycle/wallpaper/reboot evidence; no new run claimed",
              "playback-validation.json": "Earlier finite-playback validation; not retested by packaging",
              "hardware-v07.json": "Limited physical version0.7 observations before startup retry fix; not0.8 phone QA",
              "hardware-resource-v07.json": "Short physical version0.7 CPU/PSS sample; not current0.8 resource use",
              "resource-profile-v07.json": "Version0.7 emulator profile; not current0.8 resource use",
              "runtime-v07.json": "Version0.7 emulator task/service lifecycle; not current0.8 runtime QA",
              "pure-tests-v07.json": "Version0.7 source-bound pure tests; original source hashes retained",
              "visual-simulation-v07.json": "Version0.7 virtual cover/large-font observations; not current0.8 visuals"}
DENIED_PARTS = {"phone-qa", "firmware", "images", "extracted", "emulator", "logs", "build", "ksu"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(4 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def apk_sha(data):
    camel, snake = data.get("apkSha256"), data.get("apk_sha256")
    require(not (camel and snake) or camel == snake, "Conflicting APK SHA fields")
    return camel or snake

def public_input(path):
    path = path.resolve()
    require(path.is_relative_to(WORK), f"Evidence must stay under work/: {path}")
    relative = path.relative_to(WORK)
    require(not any(part.lower() in DENIED_PARTS or part.lower().startswith("phone-")
                    for part in relative.parts), f"Private/raw evidence path refused: {relative}")
    require(path.is_file(), f"Missing public input: {relative}")
    return path


def run(command):
    result = subprocess.run([str(item) for item in command], capture_output=True,
                            encoding="utf-8", errors="replace", check=True)
    return result.stdout + result.stderr


def pack(destination, entries):
    unique = {}
    for path, name in entries:
        path = pathlib.Path(path)
        require(path.is_file(), f"Missing archive input: {path}")
        name = str(name).replace("\\", "/")
        require(not name.startswith("/") and ".." not in pathlib.PurePosixPath(name).parts,
                f"Unsafe ZIP entry: {name}")
        require(path.suffix.lower() not in {".p12", ".jks", ".keystore"}, f"Signing material refused: {name}")
        require(name not in unique or unique[name] == path, f"Duplicate ZIP entry: {name}")
        unique[name] = path
    temporary = destination.with_name(destination.name + ".tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=4) as archive:
        for name, path in sorted(unique.items()):
            archive.write(path, name)
    with zipfile.ZipFile(temporary) as archive:
        require(archive.testzip() is None, f"ZIP integrity failure: {destination.name}")
    temporary.replace(destination)
    return len(unique)


def apk_checks(apk, catalog, paths):
    tools = WORK / "tools"
    bt = tools / "sdk/build-tools/android-16"
    java = tools / "jdk/jdk-17.0.20.1+1/bin/java.exe"
    badging = run([bt / "aapt2.exe", "dump", "badging", apk])
    require("name='org.flippets.app'" in badging and f"versionName='{VERSION}'" in badging
            and f"versionCode='{VERSION_CODE}'" in badging, f"APK package/version is not org.flippets.app {VERSION} ({VERSION_CODE})")
    signature = run([java, "-jar", bt / "lib/apksigner.jar", "verify", "--verbose", "--print-certs", apk])
    require("Verified using v3 scheme" in signature and "Verified using v3 scheme (APK Signature Scheme v3): true" in signature,
            "APK v3 signature verification did not report success")
    run([bt / "zipalign.exe", "-c", "-P", "16", "4", apk])
    certificate = re.search(r"Signer #1 certificate SHA-256 digest: ([0-9a-f]+)", signature)
    libraries = []
    with zipfile.ZipFile(apk) as archive:
        require(archive.testzip() is None, "APK ZIP integrity failed")
        require(json.loads(archive.read("assets/catalog.json")) == catalog, "APK/source catalogue mismatch")
        source_assets = [p for p in (WORK / "app/assets").rglob("*") if p.is_file()]
        expected_names = {"assets/" + p.relative_to(WORK / "app/assets").as_posix() for p in source_assets}
        actual_names = {n for n in archive.namelist() if n.startswith("assets/") and not n.endswith("/")}
        require(actual_names == expected_names, "APK/source assets set differs")
        for path in source_assets:
            name = "assets/" + path.relative_to(WORK / "app/assets").as_posix()
            require(archive.read(name) == path.read_bytes(), f"APK/source asset bytes differ: {name}")
        for path in paths:
            if path.endswith(".mp4"):
                require(archive.getinfo("assets/" + path).compress_type == zipfile.ZIP_STORED,
                        f"MP4 must remain uncompressed: {path}")
        for name in archive.namelist():
            if not name.startswith("lib/") or not name.endswith(".so"):
                continue
            data = archive.read(name)
            require(data[:4] == b"\x7fELF" and data[4] == 2, f"Not ELF64: {name}")
            offset = struct.unpack_from("<Q", data, 32)[0]
            size, count = struct.unpack_from("<HH", data, 54)
            alignments = []
            for i in range(count):
                fields = struct.unpack_from("<IIQQQQQQ", data, offset + i * size)
                if fields[0] == 1:
                    alignments.append(fields[-1])
            require(alignments and all(x >= 16384 for x in alignments), f"ELF LOAD alignment <16KiB: {name}")
            libraries.append({"path": name, "loadAlignments": alignments,
                              "sha256": hashlib.sha256(data).hexdigest()})
    require(len(libraries) == 4 and {x["path"].split("/")[1] for x in libraries} == {"arm64-v8a", "x86_64"},
            "Expected four native libraries in arm64-v8a/x86_64")
    return {"package": "org.flippets.app", "versionName": VERSION, "versionCode": VERSION_CODE,
            "signatureV3Verified": True, "certificateSha256": certificate.group(1) if certificate else None,
            "zipalign16KiBVerified": True, "allAssetsByteIdenticalToSources": True,
            "nativeLibraries": libraries}


def source_entries():
    entries = [(p, p.relative_to(ROOT)) for p in (WORK / "app").rglob("*") if p.is_file()]
    for name in ["README.md", "CHANGELOG.md", "AGENTS.md", ".gitattributes", ".gitignore"]:
        if (ROOT / name).is_file():
            entries.append((ROOT / name, name))
    entries += [(p, p.relative_to(ROOT)) for p in (ROOT / "docs").glob("*.md")]
    # Sanitized OEM inspection only; never glob raw phone dumps.
    for name in ["folded-wallpaper-phone-inspection.json"]:
        path = ROOT / "docs" / name
        if path.is_file():
            entries.append((path, path.relative_to(ROOT)))
    # Only named portable scripts/docs: top-level phone-*.txt dumps must never leak.
    for name in ["build_apk.py", "prepare_catalog.py", "prepare_compositions.py", "inspect_compositions.py",
                 "check_native.py", "download_firmware.py", "download_presets.py", "read_erofs_file.py",
                 "package_release.py", "prepare_playback.py", "extract_ready.py", "extract_theme_resources.py",
                 "payload_plan.py", "read_partial_metadata.py", "prepare_sample.py", "SOURCE-README.txt", "CODE-LICENSE.txt"]:
        path = WORK / name
        if path.is_file():
            entries.append((path, path.relative_to(ROOT)))
    if (WORK / "tools/README.md").is_file():
        entries.append((WORK / "tools/README.md", "work/tools/README.md"))
    for path in (WORK / "tests").rglob("*"):
        if path.is_file() and path.suffix in {".py", ".java", ".sh", ".xml"} \
                and "classes" not in path.parts and path.name not in {"profile_phone.py", "phone_ui.py"}:
            entries.append((path, path.relative_to(ROOT)))
    for path in (WORK / "research").rglob("*"):
        if path.is_file() and (path.suffix in {".json", ".xml", ".java", ".md"}) \
                and not path.name.startswith("android-"):
            entries.append((path, path.relative_to(ROOT)))
    for path in (WORK / "tools/libpag").rglob("*"):
        if path.is_file() and (path.name == "classes.jar" or
                              path.suffix == ".so" and path.parent.name in {"arm64-v8a", "x86_64"}):
            entries.append((path, path.relative_to(ROOT)))
    for path in (WORK / "tools/shizuku").glob("*"):
        if path.is_file() and (path.suffix in {".jar", ".pom", ".aar"} or path.name == "LICENSE"):
            entries.append((path, path.relative_to(ROOT)))
    for name in ["START-HERE.txt", "flip-pets-control.sh", "FlipPets-ADB.ps1"]:
        entries.append((OUT / name, "outputs/" + name))
    return entries


def original_entries():
    entries = [(p, p.relative_to(WORK / "original-resources"))
               for p in (WORK / "original-resources").rglob("*") if p.is_file()]
    require(entries, "Original resource inputs missing")
    donor = WORK / "jars/pandora-subscreencenter.apk"
    if donor.is_file():
        entries.append((donor, "pandora-subscreencenter.apk"))
    entries += [(p, "fonts/" + p.name) for p in (WORK / "app/assets/fonts").glob("*") if p.is_file()]
    for name in ["MRC-coverage.json", "font-provenance.json", "composition-provenance.json",
                 "pandora-rearscreen-inventory.json", "portable-resource-provenance.json"]:
        entries.append((WORK / "research" / name, name))
    entries.append((WORK / "CODE-LICENSE.txt", "CODE-LICENSE.txt"))
    return entries


def report(verification, catalog):
    e = html.escape
    physical = verification["currentApk"].get("physicalEvidence")
    notice = ("0.8 прошла актуальные эмуляторные проверки и ограниченную проверку на реальном MIX Flip. Точные физические наблюдения/ограничения находятся в current physical evidence; длительная стабильность, расход батареи и нативное применение анимированных обоев сложенного экрана этим не подтверждены." if physical else "0.8 прошла актуальные проверки на стандартном Android16 в эмуляторе. Физические результаты0.8 в этот пакет ещё не включены. На реальном MIX Flip EEA HyperOS3 ранее подтверждены два экрана, fold-return, аппаратный декодер и собственные фото в версии0.5; это историческая базовая проверка.")
    cards = []
    for pet in catalog:
        thumb = WORK / "app/assets/thumbs" / (pet["id"] + ".webp")
        data = base64.b64encode(thumb.read_bytes()).decode()
        kind = "Адаптированная композиция" if pet["kind"] == "composition" else f'{len(pet["clips"])} исходных клипов'
        cards.append(f'<article><img loading="lazy" src="data:image/webp;base64,{data}" alt="{e(pet["name"])}"><h3>{e(pet["name"])}</h3><p>{e(kind)}</p></article>')
    tests = ''.join(f'<li>{e(name)}: {data["tested"]}/{data["tested"]}, SHA совпадает.</li>'
                    for name, data in verification["currentApk"]["emulatorQa"].items())
    profile = verification["currentApk"].get("resourceProfile")
    if profile:
        rows = ''.join(f'<tr><td>{e(item.get("scenario", item.get("label", "scenario")))}</td><td>{item.get("cpuPercentOneCore", 0):.2f}%</td><td>{item.get("pssKiB", 0)/1024:.1f} МиБ</td></tr>' for item in profile["data"].get("results", []))
        resource_section = f'<p>Свежий профиль связан с этим APK. {e(profile["data"].get("environment", "Эмулятор Android 16; не замер батареи телефона."))}</p><table><tr><th>Сценарий</th><th>CPU одного ядра</th><th>PSS</th></tr>{rows}</table>'
    else:
        resource_section = '<p>Свежий профиль 0.8 в этот пакет не включён. Старые CPU/PSS доступны только как historical baseline со своим SHA. Нулевой фоновый рендер и экономия батареи требуют отдельного измерения на новой сборке/телефоне.</p>'
    history = ''.join(f'<li>{e(item["file"])} — {e(item["scope"])}; исходный SHA: <code>{e(item.get("originalApkSha256") or "не указан / unbound")}</code>.</li>' for item in verification["historicalEvidence"])
    return f'''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Flip Pets {VERSION} — проверенный пакет</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#151218;color:#e9e0e9;font:16px/1.55 system-ui,sans-serif}}main{{max-width:1150px;margin:auto;padding:32px 20px}}h1{{font-size:clamp(30px,5vw,52px);line-height:1.15}}a{{color:#d7baff}}p,li{{color:#cdc2d3}}nav{{display:flex;gap:18px;flex-wrap:wrap}}.hero,article{{background:#211e26;border-radius:24px;padding:20px}}.notice{{background:#39333f;border-radius:18px;padding:18px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}article img{{width:100%;height:170px;object-fit:contain}}h3{{font-size:17px}}article p{{font-size:13px}}code{{word-break:break-all}}table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #514658;padding:10px;text-align:left}}
</style><main><section class="hero"><p>XIAOMI 17 PRO → MIX FLIP · ROOTLESS</p><h1>Flip Pets {VERSION}<br>30 оформлений, исходная графика.</h1><p>170 оригинальных PAG/MP4-клипов и 11 адаптированных композиций. Material You, приватные фото, поиск и избранное.</p><nav><a href="FlipPets.apk">APK</a><a href="START-HERE.txt">Инструкция</a><a href="FlipPets-Source.zip">Исходники</a><a href="Verification.zip">Доказательства</a></nav></section>
<p class="notice">{e(notice)}</p>
<h2>Сложенный экран: нативная интеграция</h2><p>По умолчанию остаются родной внешний интерфейс, защищённый экран блокировки и AOD Xiaomi. Следующий приоритет — опциональные анимированные обои через штатный редактор/движок Xiaomi; в 0.8 этот export/apply ещё не реализован. Исследование: sourceZIP/docs/folded-wallpaper-options.md. Повторная попытка запуска после раскрытия ограничена по времени и проверяет готовность state5; устойчивое поведение0.8 на HyperOS требует своего аппаратного отчёта. Utility-карточки второстепенны, включаются явно и не подменяют штатные виджеты.</p><h2>Что нового</h2><p>Настройки/галерея используют системные цвета и светлую/тёмную тему. Optional карточки батареи, медиаплеера или визуального таймера выключены по умолчанию; это наши дополнения, а не заявленная копия виджетов17Pro. Одновременно показывается одна компактная карточка. Таймер/секундомер без звука и точного фонового alarm; музыка через опубликованные MediaSession и поддерживаемые плеером действия.</p>
<p>Внешний сеанс отделён от задачи настроек и поддерживается user-enabled foreground-службой с тихим уведомлением/Stop. Закрытие настроек не является командой выключения сеанса. Wake lock и скрытый рендер не добавлены. HyperOS всё ещё может принудительно остановить приложение. Затухание работает по exposed hinge angle либо дискретному flip-state; дискретное состояние не называется измеренным углом.</p>
<h2>Запуск</h2><ol><li>Установи APK, выбери оформление/фото.</li><li>Запусти <a href="https://shizuku.rikka.app/guide/setup/">Shizuku по официальной инструкции</a>, нажми «Включить через Shizuku» и разреши доступ.</li><li>Раскрой/разблокируй MIX Flip. При складывании/сне возвращается штатный интерфейс/AOD Xiaomi.</li><li>После перезагрузки Shizuku запускается заново, затем включается сеанс. Фото и настройки сохраняются.</li></ol>
<h2>Проверки этого APK</h2><ul>{tests}</ul><p>Всего {verification["currentApk"]["qaChecks"]} успешных runtime-проверок. Все assets APK совпали с source bytes; MP4 не сжаты, подписьv3/zipalign/ELF16KiB проверены. SHA-256: <code>{verification["apkSha256"]}</code>. Успех эмулятора не доказывает физический угол шарнира, обход ограниченийHyperOS или расход батареи.</p>
<h2>Ресурсы</h2><div class="grid">{''.join(cards)}</div><p>Геометрия адаптирована к внешнему1392×1208/1208×1392 и основному1224×2912. Вырез камер учитывается по insets. Размеры — <a href="https://www.mi.com/global/product/xiaomi-mix-flip/specs/">официальные характеристикиMIX Flip</a>; касания/вырезы новых карточек ещё требуют телефона.</p>
<h2>Ресурсы процесса</h2>{resource_section}<p>CPU100% означает одно ядро; PSS относится к процессу приложения. Системный decoder/GPU и батарея этим не измеряются. На 0.5 телефон показал около39% одного ядра при непрерывном30fps и0.16% на удержанном кадре, короткие12-секундные интервалы; это исторические замеры, не обещание для0.8.</p>
<h2>Исторические данные</h2><ul>{history}</ul><p>Без полного системного сервисаXiaomi не обещаются AI-dialog, AON-камерные жесты, платежи, облачная погода/Douban и полноценныйFolme. Исследование и donor-roadmap находятся в sourceZIP/docs. MIT относится только к нашему коду; графика/шрифты сохраняют права владельцев. Прошивки — только доноры ресурсов, не для установки наMIX Flip.</p></main></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa-dir", type=pathlib.Path, default=WORK / "qa-v03/device-files")
    parser.add_argument("--profile", type=pathlib.Path)
    parser.add_argument("--physical-evidence", type=pathlib.Path, help="Explicit public current-APK physical report; limited scope remains explicit")
    parser.add_argument("--current-evidence", type=pathlib.Path, nargs="*", default=[])
    parser.add_argument("--public-screenshots", type=pathlib.Path, nargs="*", default=[])
    parser.add_argument("--skip-originals", action="store_true", help="Do not regenerate original-resource ZIP")
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    apk = OUT / "FlipPets.apk"
    binary = sha(apk)
    catalog = read(WORK / "app/assets/catalog.json")
    paths = {value for pet in catalog for value in pet["clips"].values()}
    require(len(catalog) == 30 and len(paths) == 170, "Catalogue count changed; review required")
    qa, evidence = {}, []
    for name, count in COUNTS.items():
        path = public_input(args.qa_dir / name)
        data = read(path)
        require(apk_sha(data) == binary, f"Stale/wrong APK SHA: {name}")
        require(data.get("tested") == count and data.get("failed") == 0,
                f"Incomplete/failed QA: {name}; expected {count}/0")
        require(len(data.get("results", [])) == count and all(x.get("ok") is True for x in data["results"]),
                f"QA result rows invalid: {name}")
        require(not data.get("skipped"), f"Skipped required QA: {name}")
        qa[name] = data
        evidence.append((path, "current/emulator/" + name))
    require({row["path"] for row in qa["qa.json"]["results"]} == paths, "Clip QA coverage differs from catalogue")
    require(qa["composition-qa.json"].get("decodedOriginalImages") == 497 and
            qa["composition-qa.json"].get("validCompiledNinePatches") == 110, "Original image/NinePatch counts mismatch")
    require((OUT / "flip-pets-control.sh").read_bytes() == (WORK / "app/assets/controller.sh").read_bytes(),
            "Public controller script differs from embedded APK source")
    checked = apk_checks(apk, catalog, paths)
    for scene in read(WORK / "research/composition-provenance.json"):
        for path, expected in scene["assets"].items():
            require(sha(WORK / "app/assets" / scene["assetRoot"] / path) == expected,
                    f"Composition image provenance mismatch: {path}")
    profile_path = args.profile
    if profile_path is None:
        candidates = [args.qa_dir / "resource-profile-v08.json", args.qa_dir.parent / "resource-profile-v08.json",
                      WORK / "qa-v03/resource-profile-v08.json"]
        profile_path = next((p for p in candidates if p.is_file()), None)
    profile = None
    if profile_path is not None:
        profile_path = public_input(profile_path)
        profile_data = read(profile_path)
        require(apk_sha(profile_data) == binary, "Resource profile is not bound to current APK")
        profile = {"file": profile_path.name, "data": profile_data}
        evidence.append((profile_path, "current/emulator/" + profile_path.name))
    extras = []
    for path in args.current_evidence:
        path = public_input(path)
        require(path.suffix.lower() == ".json", "Current structured evidence must be JSON")
        data = read(path)
        require(apk_sha(data) == binary, f"Current evidence SHA differs: {path.name}")
        require(data.get("failed", 0) == 0 and data.get("passed", True) is True,
                f"Current evidence contains failures: {path.name}")
        if isinstance(data.get("compile"), dict):
            require(data["compile"].get("passed", True) is True, f"Compile evidence failed: {path.name}")
        if isinstance(data.get("suites"), list):
            require(all(row.get("passed", True) is True for row in data["suites"]), f"Pure suite failed: {path.name}")
        for relative, expected in data.get("source_sha256", {}).items():
            source = (ROOT / relative).resolve()
            require(source.is_relative_to(ROOT) and source.is_file() and sha(source) == expected,
                    f"Evidence/source SHA differs: {relative}")
        if isinstance(data.get("results"), list):
            require(all(row.get("ok", True) is True for row in data["results"]), f"Current evidence failed rows: {path.name}")
        extras.append({"file": path.name, "data": data})
        evidence.append((path, "current/additional/" + path.name))
    physical = None
    if args.physical_evidence is not None:
        path = public_input(args.physical_evidence)
        require(path.suffix.lower() == ".json", "Physical evidence must be structured public JSON")
        data = read(path)
        require(apk_sha(data) == binary, "Physical report APK SHA differs")
        require(data.get("failed") == 0, "Physical report contains failed/unknown checks")
        rows = data.get("results")
        require(isinstance(rows, list) and len(rows) > 0, "Physical report needs explicit observed results")
        require(data.get("tested") == len(rows), "Physical report tested count differs from results")
        require(all(row.get("ok") is True for row in rows), "Physical report has failed/unknown rows")
        physical = {"file": path.name, "scope": "Limited physical observations; see exact report and limitations", "data": data}
        evidence.append((path, "current/physical/" + path.name))
    screenshots = []
    for path in args.public_screenshots:
        path = public_input(path)
        require(path.suffix.lower() in {".png", ".jpg", ".webp"}, "Screenshot type refused")
        screenshots.append({"file": path.name, "sha256": sha(path), "scope": "Explicitly selected emulator/app screenshot; no hardware claim"})
        evidence.append((path, "current/screenshots/" + path.name))
    historical = []
    for name, scope in HISTORICAL.items():
        path = WORK / "qa-v03" / name
        if not path.is_file():
            continue
        data = read(path)
        historical.append({"file": name, "scope": scope, "originalApkSha256": apk_sha(data),
                           "sourceFileSha256": sha(path), "data": data})
        evidence.append((path, "historical/" + name))
    fixtures = []
    for path in [WORK / "qa-final/controller-tests.json", WORK / "qa-v02/supervisor-tests.json"]:
        if path.is_file():
            data = read(path)
            fixtures.append({"file": path.name, "scope": "Stubbed commands, not physical hardware; no APK SHA binding assumed", "data": data})
            evidence.append((path, "fixtures/" + path.name))
    for name in RESEARCH:
        path = WORK / "research" / name
        if path.is_file():
            evidence.append((path, "firmware-analysis/" + name))
    firmware = [{key: value for key, value in item.items() if key not in {"path"}}
                for item in read(OUT / "Firmware-manifest.json")]
    verification = {"version": VERSION, "apkSha256": binary,
                    "currentApk": {"environment": "Standard Android16/API36 x86_64 emulator; not HyperOS",
                                   "emulatorQa": qa, "qaChecks": sum(COUNTS.values()),
                                   "binaryChecks": checked, "compositionImageHashesVerified": True,
                                   "resourceProfile": profile, "physicalEvidence": physical, "additionalEvidence": extras, "screenshots": screenshots},
                    "catalogue": {"sets": 30, "originalClips": 170, "pagClips": sum(p.endswith('.pag') for p in paths),
                                  "mp4Clips": sum(p.endswith('.mp4') for p in paths), "offlineCompositions": 11,
                                  "originalImages": 497, "compiledNinePatches": 110, "originalFonts": 5},
                    "historicalEvidence": historical, "controllerFixtures": fixtures,
                    "physicalReleaseValidation": {"version08Tested": physical is not None,
                        "phoneInstalledVersionAtHandoff": "0.7" if physical is None else VERSION,
                        "phoneVersionScope": "Phone remains on0.7;0.8 emulator-only release does not include a phone installation" if physical is None else "See explicit current physical report", "scope": "Limited physical observations only" if physical else "No current physical evidence included",
                        "baseline": "Version0.5 fold/photo/two-screen and limited0.7 phone observations retain their original SHA above",
                        "remaining": ["Native custom animated folded wallpaper application is not implemented/tested",
                                      "Long stability/battery run not demonstrated by short checks"],
                        "reportLimitations": (physical["data"].get("limitations", []) + physical["data"].get("pending", [])) if physical else ["Version0.8 was not installed/tested on the physical phone; this release concludes after emulator checks"]},
                    "firmware": firmware, "coverage": read(WORK / "research/MRC-coverage.json"),
                    "fontProvenance": read(WORK / "research/font-provenance.json"),
                    "privacy": "No raw phone dumps, private photos, signing keys or collected notification/media text in these bundles"}
    dump(OUT / "Verification.json", verification)
    dump(OUT / "resource-profile.json", {"releaseVersion": VERSION, "currentApkSha256": binary,
        "currentProfile": profile, "historicalProfiles": [item for item in historical if item["file"] in {"resource-profile.json", "resource-profile-v07.json", "hardware-resource-v07.json"}]})
    (OUT / "FlipPets.sha256.txt").write_text(binary + "  FlipPets.apk\n", encoding="utf-8")
    (OUT / "report.html").write_text(report(verification, catalog), encoding="utf-8")
    evidence.insert(0, (OUT / "Verification.json", "Verification.json"))
    evidence.append((OUT / "resource-profile.json", "resource-profile.json"))
    source_count = pack(OUT / "FlipPets-Source.zip", source_entries())
    evidence_count = pack(OUT / "Verification.zip", evidence)
    original_count = None if args.skip_originals else pack(OUT / "Original-Xiaomi-Resources.zip", original_entries())
    names = ["FlipPets.apk", "FlipPets.sha256.txt", "FlipPets-Source.zip", "Verification.json", "Verification.zip",
             "resource-profile.json", "report.html", "START-HERE.txt", "FlipPets-ADB.ps1", "flip-pets-control.sh", "Firmware-manifest.json"]
    if not args.skip_originals:
        names.append("Original-Xiaomi-Resources.zip")
    (OUT / "checksums.sha256").write_text(''.join(sha(OUT / name) + '  ' + name + '\n' for name in sorted(names)), encoding="utf-8")
    print(json.dumps({"version": VERSION, "apkSha256": binary, "runtimeChecks": sum(COUNTS.values()),
                      "sourceZipEntries": source_count, "evidenceZipEntries": evidence_count,
                      "originalZipEntries": original_count, "currentProfileIncluded": profile is not None,
                      "physical08Tested": physical is not None}, indent=2))


if __name__ == "__main__":
    main()