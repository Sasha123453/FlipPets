# Свой питомец по фотографии: фактический pipeline18Pro

10.10.2026 пользователь запросил сценарий как у18Pro: фото своего питомца →
автоматически созданный объёмно выглядящий персонаж → анимация на внешнем экране.
Это отдельная функция; существующий импорт фото не объявляется её реализацией.

Источник — проверенный hongkong product, Themes11.5.3.1, APK SHA256
`3888058041439577aadbb933c9bed1fb3ef16acda20d15404fb620314a8edd0a`.
Новые class reads выполнялись offline, без запросов к генератору, авторизации,
чтения аккаунта или отправки фотографий. Декомпиляция — свидетельство клиентской
архитектуры, не выполненный end-to-end тест.

Подтверждены классы `com.rearScreen.aiCompanion`:

1. `AiCompanionApiService` разделяет generateImage, pollGenerateImageStatus,
   submitVideoTask, awaitGenerateSubmitted и acquireVideoTask.
2. `AiCompanionRealApiProvider$generateImage$2` передаёт локальный reference file
   и userPrompt в `StartWithAiCompanionHandle` через `AiWallpaperManager`.
   Сценарий имеет имя `accompanyPic2Pic`.
3. `submitVideoTask$2` проверяет существование файла с подтверждённым статичным
   изображением, затем отправляет `accompanyPic2Video` в тот же manager; связывает
   image/video задачи через pic2PicBizId/bizId.
4. `AiCompanionAcquireApi` содержит настоящий `POST ai/acquire`, не локальный
   генератор. `CompanionGenerateRawDataBuilder` формирует JSON text/imageUrls и
   шифрует его AES с ключом, полученным предыдущими стадиями.
5. Constants содержат `reference.jpg`, `generated_static.png`, `details.mtz` и
   имена кастомного companion. Это подтверждает image→video/resource pipeline.
   Клиентский код не является доказательством выдачи настоящего3D mesh/rig или
   непрерывного локального3D-рендера. Визуальное «3D» может быть видео.

В полном Theme network interceptor есть условная account/token/signature ветка;
её требования именно для каждого companion-запроса пока не прослежены. Нельзя
обещать доступность генератора на MIX/EEA, бесплатность или отсутствие аккаунта.
Модели/веса генерации в прочитанных классах не найдены; это ограниченный client
audit, а не доказательство отсутствия любых локальных моделей во всей прошивке.

Для работающего переноса нужны либо подтверждённый штатный сервис/экспорт Xiaomi,
либо отдельный действующий генератор image→image→video с документированным API.
Перед отправкой фото пользователь должен видеть сервис и явно подтверждать её.
Ключи сервиса не должны встраиваться в APK; промежуточные файлы остаются приватными.
Root/KernelSU не предоставляет серверные ключи или право доступа к API Xiaomi.

До подтверждённого генератора не добавлять фиктивную кнопку «Создать3D питомца».
Следующие проверяемые шаги: точный gateway/permissions/availability, условия
сервиса, затем выбранное пользователем фото, настоящий результат и проверка его
декодирования/приватного хранения. Интернет-разрешение текущего APK не менялось.

Ignored source evidence: `work/extracted/hongkong/AiCompanionApiService.java`,
`AiCompanionRealApiProvider.java`, его generateImage/submitVideoTask coroutines,
`AiCompanionAcquireApi.java`, `AiCompanionConstants.java`,
`CompanionGenerateRawDataBuilder.java`.
