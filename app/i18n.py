"""
app/i18n.py — Lightweight Fast Multilingual Localization Module
==============================================================
Provides instant translation dictionaries for Russian (ru) and English (en)
with request-aware language resolution and Jinja2 global helpers.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from fastapi import Request

SUPPORTED_LANGUAGES = ("ru", "en")
DEFAULT_LANGUAGE = "ru"

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Brand & Navigation
    "brand_title": {
        "ru": "🛡️ UniPlag & ICG",
        "en": "🛡️ UniPlag & ICG",
    },
    "nav_my_works": {
        "ru": "📝 Мои работы",
        "en": "📝 My Works",
    },
    "nav_upload": {
        "ru": "📤 Сдать работу",
        "en": "📤 Submit Work",
    },
    "nav_all_checks": {
        "ru": "📊 Все проверки",
        "en": "📊 All Checks",
    },
    "nav_check_works": {
        "ru": "📄 Проверить работы",
        "en": "📄 Check Works",
    },
    "nav_corpus": {
        "ru": "📚 Корпус вуза",
        "en": "📚 Academic Corpus",
    },
    "nav_users": {
        "ru": "👥 Пользователи",
        "en": "👥 Users",
    },
    "nav_icg": {
        "ru": "🧠 ICG Контур",
        "en": "🧠 ICG Contour",
    },
    "nav_audit": {
        "ru": "🔒 512-bit Аудит",
        "en": "🔒 512-bit Audit",
    },
    "nav_guide": {
        "ru": "📖 Руководство",
        "en": "📖 User Guide",
    },
    "nav_logout": {
        "ru": "Выйти ➔",
        "en": "Log out ➔",
    },
    "role_admin": {
        "ru": "👑 Админ",
        "en": "👑 Admin",
    },
    "role_teacher": {
        "ru": "👨‍🏫 Преподаватель",
        "en": "👨‍🏫 Faculty",
    },
    "role_student": {
        "ru": "🎓 Студент",
        "en": "🎓 Student",
    },

    # Core Metrics
    "metric_originality": {
        "ru": "Оригинальность",
        "en": "Originality",
    },
    "metric_originality_sub": {
        "ru": "Текстовая новизна",
        "en": "Text novelty",
    },
    "metric_plagiarism": {
        "ru": "Заимствования",
        "en": "Plagiarism Matches",
    },
    "metric_plagiarism_sub": {
        "ru": "Совпадения с корпусом",
        "en": "Corpus matches",
    },
    "metric_ai": {
        "ru": "ИИ-генерация",
        "en": "AI Generation",
    },
    "metric_ai_sub": {
        "ru": "Вероятность нейросети",
        "en": "Neural net probability",
    },
    "metric_icg": {
        "ru": "Вклад ICG v0.4",
        "en": "ICG Contribution v0.4",
    },
    "metric_icg_sub": {
        "ru": "Синтез и логика (DAG)",
        "en": "Synthesis & logic (DAG)",
    },

    # Dashboard & Stats
    "stat_my_checks": {
        "ru": "сданных работ",
        "en": "submitted works",
    },
    "stat_avg_orig": {
        "ru": "средняя оригинальность",
        "en": "avg originality",
    },
    "stat_avg_icg": {
        "ru": "интеллект. вклад ICG",
        "en": "avg ICG score",
    },
    "stat_rank_place": {
        "ru": "место в рейтинге",
        "en": "leaderboard rank",
    },
    "stat_out_of": {
        "ru": "из",
        "en": "out of",
    },
    "tab_students": {
        "ru": "🏆 Рейтинг студентов",
        "en": "🏆 Student Leaderboard",
    },
    "tab_teachers": {
        "ru": "🎓 Рейтинг преподавателей",
        "en": "🎓 Faculty Leaderboard",
    },
    "tab_checks": {
        "ru": "📊 Все проверки",
        "en": "📊 All Checks",
    },

    # Report Page
    "report_title": {
        "ru": "Отчёт",
        "en": "Report",
    },
    "report_author": {
        "ru": "Автор",
        "en": "Author",
    },
    "report_words": {
        "ru": "Слов",
        "en": "Words",
    },
    "report_chars": {
        "ru": "Символов",
        "en": "Characters",
    },
    "report_checked_at": {
        "ru": "Проверен",
        "en": "Checked on",
    },
    "report_download_pdf_ru": {
        "ru": "📄 Скачать PDF (RU)",
        "en": "📄 Download PDF (RU)",
    },
    "report_download_pdf_en": {
        "ru": "📄 Скачать PDF (EN)",
        "en": "📄 Download PDF (EN)",
    },
    "report_verification_seal": {
        "ru": "🔒 Цифровая печать:",
        "en": "🔒 Verification Seal:",
    },
    "report_full_text": {
        "ru": "📄 Полный текст работы",
        "en": "📄 Full Document Text",
    },
    "report_legend_plag": {
        "ru": "красное — заимствование",
        "en": "red — matched fragment",
    },
    "report_legend_ai": {
        "ru": "жёлтое — вероятный ИИ-текст",
        "en": "yellow — probable AI text",
    },
    "report_copy_btn": {
        "ru": "📋 Копировать",
        "en": "📋 Copy",
    },
    "report_fullscreen_btn": {
        "ru": "🔍 На весь экран",
        "en": "🔍 Fullscreen",
    },
    "report_collapse_btn": {
        "ru": "✕ Свернуть",
        "en": "✕ Collapse",
    },

    # Upload Form
    "upload_title": {
        "ru": "📤 Сдать работу на проверку",
        "en": "📤 Submit Work for Examination",
    },
    "upload_drag_hint": {
        "ru": "Нажмите для выбора файлов или перетащите их сюда",
        "en": "Click to select files or drag & drop them here",
    },
    "upload_supported_formats": {
        "ru": "Поддерживаются форматы: DOCX, DOC, PDF, RTF, TXT, ODT (до 20 МБ)",
        "en": "Supported formats: DOCX, DOC, PDF, RTF, TXT, ODT (up to 20 MB)",
    },
    "upload_mode_legend": {
        "ru": "Режим академической экспертизы",
        "en": "Academic Examination Mode",
    },
    "upload_mode_full": {
        "ru": "🛡️ Полный анализ (Плагиат + Детекция ИИ + Граф ICG)",
        "en": "🛡️ Full Analysis (Plagiarism + AI Detection + ICG Graph)",
    },
    "upload_mode_plag": {
        "ru": "📄 Только поиск заимствований (Плагиат)",
        "en": "📄 Plagiarism search only",
    },
    "upload_mode_ai": {
        "ru": "🤖 Только детекция ИИ-текста (ChatGPT / нейросети)",
        "en": "🤖 AI text detection only (ChatGPT / LLMs)",
    },
    "upload_submit_btn": {
        "ru": "🚀 Начать проверку",
        "en": "🚀 Start Examination",
    },

    # Recommendations & ICG
    "recs_growth_vector": {
        "ru": "🎯 Главный вектор роста для усиления работы:",
        "en": "🎯 Key Growth Priority for Thesis Strengthening:",
    },
    "recs_checklist": {
        "ru": "📋 Пошаговый чек-лист доработки (для повышения ICG):",
        "en": "📋 Step-by-Step Actionable Checklist (to boost ICG):",
    },
    "recs_templates": {
        "ru": "💡 Готовые академические шаблоны для усиления синтеза:",
        "en": "💡 Academic Phrasing Templates for Synthesis Enhancement:",
    },
}


def get_language(request: Optional[Request] = None, lang_override: Optional[str] = None) -> str:
    """Resolves active language code from override, cookie, or query parameter."""
    if lang_override and lang_override.lower() in SUPPORTED_LANGUAGES:
        return lang_override.lower()

    if request:
        # Check query param
        q_lang = request.query_params.get("lang")
        if q_lang and q_lang.lower() in SUPPORTED_LANGUAGES:
            return q_lang.lower()

        # Check cookie
        c_lang = request.cookies.get("uniplag_lang")
        if c_lang and c_lang.lower() in SUPPORTED_LANGUAGES:
            return c_lang.lower()

        # Check header
        accept_lang = request.headers.get("accept-language", "")
        if "en" in accept_lang and "ru" not in accept_lang:
            return "en"

    return DEFAULT_LANGUAGE


def t(key: str, lang: Optional[str] = None, **kwargs: Any) -> str:
    """Translates a dictionary key into the specified or default language."""
    target_lang = (lang or DEFAULT_LANGUAGE).lower()
    if target_lang not in SUPPORTED_LANGUAGES:
        target_lang = DEFAULT_LANGUAGE

    entry = TRANSLATIONS.get(key)
    if not entry:
        return key

    text = entry.get(target_lang) or entry.get(DEFAULT_LANGUAGE) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
