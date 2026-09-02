import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable

from .ai_detector import detect as ai_detect
from .db import Check, Document, Fragment, Match
from .fingerprint import fingerprint
from .plagiarism import align_fragments, corpus_index, ensure_index
from .quality import assess as quality_assess

# Aris Directive (ICG integration): the ICG watchdog (52 benchmark cases) is HEAVY
# CPU-bound work. It must NEVER start in the moment of a user check — with the GIL it
# would compete with the running check for the CPU (both crawl). Instead, a planner
# thread runs the watchdog only when: (a) the schedule is due (6h OR 500 checks) AND
# (b) no check is currently in flight.
_active_checks = 0
_active_checks_lock = threading.Lock()
_watchdog_lock = threading.Lock()
_watchdog_running = False

# Aris Directive (v0.4.1, REFAC): bounded pool instead of a raw thread per upload.
# max_workers = cpu_count * 2: часть тредов ждёт IO (Ollama quality/ICG deep),
# часть крутит CPU-работу (MinHash, выравнивание, NLI fast-контур).
_check_executor = ThreadPoolExecutor(
    max_workers=max(2, (os.cpu_count() or 2) * 2),
    thread_name_prefix="uniplag-check",
)
# Тяжёлый ICG (большие тексты / deep-перепроверка) живёт в отдельном пуле:
# N-ка медленных ICG не должна выедать всех воркеров пула проверок.
_icg_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="uniplag-icg")
_check_futures: dict[int, Future] = {}
_check_futures_lock = threading.Lock()


def _enter_check():
    global _active_checks
    with _active_checks_lock:
        _active_checks += 1


def _exit_check():
    global _active_checks
    with _active_checks_lock:
        _active_checks = max(0, _active_checks - 1)


def active_checks() -> int:
    with _active_checks_lock:
        return _active_checks


def watchdog_busy() -> bool:
    return _watchdog_running


def submit_background_check(check_id: int, do_plag: bool, do_ai: bool, do_quality: bool) -> Future:
    """Schedule a check in the bounded pool (Aris Directive v0.4.1, TASK_1)."""
    with _check_futures_lock:
        _check_futures.pop(check_id, None)
    fut = _check_executor.submit(check_document_background, check_id, do_plag, do_ai, do_quality)
    with _check_futures_lock:
        _check_futures[check_id] = fut
    return fut


def pending_check_task(check_id: int) -> bool:
    with _check_futures_lock:
        fut = _check_futures.get(check_id)
    return fut is not None and not fut.done()


def submit_heavy_icg(fn: Callable[..., None]) -> Future:
    """TASK_1: heavy ICG work (deep re-check, big-text fast contour) to a dedicated pool."""
    return _icg_executor.submit(fn)


def _run_watchdog():
    global _watchdog_running
    if not _watchdog_lock.acquire(blocking=False):
        return
    if _watchdog_running:
        _watchdog_lock.release()
        return
    _watchdog_running = True
    _watchdog_lock.release()

    try:
        from .icg.icg_watchdog import run_watchdog_once
        from .db import SessionLocal
        with SessionLocal() as db2:
            run_watchdog_once(db2)
    except Exception:
        pass
    finally:
        _watchdog_running = False


def start_watchdog_planner(interval: float = 60.0) -> threading.Thread:
    """Single daemon thread that runs the watchdog on schedule + idle time only."""
    def _loop():
        while True:
            try:
                if not _watchdog_running and active_checks() == 0:
                    from .icg.icg_watchdog import should_run_watchdog, last_health
                    from .db import SessionLocal
                    from .db import Check as _Chk
                    from sqlalchemy import func as _func
                    with SessionLocal() as _db:
                        h = last_health(_db)
                        checks_since = 0
                        if h is not None and h.ts is not None:
                            checks_since = _db.query(_func.count(_Chk.id)).filter(
                                _Chk.created_at > h.ts).scalar() or 0
                        due = h is None or should_run_watchdog(_db, checks_since)
                    if due:
                        _run_watchdog()
            except Exception:
                pass
            finally:
                threading.Event().wait(interval)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t


def run_check(db, doc: Document, do_plag: bool = True, do_ai: bool = True,
              do_quality: bool = False) -> Check:
    _enter_check()
    try:
        return _run_check_inner(db, doc, do_plag, do_ai, do_quality)
    finally:
        _exit_check()


