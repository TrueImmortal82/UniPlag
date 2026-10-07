# 🛡️ UniPlag & ICG Enterprise v0.4.1 — Update #54

<div align="center">

![BlackBox](https://img.shields.io/badge/BlackBox-v2%20Ed25519--Attested-black?style=for-the-badge&logo=lock)
![Security](https://img.shields.io/badge/Ledger-56%20Blocks%20Sealed-purple?style=for-the-badge&logo=shield)
![Languages](https://img.shields.io/badge/Languages-RU%20%7C%20EN%20%7C%20UZ-green?style=for-the-badge)
![Release](https://img.shields.io/badge/Release-v0.4.1--enterprise-blue?style=for-the-badge&logo=github)

**Next-Generation Academic Integrity, AI Content Detection & Intellectual Contribution Graph (ICG) Verification Platform.**

[🇷🇺 Русский](#-русский-ru) • [🇬🇧 English](#-english-en) • [🇺🇿 O'zbekcha](#-ozbekcha-uz)

</div>

---

# 🇷🇺 Русский (RU)

## 🌟 Обзор платформы

**UniPlag & ICG** — академическая платформа нового поколения для университетов, диссертационных советов и научных издательств. Система решает ключевые вызовы современного образования: **машинную генерацию текста (LLM)** и **пассивную компиляцию источников без самостоятельного научного вклада автора**.

### 🎯 4-Метрическая модель экспертизы
1. **Оригинальность текста** (0–100%, порог ≥ 70%) — текстовая новизна относительно глобальных и локальных корпусов.
2. **Заимствования и совпадения** (0–100%, порог < 20%) — выявление цитирований с подсветкой фрагментов.
3. **Детекция нейросетей (AI / LLM)** (0–100%, порог < 25%) — стилометрический анализ признаков генерации (ChatGPT и др.).
4. **Граф интеллектуального вклада (ICG v0.4)** (0–100%, порог ≥ 45%) — оценка глубины синтеза источников, логики аргументации (DAG) и самостоятельных авторских выводов.

Дополнительные контуры: **Cheating Guard** (хомоглифы, скрытый текст DOCX — Update #50) и **Source Finder** (поиск реального источника через decode-обфускацию — Update #51).

### ⚡ Запуск (готовый дистрибутив)
Самый простой способ — **скачать готовый `UniPlag_Server.exe`** со страницы [Releases](https://github.com/TrueImmortal82/UniPlag/releases) (ассет `v0.4.1-enterprise`). Никаких ключей и зависимостей не требуется — мастер-ключ расшифрования уже встроен на этапе сборки.

1. Скачайте **`UniPlag_Server.exe`** из [Releases](https://github.com/TrueImmortal82/UniPlag/releases/latest).
2. Запустите двойным кликом (порт `7932`, при занятости автоматически `7933 → 7934 → …`).
3. Откройте в браузере: **`http://localhost:7932`**.

*(Опционально)* для глубокого нейросетевого анализа установите [**Ollama**](https://ollama.com) — при первом старте платформа автоматически подтянет оптимальную модель (`qwen2.5:1.5b` / `llama3.2`).

### 🧪 Проверка подлинности дистрибутива (для разработчиков)
```bash
python run_blackbox.py --verify-only
```
Проверяет **Ed25519-аттестацию издателя** контейнера `.bbx` через встроенный публичный ключ — без мастер-ключа.

### 🔐 Модель безопасности
- **`.bbx` v2**: Ed25519-подпись издателя (публичный ключ встроен в лаунчер, приватный — у издателя) + шифрование AES-256-GCM данных.
- **Fail-closed**: мастер-ключ отсутствует в репозитории и лаунчерах; расшифрование — только через env `UNIPLAG_SOVEREIGN_KEY_512` или `.security/sovereign_512.key` (для лицензированных билдов).
- **512-битная печать подлинности (MAC)** PDF-справок с онлайн-проверкой `/verify/{seal}`.
- **Опция привязки к машине** (Windows DPAPI): `--bind-machine`.
- **Аудит-реестр (ledger)**: 56 блоков chained-манифеста (<code>main</code> ветка разработки).

⚠️ Персональные учётные записи по умолчанию (`admin` / `teacher` / `student`) при первом входе **требуют смены пароля** (сигнал — красный баннер в шапке).

### 🧩 Системные требования
| Компонент | Минимум | Рекомендуется |
|---|---|---|
| ОС | Windows 10 x64 | Windows 11 x64 / Server 2019+ |
| RAM | 4 GB | 8 GB+ |
| Python (dev) | 3.10+ | 3.12 |
| Ollama (AI-анализ) | — | установлена, модель `qwen2.5:1.5b` |

### 📚 Документация
| Файл | Содержание |
|---|---|
| [USER_GUIDE.md](USER_GUIDE.md) | Руководство пользователя (RU / EN / UZ) |
| [RELEASE_NOTES.md](RELEASE_NOTES.md) | История обновлений (Update #50 → #54) |
| [INTEGRATION_STANDARDS.md](INTEGRATION_STANDARDS.md) | Стандарты интеграции и аудита |
| [SECURITY.md](SECURITY.md) | Политика безопасности и ответственное раскрытие |

---

# 🇬🇧 English (EN)

## 🌟 Platform Overview

**UniPlag & ICG** is a next-generation academic verification platform for universities, dissertation committees, and research publishers. It tackles the two critical challenges of modern academia: **AI-generated text (LLMs)** and **passive compilation lacking authentic authorial contribution**.

### 🎯 4-Metric Academic Evaluation Model
1. **Text Originality** (0–100%, threshold ≥ 70%).
2. **Plagiarism & Borrowings** (0–100%, threshold < 20%) — multi-source matching with fragment highlighting.
3. **AI Generation Probability** (0–100%, threshold < 25%) — stylometric LLM detection (ChatGPT, etc.).
4. **Intellectual Contribution Graph (ICG v0.4)** (0–100%, threshold ≥ 45%) — epistemic DAG reasoning modeling synthesis depth and novel inferences.

Extra pipelines: **Cheating Guard** (homoglyphs, hidden DOCX text — Update #50) and **Source Finder** (real-source tracing through de-obfuscation — Update #51).

### ⚡ Quick Start (Ready Build)
The easiest way is to **download the prebuilt `UniPlag_Server.exe`** from the [Releases](https://github.com/TrueImmortal82/UniPlag/releases) page (asset `v0.4.1-enterprise`). No keys or dependencies needed — the decryption master key is already baked in at build time.

1. Download **`UniPlag_Server.exe`** from [Releases](https://github.com/TrueImmortal82/UniPlag/releases/latest).
2. Double-click to run (port `7932`, auto-fallback `7933 → 7934 → …`).
3. Open **`http://localhost:7932`** in your browser.

*(Optional)* For deep neural analysis install [**Ollama**](https://ollama.com) — the platform auto-pulls the optimal model (`qwen2.5:1.5b` / `llama3.2`) on first launch.

### 🧪 Authenticity Verification (Developers)
```bash
python run_blackbox.py --verify-only
```
Verifies the **Ed25519 publisher attestation** of the `.bbx` container through the embedded public key — no master key required.

### 🔐 Security Model
- **`.bbx` v2**: Ed25519 publisher signature (public key embedded in launchers; private key held only by the publisher) + AES-256-GCM payload encryption.
- **Fail-closed**: no master key exists in this repository or in the launchers; decryption is only possible via env `UNIPLAG_SOVEREIGN_KEY_512` or `.security/sovereign_512.key` (licensed builds).
- **512-bit authenticity seal (MAC)** on PDF certificates with online verification at `/verify/{seal}`.
- **Machine binding option** (Windows DPAPI): `--bind-machine`.
- **Audit ledger**: 56 sealed blocks of the chained integrity manifest.

⚠️ Default accounts (`admin` / `teacher` / `student`) must change their password on first login (a red banner prompts this).

### 🧩 System Requirements
| Component | Minimum | Recommended |
|---|---|---|
| OS | Windows 10 x64 | Windows 11 x64 / Server 2019+ |
| RAM | 4 GB | 8 GB+ |
| Python (dev only) | 3.10+ | 3.12 |
| Ollama (AI analysis) | — | installed, `qwen2.5:1.5b` |

### 📚 Documentation
| File | Contents |
|---|---|
| [USER_GUIDE.md](USER_GUIDE.md) | User guide (RU / EN / UZ) |
| [RELEASE_NOTES.md](RELEASE_NOTES.md) | Release history (Update #50 → #54) |
| [INTEGRATION_STANDARDS.md](INTEGRATION_STANDARDS.md) | Integration & audit standards |
| [SECURITY.md](SECURITY.md) | Security policy & responsible disclosure |

---

# 🇺🇿 O'zbekcha (UZ)

## 🌟 Platforma haqida

**UniPlag & ICG** — universitetlar, dissertatsiya kengashlari va ilmiy nashriyotlar uchun yangi avlod akademik ekspertiza platformasi. Tizim ikkita asosiy muammoni hal etadi: **sun'iy intellekt (LLM / ChatGPT) matnini aniqlash** va **mualliflik hissasisiz passiv kompilyatsiyani baholash**.

### 🎯 4-Metrik baholash modeli
1. **Matn originalligi** (0–100%, ≥ 70%).
2. **O'zlashtirish va mosliklar** (0–100%, < 20%).
3. **Sun'iy intellektni aniqlash** (0–100%, < 25%).
4. **Intellektual hissa grafigi (ICG v0.4)** (0–100%, ≥ 45%).

### ⚡ Ishga tushirish (tayyor build)
Eng oson usul — [Releases](https://github.com/TrueImmortal82/UniPlag/releases) sahifasidan tayyor **`UniPlag_Server.exe`**ni yuklab olish. Kalitlar va qo'shimcha bog'liqliklar shart emas.

1. **`UniPlag_Server.exe`**ni yuklab oling ([Releases](https://github.com/TrueImmortal82/UniPlag/releases/latest)).
2. Ikki marta bosib ishga tushiring (7932-port, band bo'lsa avtomatik 7933 → 7934 → …).
3. Brauzerda oching: **`http://localhost:7932`**.

*(Ixtiyoriy)* Chuqur neyrotahlil uchun [**Ollama**](https://ollama.com) o'rnating — dastur birinchi ishga tushishda eng qulay modelni avtomatik yuklaydi.

### 🧪 Qidiruv/xavfsizlikni tekshirish (dasturchilar uchun)
```bash
python run_blackbox.py --verify-only
```

### 📚 Hujjatlar
| Fayl | Mazmuni |
|---|---|
| [USER_GUIDE.md](USER_GUIDE.md) | Foydalanuvchi qo'llanmasi (RU / EN / UZ) |
| [RELEASE_NOTES.md](RELEASE_NOTES.md) | Yangilanishlar tarixi (Update #50 → #54) |
| [INTEGRATION_STANDARDS.md](INTEGRATION_STANDARDS.md) | Integratsiya standartlari |
| [SECURITY.md](SECURITY.md) | Xavfsizlik siyosati |

---

## 📁 Sample Files / Namunaviy fayllar

| File | Lang | Description | Verdict |
|---|---|---|---|
| [`samples/01_high_icg_original_research.docx`](samples/01_high_icg_original_research.docx) | 🇷🇺 RU | High-ICG original research paper | 🟢 Recommended |
| [`samples/02_ai_generated_essay.txt`](samples/02_ai_generated_essay.txt) | 🇷🇺 RU | AI-generated essay (AI detection) | 🔴 AI detected |
| [`samples/03_plagiarism_compilation_review.txt`](samples/03_plagiarism_compilation_review.txt) | 🇷🇺 RU | Compilation/plagiarism review | 🟡 Compilation |
| [`samples/04_english_academic_paper.pdf`](samples/04_english_academic_paper.pdf) | 🇬🇧 EN | English academic paper | 🟢 Recommended |

## ⚖️ License / Licence / Litsenziya

Full terms are in [**LICENSE.md**](LICENSE.md) *(EULA in RU / EN / UZ)*.

All rights reserved. Proprietary analytical models, epistemic DAG logic, and cryptographic verification mechanisms are protected intellectual property.