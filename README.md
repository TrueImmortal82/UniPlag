# 🛡️ UniPlag & ICG Enterprise v0.4.1

<div align="center">

![Platform](https://img.shields.io/badge/Platform-UniPlag%20%26%20ICG%20Enterprise-blue?style=for-the-badge&logo=shield)
![Security](https://img.shields.io/badge/Security-512--bit%20Cryptographic%20Seal-purple?style=for-the-badge&logo=lock)
![Languages](https://img.shields.io/badge/Languages-🇷🇺%20RU%20|%20🇬🇧%20EN%20|%20🇰🇿%20KK-green?style=for-the-badge)
![BlackBox](https://img.shields.io/badge/Format-BlackBox%20%28Zero--Disk%29-black?style=for-the-badge)

**Next-Generation Autonomous Academic Integrity, AI Content Analysis & Intellectual Contribution Graph (ICG) Verification Platform.**

[🇷🇺 Русский](#-русский-ru) • [🇬🇧 English](#-english-en) • [🇰🇿 Қазақша](#-қазақша-kk)

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

# 🇰🇿 Қазақша (KK)

## 🌟 Платформа туралы шолу
**UniPlag & ICG** — университеттерге, диссертациялық кеңестерге және ғылыми баспаларға арналған жаңа буынның академиялық сараптама платформасы. Жүйе заманауи білім берудегі басты мәселелерді шешеді: **жасанды интеллект мәтінін (LLM) анықтау** және **авторлық ғылыми үлессіз көшіріп алуды (компиляция) бағалау**.

### 🎯 4-Метрикалық сараптама үлгісі
1. **Мәтін түпнұсқалығы** (0–100%) — академиялық қорға қатысты авторлық мәтіннің жаңалығы.
2. **Алынған үзінділер мен сілтемелер** (0–100%) — бастапқы дереккөздерді нақты көрсету.
3. **ЖИ генерациясын анықтау (AI)** — нейрожелілер стилометриясын талдау.
4. **Зияткерлік үлес графигі (ICG v0.4)** — дереккөздерді синтездеу тереңдігін (DAG) және автордың дербес ғылыми қорытындыларын бағалау.

### 📜 512-биттік цифрлық мөрлі ресми PDF-анықтамалар
* Мемлекеттік аттестаттау комиссиясы (МАК), деканат және ғылыми кеңестер үшін А4 форматындағы ресми сертификаттар.
* **512-биттік цифрлық растау мөрі (SHA-512)** және `/verify/{seal}` арқылы онлайн тексеру.

### 🤖 Жергілікті Ollama контуры және модельдерді автожүктеу
* Терең нейрожелілік талдау үшін [**Ollama**](https://ollama.com) орнатылуы қажет.
* Алғашқы іске қосылғанда жүйе ең оңтайлы модельді (**`qwen2.5:1.5b`** / `llama3.2`) **автоматты түрде жүктеп алады**.

### 🚀 Жылдам іске қосу
```bash
# 1. Тәуелділіктерді орнату
pip install -r requirements.txt

# 2. Қорғалған BlackBox контейнерін іске қосу
run_blackbox.bat
# немесе: python run_blackbox.py --port 7932
```
* Браузерде ашу: **`http://localhost:7932`**

---

## 📁 Демонстрациялық файлдар / Sample Files / Демонстрациялық құжаттар

| Файл | Тіл / Language | Сипаттамасы / Description | Вердикт |
|---|---|---|:---:|
| [`samples/01_high_icg_original_research.docx`](samples/01_high_icg_original_research.docx) | 🇷🇺 RU | Научная ВКР с высоким ICG и авторским синтезом | 🟢 Рекомендовано |
| [`samples/02_ai_generated_essay.txt`](samples/02_ai_generated_essay.txt) | 🇷🇺 RU | Эссе со стилометрическими маркерами нейросети | 🔴 Детекция ИИ |
| [`samples/03_plagiarism_compilation_review.txt`](samples/03_plagiarism_compilation_review.txt) | 🇷🇺 RU | Реферативный обзор с заимствованиями | 🟡 Компиляция |
| [`samples/04_english_academic_paper.pdf`](samples/04_english_academic_paper.pdf) | 🇬🇧 EN | Research Paper for International Certificate | 🟢 Recommended |

---

## 🔒 Лицензия және құпиялылық / License & Confidentiality

All rights reserved. Proprietary analytical models, epistemic DAG logic, and cryptographic verification mechanisms are protected intellectual property.
