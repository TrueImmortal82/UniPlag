# 🛡️ UniPlag & ICG Enterprise v0.4.1 (Official Public Release)

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-blue.svg)](LICENSE.md)
[![Build Status](https://img.shields.io/badge/BlackBox-PASS%2014%2F14-success.svg)](dist/UniPlag_Enterprise.bbx)
[![Security](https://img.shields.io/badge/Ledger-512--bit%20Sealed%20(Block%20%2347)-emerald.svg)](.security/)
[![Languages](https://img.shields.io/badge/Languages-RU%20%7C%20EN%20%7C%20UZ-orange.svg)](#)

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

### 🚀 Инструкция по запуску / Quick Start / Ishga tushirish:
1. Скачайте репозиторий или прикреплённые файлы релиза.
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Запустите двойным кликом файл **`run_blackbox.bat`** (или в терминале: `python run_blackbox.py --port 7932`).
4. Откройте в браузере: **`http://localhost:7932`**
