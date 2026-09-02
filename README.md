# 🛡️ UniPlag & ICG Enterprise v0.4.1

<div align="center">

![Platform](https://img.shields.io/badge/Platform-UniPlag%20%26%20ICG%20Enterprise-blue?style=for-the-badge&logo=shield)
![Security](https://img.shields.io/badge/Security-512--bit%20Cryptographic%20Seal-purple?style=for-the-badge&logo=lock)
![Languages](https://img.shields.io/badge/Languages-🇷🇺%20RU%20|%20🇬🇧%20EN%20|%20🇺🇿%20UZ-green?style=for-the-badge)
![BlackBox](https://img.shields.io/badge/Format-BlackBox%20%28Zero--Disk%29-black?style=for-the-badge)

**Next-Generation Autonomous Academic Integrity, AI Content Analysis & Intellectual Contribution Graph (ICG) Verification Platform.**

[🇷🇺 Русский](#-русский-ru) • [🇬🇧 English](#-english-en) • [🇺🇿 O'zbekcha](#-ozbekcha-uz)

</div>

---

# 🇷🇺 Русский (RU)

## 🌟 Обзор платформы
**UniPlag & ICG** — комплексная академическая платформа нового поколения для университетов, диссертационных советов и научных издательств. Система решает ключевые вызовы современного образования: **машинную генерацию текста нейросетями (LLM)** и **пассивную компиляцию источников без самостоятельного научного вклада автора**.

### 🎯 4-Метрическая модель экспертизы
1. **Оригинальность текста** (0–100%) — текстовая новизна относительно корпусов.
2. **Заимствования и совпадения** (0–100%) — выявление цитирований с подсветкой фрагментов.
3. **Детекция нейросетей (AI)** — стилометрический анализ признаков генерации (ChatGPT / LLM).
4. **Граф интеллектуального вклада (ICG v0.4)** — оценка глубины синтеза источников, логики аргументации (DAG) и самостоятельных авторских выводов.

### 📜 Официальные PDF-справки с 512-битной печатью
* Формирование защищённых векторных сертификатов (формат А4) для ГЭК, диссертационных советов и деканатов.
* **512-битная цифровая печать подлинности (SHA-512)** и онлайн-проверка через постоянную ссылку `/verify/{seal}`.

### 🤖 Локальный контур Ollama и автозагрузка моделей
* Для глубокого нейросетевого анализа требуется установленная [**Ollama**](https://ollama.com).
* При первом старте система **автоматически подгружает оптимальную модель** (`qwen2.5:1.5b` / `llama3.2`), в том числе в защищённом контейнере BlackBox.

### 🚀 Быстрый запуск
```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Запустите защищённый BlackBox контейнер
run_blackbox.bat
# или: python run_blackbox.py --port 7932
```
* Открыть в браузере: **`http://localhost:7932`**

---

# 🇬🇧 English (EN)

## 🌟 Platform Overview
**UniPlag & ICG** is a next-generation academic verification platform designed for universities, dissertation committees, and research publishers. The system addresses the critical challenges of modern academia: **AI-generated text (LLMs)** and **passive compilation lacking authentic authorial research contribution**.

### 🎯 4-Metric Academic Evaluation Model
1. **Text Originality** (0–100%) — lexical and structural novelty across global and local corpora.
2. **Plagiarism & Citations** (0–100%) — multi-source borrowing detection with fragment highlighting.
3. **AI Generation Probability** — stylometric and syntactic analysis for detecting LLMs (ChatGPT, etc.).
4. **Intellectual Contribution Graph (ICG v0.4)** — epistemic DAG reasoning modeling evaluating depth of source synthesis and novel author inferences.

### 📜 Official 512-bit Sealed PDF Certificates
* Official vector A4 certificates ready for state examination boards and accreditation.
* **512-bit Cryptographic Authenticity Seal (SHA-512)** with instant online verification at `/verify/{seal}`.

### 🤖 Local Neural Engine (Ollama) & Auto-Model Fetching
* For deep neural semantic analysis, [**Ollama**](https://ollama.com) is recommended.
* On initial launch, UniPlag **automatically pulls the optimal model** (`qwen2.5:1.5b` / `llama3.2`) in background.

### 🚀 Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch encrypted BlackBox container
run_blackbox.bat
# or: python run_blackbox.py --port 7932
```
* Open in browser: **`http://localhost:7932`**

---

# 🇺🇿 O'zbekcha (UZ)

## 🌟 Platforma haqida umumiy sharh
**UniPlag & ICG** — universitetlar, dissertatsiya kengashlari va ilmiy nashriyotlar uchun mo'ljallangan yangi avlod akademik ekspertiza platformasi. Tizim zamonaviy ta'limning eng muhim muammolarini hal etadi: **sun'iy intellekt (LLM / ChatGPT) matnini aniqlash** hamda **mualliflik hissasisiz ko'chirib olish (passiv kompilyatsiya) darajasini baholash**.

### 🎯 4-Metrikali akademik baholash modeli
1. **Matn originalligi** (0–100%) — akademik bazalarga nisbatan muallif matnining yangilik darajasi.
2. **Olingan parchalar va iqtiboslar** (0–100%) — manbalar bilan mosliklarni aniq ko'rsatish va ajratib ko'rsatish.
3. **Sun'iy intellektni aniqlash (AI)** — neyrotarmoqlar uslubiy belgilarini aniqlash.
4. **Intellektual hissa grafigi (ICG v0.4)** — adabiyotlar tahlili chuqurligi (DAG) va muallifning mustaqil ilmiy xulosalarini baholash.

### 📜 512-bitli raqamli muhrga ega rasmiy PDF-ma'lumotnomalar
* Davlat attestatsiya komissiyasi (DAK), dekanat va ilmiy kengashlar uchun A4 formatidagi rasmiy sertifikatlar.
* **512-bitli raqamli tasdiqlash muhri (SHA-512)** va `/verify/{seal}` havolasi orqali onlayn haqiqiylikni tekshirish.

### 🤖 Mahalliy Ollama neyrotizimi va modellarni avtomatik yuklash
* Chuqur neyrotarmoq tahlili uchun [**Ollama**](https://ollama.com) dasturi o'rnatilgan bo'lishi lozim.
* Dastur birinchi marta ishga tushganda eng qulay va tezkor modelni (**`qwen2.5:1.5b`** / `llama3.2`) **avtomatik ravishda yuklab oladi**.

### 🚀 Tezkor ishga tushirish
```bash
# 1. Kerakli kutubxonalarni o'rnatish
pip install -r requirements.txt

# 2. Himoyalangan BlackBox konteynerini ishga tushirish
run_blackbox.bat
# yoki: python run_blackbox.py --port 7932
```
* Brauzerda ochish: **`http://localhost:7932`**

---

## 📁 Namunaviy fayllar / Sample Files / Демонстрационные примеры

| Fayl / File | Til / Lang | Tavsif / Description | Natija / Verdict |
|---|---|---|:---:|
| [`samples/01_high_icg_original_research.docx`](samples/01_high_icg_original_research.docx) | 🇷🇺 RU | Yuqori ICG va mualliflik sinteziga ega ilmiy BMI | 🟢 Tavsiya etiladi |
| [`samples/02_ai_generated_essay.txt`](samples/02_ai_generated_essay.txt) | 🇷🇺 RU | Neyrotarmoq belgilari mavjud esse (AI deteksiya) | 🔴 AI aniqlandi |
| [`samples/03_plagiarism_compilation_review.txt`](samples/03_plagiarism_compilation_review.txt) | 🇷🇺 RU | Matn o'zlashtirishlari mavjud referativ sharh | 🟡 Kompilyatsiya |
| [`samples/04_english_academic_paper.pdf`](samples/04_english_academic_paper.pdf) | 🇬🇧 EN | Xalqaro sertifikat uchun ingliz tilidagi ilmiy maqola | 🟢 Recommended |

---

## 🔒 Litsenziya va maxfiylik / License & Confidentiality

Barcha huquqlar himoyalangan. Analitik modellar, ICG mantiqiy graflari va kriptografik tekshirish mexanizmlari mualliflik mulki hisoblanadi.