def _run_check_inner(db, doc: Document, do_plag: bool = True, do_ai: bool = True,
                     do_quality: bool = False, progress_cb=None, check: Check | None = None) -> Check:
    def _stage(progress, msg):
        if progress_cb:
            try:
                progress_cb(progress, msg)
            except Exception:
                pass

    ensure_index(db)
    fp = fingerprint(doc.text)

    if check is None:
        check = Check(document_id=doc.id)
        db.add(check)
        db.flush()
    _stage(5, "Загрузка работы")

    if do_plag:
        cands = corpus_index.candidates(fp, exclude=doc.id)
        total_matched_chars = 0
        for idx, (cand_id, est_sim) in enumerate(cands):
            cand = db.get(Document, cand_id)
            percent, spans = align_fragments(doc.text, cand.text)
            if percent < 0.5 or not spans:
                continue
            m = Match(
                check=check,
                source_doc_id=cand.id,
                source_label=cand.title,
                sim=percent,
                matched_words=int(round(len(fp["hashes"]) * percent / 100)) + config_shingle_k(),
            )
            for s, e in spans:
                total_matched_chars += e - s
                m.fragments.append(Fragment(q_start=s, q_end=e, text=doc.text[s:e][:500]))
            db.add(m)
            _stage(10 + int(20 * (idx + 1) / max(1, len(cands))), "Поиск заимствований")
        chars = max(len(doc.text), 1)
        from .plagiarism import merge_spans
        all_spans = [(fr.q_start, fr.q_end) for match in check.matches for fr in match.fragments]
        union = sum(e - s for s, e in merge_spans(all_spans))
        check.plag_score = round(min(100.0 * union / chars, 99.9), 2)
    _stage(30, "Заимствования готовы")

    if do_ai:
        _stage(32, "Анализ ИИ-текста")
        result = ai_detect(doc.text)
        check.ai_score = max(result.get("score", 0.0), 0.0)
        check.ai_method = result.get("method", "")
        check.ai_json = json.dumps(result, ensure_ascii=False)
    _stage(55, "ИИ-текст готов")

    if do_quality:
        _stage(57, "Оценка качества")
        qr = quality_assess(doc.text)
        check.quality_json = json.dumps(qr, ensure_ascii=False)
    _stage(70, "Качество готово")

    # Intellectual Contribution Graph (ICG) Analysis — Aris Directive: via integration layer (FAST contour).
    _stage(72, "Построение графа интеллектуального вклада")

    def _run_icg_fast():
        from .icg.integration import check_icg_fast
        from .icg.icg_watchdog import current_degraded
        icg_score, _icg_summary, icg_payload = check_icg_fast(str(doc.id), doc.text)
        if current_degraded(db):
            _obj = json.loads(icg_payload)
            _obj["degraded"] = True
            _obj["disclaimer"] = "Внимание: точность ICG временно снижена (регрессия v0.4)."
            icg_payload = json.dumps(_obj, ensure_ascii=False)
        return icg_score, icg_payload

    try:
        # Aris Directive (v0.4.1, TASK_1): на больших текстах dead-контур ICG уходит
        # в отдельный пул, чтобы не выедать воркеры пула проверок.
        if len(doc.text.split()) >= config_large_icg_words():
            _fut = _icg_executor.submit(_run_icg_fast)
            icg_score, icg_payload = _fut.result()
        else:
            icg_score, icg_payload = _run_icg_fast()
        check.icg_score = icg_score
        check.icg_json = icg_payload
    except Exception as e:
        check.icg_score = 0.0
        check.icg_json = json.dumps({"error": str(e)}, ensure_ascii=False)
    _stage(95, "ICG готов")

    # Anti-Tamper & Cryptographic Report Digital Sealing
    try:
        from .integrity import generate_report_seal, verify_code_integrity
        integrity_status = verify_code_integrity()
        if not integrity_status.is_valid:
            # Embed tamper disclaimer into check payload
            _obj = json.loads(check.icg_json or "{}")
            _obj["tamper_detected"] = True
            _obj["disclaimer"] = "ВНИМАНИЕ: Нарушена целостность ядра системы! Отчёт не может быть официально заверен."
            check.icg_json = json.dumps(_obj, ensure_ascii=False)

        seal = generate_report_seal(
            check_id=check.id,
            doc_title=doc.title,
            doc_text=doc.text,
            plag_score=check.plag_score,
            ai_score=check.ai_score,
            icg_score=check.icg_score,
            created_at_iso=check.created_at.isoformat() if check.created_at else datetime.utcnow().isoformat(),
        )
        check.verification_seal = seal
    except Exception as e:
        print(f"Warning: Failed to seal report: {e}")

    check.status = "done"
    check.progress = 100
    check.status_msg = "Проверка завершена"
    _stage(100, "Готово")

    db.commit()
    db.refresh(check)
    return check


def _apply_progress(db, check_id: int, progress: int, msg: str) -> None:
    c = db.get(Check, check_id)
    if c is not None:
        # Do not clobber a terminal status (done/error) with "running".
        if c.status not in ("done", "error"):
            c.status = "running"
        c.progress = progress
        c.status_msg = msg
        db.commit()


def check_document_background(check_id: int, do_plag: bool, do_ai: bool, do_quality: bool) -> None:
    """Run the full check for an already-created Check row in a background thread.

    Owns its own session; updates Check.status/progress between stages.
    This is the entry point for the async (upload-separated) flow.
    """
    _enter_check()
    try:
        from .db import SessionLocal
        with SessionLocal() as db:
            check = db.get(Check, check_id)
            if check is None:
                return
            doc = db.get(Document, check.document_id)
            if doc is None:
                check.status = "error"
                check.status_msg = "Документ не найден"
                db.commit()
                return
            check.status = "running"
            check.progress = 1
            check.status_msg = "Проверка начата"
            db.commit()
            _run_check_inner(
                db, doc,
                do_plag=do_plag, do_ai=do_ai, do_quality=do_quality,
                progress_cb=lambda p, m: _apply_progress(db, check_id, p, m),
                check=check,
            )
    except Exception as e:
        try:
            from .db import SessionLocal
            with SessionLocal() as db:
                c = db.get(Check, check_id)
                if c is not None:
                    c.status = "error"
                    c.progress = 0
                    c.status_msg = f"Ошибка: {e}"
                    db.commit()
        except Exception:
            pass
    finally:
        _exit_check()


def config_shingle_k() -> int:
    from . import config
    return config.SHINGLE_K


def config_large_icg_words() -> int:
    from . import config
    return getattr(config, "ICG_LARGE_WORDS", 5000)
