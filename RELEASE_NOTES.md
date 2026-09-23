# 🛡️ UniPlag & ICG Enterprise v0.4.1 (Official Public Release)

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-blue.svg)](LICENSE.md)
[![Build Status](https://img.shields.io/badge/BlackBox-PASS%2014%2F14-success.svg)](dist/UniPlag_Enterprise.bbx)
[![Security](https://img.shields.io/badge/Ledger-512--bit%20Sealed%20(Block%20%2347)-emerald.svg)](.security/)
[![Languages](https://img.shields.io/badge/Languages-RU%20%7C%20EN%20%7C%20UZ-orange.svg)](#)

---

# 🔐 Update #50 — Adaptive Heuristic Cheating Detector & Active Learning Loop

## 🇷🇺 Русский

Новый модуль **академической честности (Cheating Guard)** с контуром активного обучения.

- **Детекция обфускации текста**: хомоглифы (кириллица/латиница: `а/a`, `с/c`, `е/e`, `о/o`, `р/p`, `х/x`, `у/y`), невидимые разделители нулевой ширины (ZWSP/ZWNJ/ZWJ, soft-hyphen, BOM).
- **Аудит структуры DOCX (OpenXML)**: скрытый текст (`w:vanish`), микрошрифты `<=3pt`, белый текст на белом фоне.
- **Adaptive Weighted Model**: индекс риска `0–100%`; hard rules — мгновенный `flagged` при скрытом тексте или `>=6` слов с хомоглифами.
- **Active Learning**: подтверждённые преподавателем прецеденты сохраняются в `cheating_signatures` и пересчитывают чувствительность `learn_from_feedback()`.
- **Интеграция**: 5-я метрика в отчёте «Читинг / Обход», блок улик при риске `>=30%`, красный бейдж в дашборде, эндпоинт `POST /report/{id}/cheating/confirm` (учитель/админ).
- Заверено Блоком #50 в Sovereign Ledger (HMAC-SHA512).

## 🇬🇧 English

New **academic integrity (Cheating Guard)** module with an active learning loop.

- **Obfuscation detection**: homoglyphs (Cyrillic/Latin pairs), zero-width separators (ZWSP/ZWNJ/ZWJ, soft-hyphen, BOM).
- **DOCX (OpenXML) audit**: hidden text (`w:vanish`), micro-fonts `<=3pt`, white-on-white text.
- **Adaptive Weighted Model**: risk index `0–100%`; hard rules instantly flag hidden text or `>=6` homoglyph words.
- **Active Learning**: teacher-confirmed precedents persist into `cheating_signatures` and retune sensitivity via `learn_from_feedback()`.
- **Integration**: 5th report metric «Cheating Guard», evidence block at risk `>=30%`, red dashboard badge, `POST /report/{id}/cheating/confirm` (teacher/admin).
- Sealed in Sovereign Ledger **Block #50** (HMAC-SHA512).

---

# 🔍 Update #51 — Source Tracing & De-Obfuscation (поиск реального источника)

## 🇷🇺 Русский

Новый модуль **Source Finder**: даже когда текст пересобран с подменёнными символами (хомоглифы, нулевые пробелы, soft-hyphen) и обходит шингловый антиплагиат, система находит **реальный источник**.

- **Декодирование обфускации** (`canonicalize`): удаление нулевых разделителей (ZWSP/ZWNJ/ZWJ, soft-hyphen, BOM, C0-артефакты) и обратная свёртка латинских лукейликов в кириллицу.
- **Локальный поиск**: повторный шингл-фингерпринт раскодированного текста по корпусу вуза (загруженные работы, arXiv/web-индексы). В отчёте: `raw` vs `decoded` совпадение — 0% → 87% («текст был пересобран для обхода антиплагиата!»).
- **Веб-фолбэк**: если корпус не даёт совпадения — параллельный опрос открытых репозиториев (OpenAlex, Crossref, arXiv, DuckDuckGo, опционально свой SearXNG), скачивание кандидатов и выравнивание.
- **Настройки админа** (`/settings`): вкл/выкл локального и веб-поиска, пороги срабатываний, провайдеры, лимиты, таймауты.
- **UI**: блок «🔍 Декодированный источник» в отчёте с таблицей найденного (название, автор, % совпадения, ссылка) и раскодированным фрагментом для ручного поиска.
- **Качество ICG-отчёта**: фильтр «мусорных» claim-узлов из списка литературы — одиночные инициалы («V.», «P.», «С.», «Е.»), сокращения («ст.», «мед.», «журн.»), номера/диапазоны страниц («224 с.», «V. 43», «Р. 45–53») и именные фрагменты записей («Maher J.J.», «Сторожаков, Е.И.») больше не становятся узлами REPRODUCTION. Для настоящих предложений (от 3 токенов) фильтр неактивен. Также расширено распознавание заголовка секции литературы («Рекомендуемая литература», «Литература», «Источники»). На реальной статье: 490 → 377 узлов.

## 🇬🇧 English

New **Source Finder** module traces the *real origin* of a document even when the text was re-assembled with substituted symbols that bypass shingle-based plagiarism checks.

- **De-obfuscation** (`canonicalize`): removes zero-width separators (ZWSP/ZWNJ/ZWJ, soft-hyphen, BOM, C0 artifacts) and folds Latin look-alikes back into Cyrillic.
- **Local search**: re-fingerprints the decoded text against the university corpus (uploaded works, arXiv/web indexes). Report shows `raw` vs `decoded` similarity — e.g. 0% → 87% (flagged «text was re-assembled to bypass plagiarism checks!»).
- **Web fallback**: when the corpus yields no hit — parallel queries to open repositories (OpenAlex, Crossref, arXiv, DuckDuckGo, optional self-hosted SearXNG), candidate page fetching and alignment.
- **Admin settings** (`/settings`): toggles, thresholds, providers, limits, timeouts.
- **UI**: «🔍 Decoded Source» block in the report with a hits table (title, author, similarity, link) and a decoded fragment for manual lookup.
- **ICG report quality**: noise claim-node filter for bibliography tokens — single initials («V.», «P.»), abbreviations («ст.», «мед.», «журн.»), page numbers/ranges («224 с.», «V. 43», «Р. 45–53») and author-name fragments («Maher J.J.», «Сторожаков, Е.И.») no longer become REPRODUCTION nodes. Real sentences (≥3 tokens) are unaffected. Broadened literature-section header detection («Рекомендуемая литература», «Литература», «Источники»). On a real article: 490 → 377 nodes.

---

## 🇷🇺 Русский

Официальный обновлённый релиз университетской платформы **UniPlag & ICG Enterprise v0.4.1**.

### 🌟 Что нового и ключевые возможности:
- **100% Трёхъязычный интерфейс (RU / EN / UZ)**: Полная сквозная локализация всех 8 разделов (Личный кабинет студента, Рейтинги академических лиг, Кабинет преподавателя TeacherScore, Сдача работ, Полный отчёт проверки с 4 метриками, Интерактивный ридер текста, Руководство Guide, Веб-архив корпуса, Поиск в arXiv, Панели администрирования).
- **4-Метрическая модель экспертизы**: Комплексная оценка работы (Оригинальность $\ge 70\%$, Заимствования $< 20\%$, Детекция нейросетей AI $< 25\%$, Граф интеллектуального вклада ICG v0.4 $\ge 45\%$).
- **512-битные PDF-справки и верификация**: Векторные сертификаты для ГЭК, диссертационных советов и ВАК с цифровой печатью подлинности HMAC-SHA512 и онлайн-верификацией (`/verify/{seal}`).
- **Интеграция с Ollama & Поддержка Cloud-моделей**: Автоматическое обнаружение Ollama, поддержка легкой локальной `qwen2.5:1.5b` и тяжелых облачных моделей (`qwen3.5:397b-cloud`).
- **Защищённый BlackBox (`.bbx`)**: Zero-Disk execution строго в оперативной памяти (RAM) с шифрованием AES-256-GCM. 14 из 14 тестов безопасности пройдены (100% PASS).
- **Надёжный лаунчер**: Автоматическое определение свободных портов (7932 $\to$ 7933 $\to$ ...), предотвращение конфликтов и защита от сбоев.

---

## 🇬🇧 English

Official updated release of the **UniPlag & ICG Enterprise v0.4.1** academic verification platform.

### 🌟 What's New & Key Capabilities:
- **100% Full Trilingual Localization (EN / RU / UZ)**: Seamless interface localization across all 8 core views (Student Dashboard, Academic Cohort Leaderboards, Faculty TeacherScore, Submission Portal, 4-Metric Examination Report, Text Highlighter Reader, User Guide, Corpus Indexer, arXiv Open Science Ingestion, and Administration Panels).
- **4-Metric Academic Evaluation**: Comprehensive multi-layer evaluation (Originality $\ge 70\%$, Borrowings $< 20\%$, Neural AI Detection $< 25\%$, Epistemic DAG Reasoning Novelty ICG v0.4 $\ge 45\%$).
- **512-bit Sealed PDF Certificates**: Cryptographically authenticated A4 certificates with online seal verification (`/verify/{seal}`) for academic examination boards.
- **Ollama Neural Engine & Cloud Model Support**: Automatic local Ollama discovery, zero-config pulling of `qwen2.5:1.5b`, and seamless integration with `qwen3.5:397b-cloud`.
- **BlackBox Zero-Disk Distribution**: AES-256-GCM encrypted package running strictly in RAM. 14/14 automated security & integrity tests passed (100% PASS).
- **Collision-Free Standalone Launcher**: Automatic port discovery (7932 $\to$ 7933...), resilient error handling, and robust cross-platform execution.

---

## 🇺🇿 O'zbekcha

**UniPlag & ICG Enterprise v0.4.1** akademik ekspertiza va ilmiy hissa monitoringi platformasining rasmiy yangilangan relizi.

### 🌟 Asosiy yangiliklar va imkoniyatlar:
- **100% 3 tilda to'liq interfeys (UZ / EN / RU)**: 8 ta asosiy bo'limning to'liq o'zbekcha tarjimasi (Talaba shaxsiy kabineti, O'qituvchi TeacherScore reytingi, Ish topshirish, 4 ta metrikali ekspertiza hisoboti, ICG ilmiy sintez grafigi, Foydalanuvchi qo'llanmasi, Universitet bazasi va arXiv ilmiy qidiruvi).
- **4-Metrikali baholash modeli**: Matn originalligi ($\ge 70\%$), Ko'chirmalar ($< 20\%$), Sun'iy intellekt matnini aniqlash ($< 25\%$) va Intellektual hissa grafigi (ICG v0.4 $\ge 45\%$).
- **512-bitli raqamli muhrli PDF-sertifikatlar**: DAK va ilmiy kengashlar uchun onlayn tekshiriluvchi rasmiy ma'lumotnomalar (`/verify/{seal}`).
- **Ollama neyrotizimi va bulutli modellar**: `qwen2.5:1.5b` va `qwen3.5:397b-cloud` modellari bilan to'liq integratsiya.
- **BlackBox xavfsiz konteyneri**: AES-256-GCM shifrlash va to'liq tezkor xotirada (RAM) ishlash (14/14 testlar PASS).
- **Port to'qnashuvlaridan himoyalangan avtomatik launcher**: 7932 port band bo'lsa, keyingi bo'sh portga avtomatik o'tish.

---

# 🌍 Update #53 — Full Trilingual Localization Near-Zero & Uzbek PDF Certificate

## 🇷🇺 Русский

Релиз закрывает аудит полного перевода интерфейса на три языка (RU / EN / UZ) и добавляет узбекский академический сертификат.

- **Исправлен критический баг локализации `loc()`**: вызов с 3 аргументами `loc(ru, en, uz)` всегда возвращал русский текст, так как третий аргумент интерпретировался как пользовательский текст. Баннер смены пароля (`base.html`) и страница `/account/password` переведены на корректную форму `loc(ru, en, uz, cur_lang)`.
- **Динамический `<html lang>`**: атрибут языка страницы больше не захардкожен как `ru`, а следует за выбранным языком сессии.
- **Узбекский PDF-сертификат**: добавлена кнопка **📄 PDF (UZ)** в отчёт проверки (`/report/{id}/pdf?lang=uz`); генератор сертификатов уже содержал полную узбекскую локализацию (заголовки, метаданные, вердикты, печать).
- **Руководство пользователя**: добавлены разделы FAQ (RU / EN / UZ).
- **Тесты**: набор `test_multilingual.py` расширен до трёх языков (CASE 4: генерация UZ-PDF, роут `?lang=uz`, наличие кнопки) — 18/18 PASS; `test_user_guide.py` 14/14 PASS; pytest 8/8 PASS.
- **Аппаратный аудит перевода**: все ключи словаря i18n покрыты на всех трёх языках (категории A/B — пустые ключи отсутствуют), UZ-интерфейс проверен рендерингом (Barcha tekshiruvlar, Originallik, Qo'llanma).
- **Реестр**: блок #53, манифест 75 файлов переподписан 512-битным ключом.

## 🇬🇧 English

This release completes a full trilingual (RU / EN / UZ) interface translation audit and ships the Uzbek academic PDF certificate.

- **Critical `loc()` localization bug fixed**: `loc(ru, en, uz)` with 3 arguments always returned Russian, because the 3rd argument was treated as custom text. The password-change banner (`base.html`) and the `/account/password` page now use the correct `loc(ru, en, uz, cur_lang)` form.
- **Dynamic `<html lang>`**: page language attribute follows the active session language instead of being hardcoded to `ru`.
- **Uzbek PDF certificate**: new **📄 PDF (UZ)** button on the check report (`/report/{id}/pdf?lang=uz`); the certificate generator already shipped full Uzbek strings (headers, metadata, verdicts, seal).
- **User guide**: FAQ sections added (RU / EN / UZ).
- **Tests**: `test_multilingual.py` extended to three languages (CASE 4: UZ PDF generation, `?lang=uz` route, button presence) — 18/18 PASS; `test_user_guide.py` 14/14 PASS; pytest 8/8 PASS.
- **Full translation audit**: every i18n key is present in all three languages (categories A/B clean), UZ UI verified by rendering.
- **Ledger**: block #53, 75-file manifest re-signed with the 512-bit sovereign key.

## 🇺🇿 O'zbekcha

- **`loc()` lokalizatsiya xatosi tuzatildi**: `loc(ru, en, uz)` 3 argument bilan doim rus tilini qaytarardi; banner va `/account/password` sahifasi `loc(ru, en, uz, cur_lang)` shakliga o'tkazildi.
- **Dinamik `<html lang>`**: sahifa tili sessiya tiliga bog'lanadi.
- **O'zbek PDF-sertifikati**: hisobotga **📄 PDF (UZ)** tugmasi qo'shildi (`/report/{id}/pdf?lang=uz`).
- **Qo'llanma**: FAQ bo'limlari qo'shildi (RU / EN / UZ).
- **Testlar**: `test_multilingual.py` 18/18 PASS, `test_user_guide.py` 14/14 PASS, pytest 8/8 PASS.

---

# 🛠️ Update #52 — MVP Hardening: Persistent Sessions & Clean Requirements

## 🇷🇺 Русский

Этап доведения платформы до полностью рабочего MVP.

- **Персистентные сессии в БД**: сессии больше не хранятся in-memory — токены живут в таблице `user_sessions` и переживают рестарт сервера (TTL 7 дней, user-agent/IP в базе, фоновый `prune_expired_sessions`). Сессия удаляется при `logout`.
- **Смена пароля + защита от дефолтных паролей**: новый экран `/account/password` (проверка текущего пароля, минимум 6 символов); если пользователь работает с паролем по умолчанию (`admin123`/`teacher123`/`student123`) — в шапке виден красный баннер с требованием сменить пароль.
- **Корректная работа со временем**: все вызовы `datetime.utcnow()` (deprecated) заменены на timezone-aware UTC по всему коду; в `checker.py` устранён скрытый `NameError` (неимпортированный `datetime`).
- **Таймауты HTTP**: проверка Ollama `timeout=5`, скоринг — конфигурируемый `OLLAMA_TIMEOUT_SEC` (по умолчанию 300 s, env `UNIPLAG_OLLAMA_TIMEOUT_SEC`); все веб-провайдеры (OpenAlex/Crossref/arXiv/SearXNG/DDG) — таймаут 8 s с ограничением пула потоков.
- **Чистые зависимости**: `requirements.txt` актуализирован (scikit-learn/joblib/numpy/httpx и др.); тестовая утилита выделена в `requirements-dev.txt` (`pytest>=8.0`).

## 🇬🇧 English

Stage of hardening the platform into a fully workable MVP.

- **Persistent DB-backed sessions**: session tokens now live in the `user_sessions` table and survive server restarts (7-day TTL, user-agent/IP stored, `prune_expired_sessions` housekeeping). Logout removes the row.
- **Password change + default-password guard**: new `/account/password` screen (current password check, 6+ chars); a red top banner forces a change when a default password (`admin123`/`teacher123`/`student123`) is still in use.
- **Timezone-correct code**: all deprecated `datetime.utcnow()` calls replaced with timezone-aware UTC app-wide; fixed a hidden `NameError` in `checker.py`.
- **HTTP timeouts**: Ollama discovery `timeout=5`, scoring uses configurable `OLLAMA_TIMEOUT_SEC` (default 300 s, env `UNIPLAG_OLLAMA_TIMEOUT_SEC`); all web providers (OpenAlex/Crossref/arXiv/SearXNG/DDG) bounded at 8 s with limited thread pool.
- **Clean requirements**: `requirements.txt` refreshed (scikit-learn/joblib/numpy/httpx, etc.); test tooling split into `requirements-dev.txt` (`pytest>=8.0`).

---
1. Скачайте репозиторий или прикреплённые файлы релиза.
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Запустите двойным кликом файл **`run_blackbox.bat`** (или в терминале: `python run_blackbox.py --port 7932`).
4. Откройте в браузере: **`http://localhost:7932`**
