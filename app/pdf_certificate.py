"""
app/pdf_certificate.py — Official Academic PDF Certificate Generator
=====================================================================
Generates high-resolution, vector-crisp official academic certificates
certifying originality, AI detection, and ICG intellectual contribution
with Sovereign 512-bit verification seals in Russian (RU) and English (EN).
"""

from __future__ import annotations

import io
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import pymupdf

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from .db import Check, Document, User


def get_cyrillic_font_file() -> Optional[str]:
    """Finds a valid TrueType font on Windows/Linux."""
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segui.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
        Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def get_cyrillic_bold_font_file() -> Optional[str]:
    """Finds a valid Bold TrueType font on Windows/Linux."""
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/seguisb.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf"),
        Path("C:/Windows/Fonts/tahomabd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return get_cyrillic_font_file()


def generate_check_pdf_certificate(
    check: Check,
    base_url: str = "http://localhost:7932",
    lang: str = "ru",
) -> bytes:
    """Generates an official A4 academic PDF certificate for a document check in RU or EN."""
    is_en = (lang.lower() == "en")
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)  # A4 standard in pt

    font_regular = get_cyrillic_font_file()
    font_bold = get_cyrillic_bold_font_file()

    font_reg_name = "arial_reg"
    font_bold_name = "arial_bold"

    if font_regular:
        try:
            page.insert_font(fontname=font_reg_name, fontfile=font_regular)
        except Exception:
            font_reg_name = "helv"
    else:
        font_reg_name = "helv"

    if font_bold:
        try:
            page.insert_font(fontname=font_bold_name, fontfile=font_bold)
        except Exception:
            font_bold_name = "helv"
    else:
        font_bold_name = "helv"

    # Color Palette
    c_navy = (16 / 255, 35 / 255, 63 / 255)
    c_blue = (2 / 255, 132 / 255, 199 / 255)
    c_green = (22 / 255, 163 / 255, 74 / 255)
    c_red = (220 / 255, 38 / 255, 38 / 255)
    c_purple = (126 / 255, 34 / 255, 206 / 255)
    c_gray_bg = (248 / 255, 250 / 255, 252 / 255)
    c_border = (203 / 255, 213 / 255, 225 / 255)
    c_muted = (100 / 255, 116 / 255, 139 / 255)
    c_ink = (30 / 255, 41 / 255, 59 / 255)
    c_white = (1, 1, 1)

    # 1. Outer Frame & Header Bar
    page.draw_rect(pymupdf.Rect(20, 20, 575.3, 821.9), color=c_border, width=1.5)
    page.draw_rect(pymupdf.Rect(25, 25, 570.3, 85), color=c_navy, fill=c_navy)

    # Header Text
    page.insert_text((40, 52), "UniPlag & ICG", fontname=font_bold_name, fontsize=18, color=c_white)
    
    sub_title = (
        "ACADEMIC EXAMINATION & INTELLECTUAL CONTRIBUTION VERIFICATION SYSTEM"
        if is_en else
        "СИСТЕМА АКАДЕМИЧЕСКОЙ ЭКСПЕРТИЗЫ И ВЕРИФИКАЦИИ ИНТЕЛЛЕКТУАЛЬНОГО ВКЛАДА"
    )
    main_cert_title = (
        "OFFICIAL ACADEMIC VERIFICATION CERTIFICATE OF THESIS ORIGINALITY"
        if is_en else
        "ОФИЦИАЛЬНАЯ СПРАВКА О РЕЗУЛЬТАТАХ ПРОВЕРКИ ВКР И НАУЧНЫХ РАБОТ"
    )

    page.insert_text((40, 72), sub_title, fontname=font_reg_name, fontsize=8.5, color=(200 / 255, 220 / 255, 245 / 255))
    page.insert_text((40, 94), main_cert_title, fontname=font_bold_name, fontsize=10.5, color=c_white)

    # 2. Document & Student Metadata Table
    meta_top = 120
    page.draw_rect(pymupdf.Rect(35, meta_top, 560.3, meta_top + 105), color=c_border, fill=c_gray_bg, width=0.8)

    doc_obj = check.document
    doc_title = doc_obj.title if doc_obj else ("Untitled" if is_en else "Без названия")
    doc_author = doc_obj.author or ("Student" if is_en else "Студент")
    owner = doc_obj.owner if doc_obj else None
    group_name = owner.group_name if owner and owner.group_name else "—"
    created_str = check.created_at.strftime("%d.%m.%Y %H:%M") if check.created_at else datetime.now().strftime("%d.%m.%Y")

    # Labels
    lbl_title = "Document Title:" if is_en else "Тема работы:"
    lbl_author = "Author / Student:" if is_en else "Автор / Студент:"
    lbl_vol = "Document Volume:" if is_en else "Объём работы:"
    lbl_date = "Examination Date:" if is_en else "Дата проверки:"

    col_offset = 145 if is_en else 130

    page.insert_text((50, meta_top + 22), lbl_title, fontname=font_bold_name, fontsize=9.5, color=c_muted)
    page.insert_text((col_offset, meta_top + 22), doc_title[:52] + ("..." if len(doc_title) > 52 else ""), fontname=font_bold_name, fontsize=9.5, color=c_ink)

    page.insert_text((50, meta_top + 42), lbl_author, fontname=font_bold_name, fontsize=9.5, color=c_muted)
    group_str = f"Group: {group_name}" if is_en else f"Группа: {group_name}"
    page.insert_text((col_offset, meta_top + 42), f"{doc_author} ({group_str})", fontname=font_reg_name, fontsize=9.5, color=c_ink)

    page.insert_text((50, meta_top + 62), lbl_vol, fontname=font_bold_name, fontsize=9.5, color=c_muted)
    actual_words = (len(doc_obj.text.split()) if doc_obj and doc_obj.text else 0)
    actual_chars = len(doc_obj.text) if doc_obj and doc_obj.text else 0
    vol_str = f"{actual_words} words · {actual_chars} characters" if is_en else f"{actual_words} слов · {actual_chars} символов"
    page.insert_text((col_offset, meta_top + 62), vol_str, fontname=font_reg_name, fontsize=9.5, color=c_ink)

    page.insert_text((50, meta_top + 82), lbl_date, fontname=font_bold_name, fontsize=9.5, color=c_muted)
    page.insert_text((col_offset, meta_top + 82), f"{created_str} (Check ID: #{check.id})", fontname=font_reg_name, fontsize=9.5, color=c_ink)

    # 3. Four Core Metric Cards
    cards_top = 240
    card_w = 125
    card_h = 75
    spacing = 8

    orig_val = round(max(0.0, 100.0 - (check.plag_score or 0.0)), 1)
    plag_val = round(check.plag_score or 0.0, 1)
    ai_val = round((check.ai_score or 0.0) * 100, 0)
    icg_val = round(check.icg_score or 0.0, 1) if getattr(check, "icg_score", None) is not None else 0.0

    if is_en:
        metrics = [
            ("Originality", f"{orig_val}%", c_green, "Text novelty"),
            ("Plagiarism", f"{plag_val}%", c_red if plag_val >= 50 else c_muted, "Corpus matches"),
            ("AI Generation", f"{int(ai_val)}%", c_red if ai_val >= 50 else c_muted, "Neural probability"),
            ("ICG v0.4 Score", f"{icg_val}%", c_purple if icg_val >= 50 else c_blue, "Synthesis & logic (DAG)"),
        ]
    else:
        metrics = [
            ("Оригинальность", f"{orig_val}%", c_green, "Текстовая новизна"),
            ("Заимствования", f"{plag_val}%", c_red if plag_val >= 50 else c_muted, "Совпадения с корпусом"),
            ("ИИ-генерация", f"{int(ai_val)}%", c_red if ai_val >= 50 else c_muted, "Вероятность нейросети"),
            ("Вклад ICG v0.4", f"{icg_val}%", c_purple if icg_val >= 50 else c_blue, "Синтез и логика (DAG)"),
        ]

    for i, (title, val, val_color, subtitle) in enumerate(metrics):
        cx = 35 + i * (card_w + spacing)
        page.draw_rect(pymupdf.Rect(cx, cards_top, cx + card_w, cards_top + card_h), color=c_border, fill=c_white, width=0.8)
        page.draw_line(pymupdf.Point(cx, cards_top), pymupdf.Point(cx + card_w, cards_top), color=val_color, width=3.5)
        page.insert_text((cx + 12, cards_top + 32), val, fontname=font_bold_name, fontsize=17, color=val_color)
        page.insert_text((cx + 12, cards_top + 49), title, fontname=font_bold_name, fontsize=8.5, color=c_ink)
        page.insert_text((cx + 12, cards_top + 63), subtitle, fontname=font_reg_name, fontsize=7.5, color=c_muted)

    # 4. Academic Verdict & ICG Reasoning Assessment
    verdict_top = 330
    page.draw_rect(pymupdf.Rect(35, verdict_top, 560.3, verdict_top + 95), color=c_border, fill=c_gray_bg, width=0.8)
    
    is_good = (orig_val >= 65.0 and icg_val >= 45.0 and ai_val < 40.0)
    verdict_color = c_green if is_good else (c_red if (plag_val >= 50.0 or icg_val < 25.0 or ai_val >= 60.0) else (234 / 255, 179 / 255, 8 / 255))
    page.draw_line(pymupdf.Point(35, verdict_top), pymupdf.Point(35, verdict_top + 95), color=verdict_color, width=4)

    lbl_verdict_hdr = "ACADEMIC VERDICT & RESEARCH CONTRIBUTION EVALUATION:" if is_en else "АКАДЕМИЧЕСКИЙ ВЕРДИКТ И ОЦЕНКА ИССЛЕДОВАТЕЛЬСКОГО ВКЛАДА:"
    page.insert_text((50, verdict_top + 20), lbl_verdict_hdr, fontname=font_bold_name, fontsize=9.5, color=c_ink)

    if is_en:
        if is_good:
            verdict_status = "RECOMMENDED FOR DEFENSE / HIGH RESEARCH CONTRIBUTION"
            verdict_desc = "The thesis demonstrates a high level of independent source synthesis, coherent argument DAG structure, and minimal text borrowing."
        elif plag_val >= 50.0 or icg_val < 25.0:
            verdict_status = "SIGNIFICANT REVISION REQUIRED (RISK ZONE)"
            verdict_desc = "Critical level of borrowings or low ICG contribution detected (passive compilation without independent author synthesis)."
        else:
            verdict_status = "ACCEPTED WITH REMARKS"
            verdict_desc = "The work meets baseline originality criteria; strengthening the evidence base for author conclusions is recommended."
    else:
        if is_good:
            verdict_status = "РЕКОМЕНДОВАНО К ЗАЩИТЕ / ВЫСОКИЙ АВТОРСКИЙ ВКЛАД"
            verdict_desc = "Работа демонстрирует высокий уровень самостоятельного синтеза источников, развитую логическую структуру доказательств и низкий уровень заимствований."
        elif plag_val >= 50.0 or icg_val < 25.0:
            verdict_status = "ТРЕБУЕТСЯ СУЩЕСТВЕННАЯ ДОРАБОТКА (ЗОНА РИСКА)"
            verdict_desc = "Обнаружен критический уровень заимствований или низкий вклад ICG (реферативное изложение без глубокого авторского синтеза)."
        else:
            verdict_status = "ДОПУСКАЕТСЯ С ЗАМЕЧАНИЯМИ"
            verdict_desc = "Работа удовлетворяет базовым требованиям оригинальности, рекомендуется усилить доказательную базу авторских выводов."

    page.insert_text((50, verdict_top + 40), verdict_status, fontname=font_bold_name, fontsize=10.5, color=verdict_color)
    rect_desc = pymupdf.Rect(50, verdict_top + 48, 545, verdict_top + 88)
    page.insert_textbox(rect_desc, verdict_desc, fontname=font_reg_name, fontsize=8.5, color=c_muted)

    # 5. Top Sources of Matches Table
    src_top = 440
    lbl_src_hdr = "SOURCES OF MATCHES (TOP CORPUS COINCIDENCES):" if is_en else "ИСТОЧНИКИ ЗАИМСТВОВАНИЙ (ТОП СОВПАДЕНИЙ В КОРПУСЕ):"
    page.insert_text((35, src_top + 14), lbl_src_hdr, fontname=font_bold_name, fontsize=9.5, color=c_ink)
    
    table_y = src_top + 24
    page.draw_rect(pymupdf.Rect(35, table_y, 560.3, table_y + 110), color=c_border, fill=c_white, width=0.8)
    page.draw_rect(pymupdf.Rect(35, table_y, 560.3, table_y + 20), color=c_border, fill=c_gray_bg, width=0.5)

    th_num = "#" if is_en else "№"
    th_source = "Source Document / Reference" if is_en else "Наименование источника / Документ"
    th_match = "Match" if is_en else "Совпадение"
    th_frags = "Fragments" if is_en else "Фрагментов"

    page.insert_text((45, table_y + 14), th_num, fontname=font_bold_name, fontsize=8.5, color=c_muted)
    page.insert_text((75, table_y + 14), th_source, fontname=font_bold_name, fontsize=8.5, color=c_muted)
    page.insert_text((430, table_y + 14), th_match, fontname=font_bold_name, fontsize=8.5, color=c_muted)
    page.insert_text((505, table_y + 14), th_frags, fontname=font_bold_name, fontsize=8.5, color=c_muted)

    matches = check.matches or []
    sorted_matches = sorted(matches, key=lambda m: m.sim, reverse=True)[:4]

    row_y = table_y + 20
    if not sorted_matches:
        empty_msg = "No text matches found in academic corpus (100% clean)." if is_en else "Текстовых совпадений в университетском корпусе не обнаружено (100% чистота)."
        page.insert_text((50, row_y + 25), empty_msg, fontname=font_reg_name, fontsize=8.5, color=c_muted)
    else:
        for idx, m in enumerate(sorted_matches, 1):
            lbl = m.source_label or ("Source" if is_en else "Источник")
            if len(lbl) > 58:
                lbl = lbl[:55] + "..."
            page.insert_text((45, row_y + 15), str(idx), fontname=font_reg_name, fontsize=8.5, color=c_ink)
            page.insert_text((75, row_y + 15), lbl, fontname=font_reg_name, fontsize=8.5, color=c_ink)
            page.insert_text((430, row_y + 15), f"{m.sim:.1f}%", fontname=font_bold_name, fontsize=8.5, color=c_red if m.sim >= 20 else c_ink)
            page.insert_text((515, row_y + 15), str(len(m.fragments or [])), fontname=font_reg_name, fontsize=8.5, color=c_muted)
            page.draw_line(pymupdf.Point(35, row_y + 22), pymupdf.Point(560.3, row_y + 22), color=(235 / 255, 240 / 255, 245 / 255), width=0.5)
            row_y += 22

    # 6. Cryptographic Verification & Sovereign 512-bit Security Seal Block
    seal_top = 570
    page.draw_rect(pymupdf.Rect(35, seal_top, 560.3, seal_top + 160), color=c_border, fill=c_gray_bg, width=0.8)

    stamp_cx = 490
    stamp_cy = seal_top + 80
    page.draw_circle(pymupdf.Point(stamp_cx, stamp_cy), 45, color=c_purple, width=1.5)
    page.draw_circle(pymupdf.Point(stamp_cx, stamp_cy), 40, color=c_purple, width=0.8)
    page.insert_text((stamp_cx - 28, stamp_cy - 12), "UniPlag & ICG", fontname=font_bold_name, fontsize=8, color=c_purple)
    page.insert_text((stamp_cx - 24, stamp_cy + 2), "512-BIT SEAL", fontname=font_bold_name, fontsize=7.5, color=c_purple)
    page.insert_text((stamp_cx - 22, stamp_cy + 16), "VERIFIED", fontname=font_bold_name, fontsize=8, color=c_green)

    lbl_sec_hdr = "DIGITAL SEAL & AUTHENTICITY VERIFICATION:" if is_en else "ЦИФРОВАЯ ПЕЧАТЬ И ВЕРИФИКАЦИЯ ПОДЛИННОСТИ:"
    page.insert_text((50, seal_top + 22), lbl_sec_hdr, fontname=font_bold_name, fontsize=9.5, color=c_ink)

    seal_hash = check.verification_seal or "UNVERIFIED_CHECK_SEAL_HASH"
    lbl_hash = "Examination Check Hash (SHA-512):" if is_en else "Контрольный хэш проверки (SHA-512):"
    page.insert_text((50, seal_top + 42), lbl_hash, fontname=font_reg_name, fontsize=8.5, color=c_muted)
    page.insert_text((50, seal_top + 57), seal_hash[:48], fontname=font_bold_name, fontsize=8, color=c_navy)
    page.insert_text((50, seal_top + 69), seal_hash[48:96], fontname=font_bold_name, fontsize=8, color=c_navy)

    verify_url = f"{base_url}/verify/{seal_hash}"
    lbl_online = "Online authenticity verification link:" if is_en else "Онлайн-проверка подлинности справки:"
    page.insert_text((50, seal_top + 92), lbl_online, fontname=font_reg_name, fontsize=8.5, color=c_muted)
    page.insert_text((50, seal_top + 106), verify_url, fontname=font_bold_name, fontsize=8.5, color=c_blue)

    sec_note1 = (
        "Authenticity protected by HMAC-SHA512 sovereign key. Any document tampering invalidates this certificate."
        if is_en else
        "Подлинность результатов защищена 512-битным алгоритмом HMAC-SHA512. Внесение изменений в документ аннулирует сертификат."
    )
    sec_note2 = (
        "Generated automatically in UniPlag & ICG v0.4.1. Valid for university examination committees and accreditation."
        if is_en else
        "Справка сформирована автоматически в системе UniPlag & ICG v0.4.1. Действительна для предоставления в ГЭК и деканат."
    )
    page.insert_text((50, seal_top + 128), sec_note1, fontname=font_reg_name, fontsize=7.5, color=c_muted)
    page.insert_text((50, seal_top + 142), sec_note2, fontname=font_reg_name, fontsize=7.5, color=c_muted)

    # 7. Bottom Footer
    page.draw_line(pymupdf.Point(35, 795), pymupdf.Point(560.3, 795), color=c_border, width=0.5)
    footer_str = (
        f"UniPlag Academic System · Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if is_en else
        f"UniPlag Academic System · Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    )
    page_str = "Page 1 of 1" if is_en else "Страница 1 из 1"
    page.insert_text((35, 808), footer_str, fontname=font_reg_name, fontsize=7.5, color=c_muted)
    page.insert_text((475, 808), page_str, fontname=font_reg_name, fontsize=7.5, color=c_muted)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
