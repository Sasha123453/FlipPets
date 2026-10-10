# Дополнительные темы заднего экрана: что подтверждено в18Pro

**Да, у штатного китайского Themes18Pro есть online-магазин заднего экрана.** Это подтверждено кодом из проверенного hongkong product, а не предположением по обычному магазину тем. Автоматический downloader/импорт произвольных online-тем в Flip Pets пока не реализован; наличие магазина не подтверждает совместимость любого MAML с нашим Java player.

Источник: `/app/MIUIThemeManager/MIUIThemeManager.apk`, пакет `com.android.thememanager`, версия11.5.3.1, SHA256 `3888058041439577aadbb933c9bed1fb3ef16acda20d15404fb620314a8edd0a`. Раздел product SHA `f63831fadeddfd4b52407ff22e02ac8d17cce6ceb474c951c4fc13c214d09f63` проверен. `/data-app/MIUIThemeStore/MIUIThemeStore.apk` — отдельный маленький stub, не исследованный основной магазин.

## Официальный UI-маршрут

`com.rearScreen.miclaw.appfunction.RearScreenStoreFunction.openRearStore` открывает Intent с action **`com.miui.theme.action.VIEW_HOME`**, string extra **`EXTRA_TAB_ID=rearscreen`**, package **`com.android.thememanager`**. В manifest обработчик `ThemeResourceProxyTabActivity` exported=true и имеет этот action; также объявлен browsable scheme `theme`. AppFunction предварительно проверяет main lock через LockScreenGuard. Это реальный вход в stock UI; открытие этого UI из Flip Pets/на MIX в данном исследовании не запускалось.

`RearScreenTab` использует tab id rearscreen и ограничивает его доступность через `DeviceUtils.a()`/device helper плюс проверку location-константы. Следовательно одного Intent extra недостаточно, чтобы доказать появление нужного tab на неподдержанном устройстве.

В сохранённом фактическом EEA MIX Flip Themes3.0.6.8-global проверка DEX string declarations не нашла этот VIEW_HOME/tab/RearScreenTab/StoreFunction контракт. Это read-only сравнение APK, не попытка запуска на телефоне; версия, регион и feature flags значимы. Нативный outer tiny lock editor MIX и отдельный rear-screen магазин18Pro — разные маршруты.

## Серверный каталог и ограничения

`RearScreenListViewModel → RearListDataManager → RearScreenNetRepository` загружает online категории через `ThemeSettingRequestApi`. В нём GET `page/v3/REAR_SCREEN_SETTING` и `page/v3/REAR_SCREEN_SETTING_REVISION`; production base `ThemeNetworkManager.getBaseUrl()` — `https://thm.market.xiaomi.com/thm/`. Ответы читаются как UIPage/UICard/UIProduct, затем преобразуются в rear category/resource items. Это не простой каталог прямых общедоступных MRC URL.

`ParamInterceptor` добавляет device, region, isGlobal, system/version, language, capability, APK version, display pixels/device type и, когда device helper поддерживает rear, rearScreenVersion. NetworkManager включает UserAgreement/Header/Param/Cache interceptors. Поэтому сервер может возвращать разные наборы под разные прошивки/устройства. Это подтверждение параметров запроса, не измеренная серверная блокировка конкретного MIX/EEA.

В том же interceptor есть **условная** account/token/signature ветка для flagged-запросов. Она обращается к LoginManager и EncryptNetworkUtils; параметры страницы помечены request_flag1. Нельзя отсюда вывести ни «весь каталог требует аккаунт», ни «все downloads анонимны и бесплатны». Фактический login, платность, DRM и условия конкретной downloadable темы не проверялись. В APK также имеются supportPaidWidgets/capability flags и версии ресурсов. Авторизованный stock UI должен сам обрабатывать такие ограничения; user tokens/идентификаторы в этом исследовании не читались и не использовались. Запросов к online API не выполнялось.

## Формат и возможное продолжение

Установленные rear темы используют MRC ZIP с `manifest.xml`, PAG/MP4/PNG/font assets и отдельной MRM JSON metadata. В examined built-in resources onlineId=null; это не готовые идентификаторы магазина для прямой загрузки. AI-generated/share MTZ и обычные MRC могут идти по разным pipelines. Произвольный downloaded theme нельзя считать одним PAG или совместимым reactive pet по его названию.

Практический следующий шаг — штатный магазин на поддержанном18Pro/CN и легальный экспорт полученного ресурса, затем offline read-only import-plan: полный archive/member hashes, формат, MAML state numbers/actions, required engine/version и доступность своих исходников. Возможность такого export/download на текущем MIX/EEA ещё требует подтверждения. Для native AI/service templates нужны отдельные backend/binder/data-binding права; PNG/MAML UI сам по себе их не предоставляет.

Для Flip Pets можно позже сделать явный импорт выбранного файла через document picker и whitelisted supported формат, не исполняя неизвестные MAML commands. Online-опция потребует отдельного выбора пользователя и INTERNET permission, которого текущий app не имеет. Из исследования не следует необходимость обходить region/device/account/DRM или устанавливать donor system APK на MIX.

Локальная code evidence сохранена только в ignored `work/extracted/hongkong`: `RearScreenStoreFunction.java`, `RearScreenTab.java`, `RearScreenNetRepository.java`, `ThemeSettingRequestApi.java`, `ThemeNetworkManager.java`, `ThemeParamInterceptor.java`, native manifest. Здесь опубликованы контракт, hashes и ограничения; private phone/account данные отсутствуют.
