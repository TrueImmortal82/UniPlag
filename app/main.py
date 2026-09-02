import json
import secrets
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import config
from .auth import current_user, create_session, get_db, require_admin, require_teacher_or_admin
from .crawler import fetch_url
from .db import Check, Document, SessionLocal, User, init_db
from .fingerprint import fingerprint
from .parsing import extract_text
from .plagiarism import corpus_index
from .i18n import t, get_language
from .blackbox.loader import get_current_mount
import mimetypes
import jinja2

_mount = get_current_mount()
if _mount is not None:
    def _bbx_template_loader(name: str):
        normalized = name.replace("\\", "/").lstrip("/")
        raw = (
            _mount.get_resource_bytes(f"app/templates/{normalized}") or
            _mount.get_resource_bytes(f"templates/{normalized}") or
            _mount.get_resource_bytes(normalized)
        )
        if raw is not None:
            return raw.decode("utf-8", errors="replace"), None, lambda: True
        raise jinja2.TemplateNotFound(name)

    _jinja_env = jinja2.Environment(loader=jinja2.FunctionLoader(_bbx_template_loader), autoescape=True)
    templates = Jinja2Templates(env=_jinja_env)
else:
    BASE = Path(__file__).resolve().parent
    tmpl_dir = BASE / "templates"
    if not tmpl_dir.exists():
        tmpl_dir = Path(__file__).resolve().parent.parent / "app" / "templates"
    templates = Jinja2Templates(directory=str(tmpl_dir))

templates.env.globals["t"] = t
templates.env.globals["get_language"] = get_language


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    # Aris Directive (v0.4.1, STABILITY): подчистить зависшие проверки от прошлых сессий.
    try:
        from .db import recover_orphaned_checks
        n = recover_orphaned_checks(lifetime_minutes=30.0)
        if n:
            print(f"Recovered {n} orphaned checks -> error (server restart).")
    except Exception as e:
        print(f"recover_orphaned_checks failed: {e}")
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as db:
        if not db.query(User).count():
            admin = User(username="admin", role="admin")
            admin.set_password("admin123")
            db.add(admin)
            db.commit()
            print("Создан администратор по умолчанию: admin / admin123 (смените пароль!)")
    
    # Ollama Local Neural Engine Status & Auto-Preparation
    try:
        from .ai_detector import get_ollama_status, get_ollama_model
        ollama_stat = get_ollama_status()
        if ollama_stat["available"]:
            if ollama_stat["active_model"]:
                print(f"🤖 [AI Detector] Ollama активна. Используется модель: {ollama_stat['active_model']}")
            else:
                print("🤖 [AI Detector] Ollama активна. Подгружаем оптимальную модель...")
                get_ollama_model()
        else:
            print("ℹ️  [AI Detector] Для глубокого нейросетевого анализа требуется Ollama (https://ollama.com). Активен локальный ML-ансамбль.")
    except Exception as e:
        print(f"Ollama check notice: {e}")

    # Anti-Tamper: Boot-time code integrity check
    try:
        from .integrity import verify_code_integrity
        integrity = verify_code_integrity()
        if integrity.is_valid:
            print("🛡 Code Integrity: SEALED & VALID (HMAC-SHA256 verified)")
        else:
            print(f"⚠️ Code Integrity ALERT: {integrity.details}")
    except Exception as e:
        print(f"Integrity verification error: {e}")

    # Aris Directive: start the ICG watchdog planner (idle-only + schedule). Non-blocking daemon.
    try:
        from .checker import start_watchdog_planner
        start_watchdog_planner(interval=60.0)
        print("ICG watchdog planner started (idle-only, every 6h or 500 checks).")
    except Exception as e:
        print(f"Watchdog planner failed to start: {e}")
    yield


app = FastAPI(title="UniPlag", lifespan=lifespan)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": ""})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username.strip()).first()
    if not user or not user.check_password(password):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Неверный логин или пароль"}, status_code=401
        )
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie("uniplag_session", create_session(user.id), httponly=True)
    return resp


@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("uniplag_session")
    return resp


def compute_student_ratings(
    db: Session,
    group_filter: Optional[str] = None,
    teacher_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_teacher_id: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, int]]:
    """Groups works by student (Student ID / Owner ID and Registered Student accounts),
    computes average originality, AI probability, and ICG intellectual contribution,
    diagnoses performance (performing vs struggling/at-risk), and provides filtering."""
    
    # Extract distinct groups
    groups_query = db.query(User.group_name).filter(User.role == "student", User.group_name != "").distinct()
    available_groups = sorted([g[0] for g in groups_query.all() if g[0]])

    students_query = db.query(User).filter(User.role == "student")
    if group_filter and group_filter.strip():
        students_query = students_query.filter(User.group_name == group_filter.strip())
    if teacher_id:
        students_query = students_query.filter(User.teacher_id == teacher_id)
    
    students = students_query.order_by(User.full_name, User.username).all()
    
    all_ratings: List[Dict[str, Any]] = []
    
    for s in students:
        docs = db.query(Document).filter(Document.owner_id == s.id).all()
        doc_ids = [d.id for d in docs]
        
        checks = (
            db.query(Check)
            .filter(Check.document_id.in_(doc_ids), Check.status == "done")
            .order_by(Check.created_at.desc())
            .all() if doc_ids else []
        )
        
        works_count = len(checks)
        if works_count > 0:
            avg_plag = sum(c.plag_score for c in checks) / works_count
            avg_orig = max(0.0, 100.0 - avg_plag)
            avg_ai = (sum(c.ai_score for c in checks) / works_count) * 100.0
            avg_icg = sum(c.icg_score for c in checks) / works_count
        else:
            avg_plag = 0.0
            avg_orig = 0.0
            avg_ai = 0.0
            avg_icg = 0.0

        # Composite Academic Rating: 40% Originality + 40% ICG + 20% Human (100 - AI)
        composite_score = round(0.4 * avg_orig + 0.4 * avg_icg + 0.2 * max(0.0, 100.0 - avg_ai), 1) if works_count > 0 else 0.0

        # Diagnostic Performance & Risk Analysis
        risk_reasons: List[str] = []
        success_highlights: List[str] = []

        if works_count == 0:
            risk_reasons.append("0 сданных работ к сроку")
        if works_count > 0 and avg_icg < 25.0:
            risk_reasons.append(f"Критически низкий ICG вклад ({round(avg_icg)}% — реферативность)")
        if works_count > 0 and avg_orig < 40.0:
            risk_reasons.append(f"Критический плагиат ({round(avg_plag)}% заимствований)")
        if works_count > 0 and avg_ai >= 60.0:
            risk_reasons.append(f"Высокий риск ИИ-генерации ({round(avg_ai)}%)")

        if works_count > 0 and avg_icg >= 45.0:
            success_highlights.append(f"Глубокий синтез и выводы (ICG {round(avg_icg)}%)")
        if works_count > 0 and avg_orig >= 75.0:
            success_highlights.append(f"Высокая оригинальность ({round(avg_orig)}%)")
        if works_count > 0 and avg_ai < 20.0:
            success_highlights.append("Самостоятельное авторское написание")

        if risk_reasons:
            performance_status = "at_risk"
            status_label = "В зоне риска"
            status_badge_class = "bad"
        elif works_count > 0 and avg_icg >= 45.0 and avg_orig >= 65.0 and avg_ai < 40.0:
            performance_status = "performing"
            status_label = "Успевает"
            status_badge_class = "ok"
        else:
            performance_status = "attention"
            status_label = "Требует внимания"
            status_badge_class = "warn"

        if composite_score >= 75:
            tier = "Лидер (Высший вклад)"
            tier_class = "ok"
        elif composite_score >= 50:
            tier = "Хороший уровень"
            tier_class = "ok"
        elif composite_score >= 30:
            tier = "Требует внимания"
            tier_class = "warn"
        else:
            tier = "В зоне риска" if works_count > 0 else "Нет сданных работ"
            tier_class = "bad" if works_count > 0 else "muted"

        teacher_user = db.get(User, s.teacher_id) if s.teacher_id else None
        is_assigned = (s.teacher_id == current_teacher_id) if current_teacher_id else False

        all_ratings.append({
            "student_id": s.id,
            "username": s.username,
            "full_name": s.full_name or s.username,
            "group_name": s.group_name or "—",
            "teacher_id": s.teacher_id,
            "teacher_name": teacher_user.full_name or teacher_user.username if teacher_user else "Не назначен",
            "is_assigned": is_assigned,
            "works_count": works_count,
            "avg_orig": round(avg_orig, 1),
            "avg_plag": round(avg_plag, 1),
            "avg_ai": round(avg_ai, 1),
            "avg_icg": round(avg_icg, 1),
            "rating_score": composite_score,
            "tier": tier,
            "tier_class": tier_class,
            "performance_status": performance_status,
            "status_label": status_label,
            "status_badge_class": status_badge_class,
            "risk_reasons": risk_reasons,
            "success_highlights": success_highlights,
            "recent_works": [
                {
                    "id": c.id,
                    "title": c.document.title,
                    "orig": round(100 - c.plag_score, 1),
                    "icg": round(c.icg_score, 1),
                    "date": c.created_at.strftime("%d.%m.%Y") if c.created_at else "",
                }
                for c in checks[:3]
            ],
        })

    # Sort descending by rating_score, then works_count
    all_ratings.sort(key=lambda x: (x["rating_score"], x["works_count"]), reverse=True)
    
    # Assign ranks
    for rank, item in enumerate(all_ratings, 1):
        item["rank"] = rank

    # Performance Counters
    perf_counts = {
        "total": len(all_ratings),
        "performing": sum(1 for r in all_ratings if r["performance_status"] == "performing"),
        "at_risk": sum(1 for r in all_ratings if r["performance_status"] == "at_risk"),
        "attention": sum(1 for r in all_ratings if r["performance_status"] == "attention"),
        "my_students": sum(1 for r in all_ratings if r["is_assigned"]),
    }

    # Apply Status Filtering if requested
    filtered_ratings = all_ratings
    if status_filter == "performing":
        filtered_ratings = [r for r in all_ratings if r["performance_status"] == "performing"]
    elif status_filter == "at_risk":
        filtered_ratings = [r for r in all_ratings if r["performance_status"] == "at_risk"]
    elif status_filter == "attention":
        filtered_ratings = [r for r in all_ratings if r["performance_status"] == "attention"]
    elif status_filter == "my_students":
        filtered_ratings = [r for r in all_ratings if r["is_assigned"]]

    return filtered_ratings, available_groups, perf_counts


def compute_teacher_ratings(db: Session) -> List[Dict[str, Any]]:
    """Computes faculty/teacher ratings based on their supervised students' academic performance,
    ICG intellectual contribution, originality, and success rates."""
    teachers = db.query(User).filter(User.role.in_(("teacher", "admin"))).order_by(User.full_name, User.username).all()
    teacher_ratings: List[Dict[str, Any]] = []

    # Get all student ratings first
    all_students_ratings, _, _ = compute_student_ratings(db)

    for t in teachers:
        # Find students assigned to this teacher
        my_students = [s for s in all_students_ratings if s.get("teacher_id") == t.id]
        
        assigned_count = len(my_students)
        if assigned_count > 0:
            total_works = sum(s["works_count"] for s in my_students)
            performing_count = sum(1 for s in my_students if s["performance_status"] == "performing")
            at_risk_count = sum(1 for s in my_students if s["performance_status"] == "at_risk")
            attention_count = sum(1 for s in my_students if s["performance_status"] == "attention")
            
            # Average metrics of students with works
            students_with_works = [s for s in my_students if s["works_count"] > 0]
            if students_with_works:
                avg_student_icg = sum(s["avg_icg"] for s in students_with_works) / len(students_with_works)
                avg_student_orig = sum(s["avg_orig"] for s in students_with_works) / len(students_with_works)
                avg_student_ai = sum(s["avg_ai"] for s in students_with_works) / len(students_with_works)
            else:
                avg_student_icg = 0.0
                avg_student_orig = 0.0
                avg_student_ai = 0.0

            success_rate = (performing_count / assigned_count) * 100.0
            
            # Composite Teacher Pedagogical Score (0-100):
            # 40% Students ICG + 30% Students Originality + 30% Success Rate
            teacher_score = round(
                0.40 * avg_student_icg + 0.30 * avg_student_orig + 0.30 * success_rate,
                1
            )
        else:
            total_works = 0
            performing_count = 0
            at_risk_count = 0
            attention_count = 0
            avg_student_icg = 0.0
            avg_student_orig = 0.0
            avg_student_ai = 0.0
            success_rate = 0.0
            teacher_score = 0.0

        if teacher_score >= 70.0:
            tier = "Кафедральный лидер (Высшая эффективность)"
            tier_class = "ok"
        elif teacher_score >= 50.0:
            tier = "Эффективный руководитель"
            tier_class = "ok"
        elif teacher_score >= 30.0:
            tier = "Удовлетворительный уровень"
            tier_class = "warn"
        else:
            tier = "Требует внимания кафедры" if assigned_count > 0 else "Нет прикреплённых студентов"
            tier_class = "bad" if assigned_count > 0 else "muted"

        top_students = sorted(
            [s for s in my_students if s["works_count"] > 0],
            key=lambda x: x["rating_score"],
            reverse=True
        )[:3]

        teacher_ratings.append({
            "teacher_id": t.id,
            "username": t.username,
            "full_name": t.full_name or t.username,
            "role": t.role,
            "assigned_count": assigned_count,
            "total_works": total_works,
            "performing_count": performing_count,
            "at_risk_count": at_risk_count,
            "attention_count": attention_count,
            "success_rate": round(success_rate, 1),
            "avg_student_icg": round(avg_student_icg, 1),
            "avg_student_orig": round(avg_student_orig, 1),
            "avg_student_ai": round(avg_student_ai, 1),
            "teacher_score": teacher_score,
            "tier": tier,
            "tier_class": tier_class,
            "top_students": top_students,
        })

    # Sort descending by teacher_score, then assigned_count
    teacher_ratings.sort(key=lambda x: (x["teacher_score"], x["assigned_count"]), reverse=True)
    
    for rank, item in enumerate(teacher_ratings, 1):
        item["rank"] = rank

    return teacher_ratings


@app.get("/guide", response_class=HTMLResponse)
def guide_page(request: Request, user: User = Depends(current_user)):
    return templates.TemplateResponse(request, "guide.html", {"user": user})


@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    group: Optional[str] = None,
    status: Optional[str] = None,
    tab: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    is_student = (getattr(user, "role", "student") == "student")
    current_teacher_id = user.id if getattr(user, "role", "student") in ("teacher", "admin") else None
    
    student_ratings, available_groups, perf_counts = compute_student_ratings(
        db,
        group_filter=group,
        status_filter=status,
        current_teacher_id=current_teacher_id,
    )
    
    teacher_ratings = compute_teacher_ratings(db) if not is_student else []
    
    if is_student:
        # Student sees only their own checks and their personal rating
        checks = (
            db.query(Check)
            .join(Document, Check.document_id == Document.id)
            .filter(Document.owner_id == user.id)
            .order_by(Check.created_at.desc())
            .limit(50)
            .all()
        )
        avg_icg_val = (
            db.query(func.avg(Check.icg_score))
            .join(Document, Check.document_id == Document.id)
            .filter(Document.owner_id == user.id, Check.status == "done")
            .scalar() or 0.0
        )
        avg_plag_val = (
            db.query(func.avg(Check.plag_score))
            .join(Document, Check.document_id == Document.id)
            .filter(Document.owner_id == user.id, Check.status == "done")
            .scalar() or 0.0
        )
        
        # Find personal ranking position
        all_ratings, _, _ = compute_student_ratings(db)
        my_rank_info = next((r for r in all_ratings if r["student_id"] == user.id), None)
        
        stats = {
            "my_checks": len(checks),
            "avg_orig": round(max(0.0, 100.0 - avg_plag_val), 1) if checks else 0.0,
            "avg_icg": round(avg_icg_val, 1),
            "group": user.group_name or "—",
            "my_rank": my_rank_info["rank"] if my_rank_info else "—",
            "total_students": len(all_ratings),
            "rating_score": my_rank_info["rating_score"] if my_rank_info else 0.0,
            "tier": my_rank_info["tier"] if my_rank_info else "—",
            "tier_class": my_rank_info["tier_class"] if my_rank_info else "muted",
            "performance_status": my_rank_info["performance_status"] if my_rank_info else "attention",
            "status_label": my_rank_info["status_label"] if my_rank_info else "—",
            "status_badge_class": my_rank_info["status_badge_class"] if my_rank_info else "muted",
            "risk_reasons": my_rank_info["risk_reasons"] if my_rank_info else [],
            "success_highlights": my_rank_info["success_highlights"] if my_rank_info else [],
        }
    else:
        # Teacher / Admin sees university-wide checks
        checks = db.query(Check).order_by(Check.created_at.desc()).limit(100).all()
        avg_icg_val = db.query(func.avg(Check.icg_score)).filter(Check.status == "done").scalar() or 0.0
        stats = {
            "docs": db.query(func.count(Document.id)).scalar() or 0,
            "checks": db.query(func.count(Check.id)).scalar() or 0,
            "web": db.query(func.count(Document.id)).filter(Document.kind == "web").scalar() or 0,
            "avg_icg": round(avg_icg_val, 1),
            "students_count": db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0,
            "teachers_count": len(teacher_ratings),
        }
    
    return templates.TemplateResponse(
        request, "dashboard.html",
        {
            "user": user,
            "checks": checks,
            "stats": stats,
            "is_student": is_student,
            "student_ratings": student_ratings,
            "teacher_ratings": teacher_ratings,
            "available_groups": available_groups,
            "selected_group": group or "",
            "selected_status": status or "",
            "selected_tab": tab or "students",
            "perf_counts": perf_counts,
        },
    )


@app.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    students = []
    if getattr(user, "role", "student") in ("teacher", "admin"):
        students = db.query(User).filter(User.role == "student").order_by(User.full_name, User.username).all()
    return templates.TemplateResponse(
        request, "upload.html",
        {"user": user, "results": None, "errors": [], "students": students}
    )


@app.post("/upload")
async def upload(
    request: Request,
    files: list[UploadFile] = File(...),
    author: str = Form(""),
    student_id: Optional[int] = Form(None),
    mode: str = Form("both"),
    do_quality: bool = Form(False),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    results, errors = [], []
    is_student = (getattr(user, "role", "student") == "student")
    
    # Resolve document owner & author
    owner_id = user.id if is_student else student_id
    if is_student:
        doc_author = user.full_name or user.username
    else:
        if student_id:
            student_user = db.get(User, student_id)
            doc_author = student_user.full_name or student_user.username if student_user else author
        else:
            doc_author = author.strip() or "Не указан"

    for f in files:
        raw = await f.read()
        if len(raw) > config.MAX_UPLOAD_BYTES:
            errors.append(f"{f.filename}: файл больше 20 МБ")
            continue
        config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = f"{secrets.token_hex(8)}_{Path(f.filename).name}"
        path = config.UPLOAD_DIR / safe_name
        path.write_bytes(raw)
        try:
            text = extract_text(path)
        except Exception as e:
            errors.append(f"{f.filename}: ошибка чтения файла ({e})")
            continue

        if not text or not text.strip():
            errors.append(f"{f.filename}: файл пуст или не содержит читаемого текста")
            continue
        doc = Document(
            title=Path(f.filename).stem[:300],
            author=doc_author,
            kind="student",
            filename=f.filename,
            text=text,
            words=len(text.split()),
            owner_id=owner_id,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        corpus_index.add(doc.id, fingerprint(text))
        do_plag = mode in ("plag", "both")
        do_ai = mode in ("ai", "both")
        # Aris/UX Directive: upload is separated from checking.
        # Create a pending Check row now, run the real check in a background thread.
        check = Check(document_id=doc.id, status="pending", progress=0, status_msg="В очереди")
        db.add(check)
        db.commit()
        db.refresh(check)
        # Aris Directive (v0.4.1, TASK_1): bounded pool, не сырой поток.
        from .checker import submit_background_check
        submit_background_check(check.id, do_plag, do_ai, do_quality)
        results.append(check)

    students = []
    if getattr(user, "role", "student") in ("teacher", "admin"):
        students = db.query(User).filter(User.role == "student").order_by(User.full_name, User.username).all()

    return templates.TemplateResponse(
        request, "upload.html",
        {"user": user, "results": results, "errors": errors, "async_mode": True, "students": students}
    )


@app.get("/report/{check_id}", response_class=HTMLResponse)
def report_page(check_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    check = db.get(Check, check_id)
    if not check:
        raise HTTPException(404)
    
    # Access control: students can only see their own works
    if getattr(user, "role", "student") == "student":
        if check.document.owner_id != user.id and check.document.author not in (user.username, user.full_name):
            raise HTTPException(403, "Доступ к чужой работе запрещён")

    ai_data = json.loads(check.ai_json) if check.ai_json else {}
    quality_data = json.loads(check.quality_json) if check.quality_json else {}
    icg_data = json.loads(check.icg_json) if getattr(check, "icg_json", None) else {}
    highlighted = build_highlighted_html(db, check)
    doc_ids = {m.source_doc_id for m in check.matches}
    docs_map = {d.id: d for d in db.query(Document).filter(Document.id.in_(doc_ids))} if doc_ids else {}
    has_highlights = bool(check.matches) or any(
        s.get("ai", 0) >= config.AI_THRESHOLD_WARN for s in ai_data.get("sentences", [])
    )
    
    from .icg.recommendations import generate_icg_recommendations
    recommendations = generate_icg_recommendations(
        icg_data,
        plag_score=check.plag_score or 0.0,
        ai_score=check.ai_score or 0.0,
        icg_score=check.icg_score or 0.0,
    )

    return templates.TemplateResponse(
        request, "report.html",
        {
            "user": user,
            "check": check,
            "doc": check.document,
            "ai": ai_data,
            "quality": quality_data,
            "icg": icg_data,
            "highlighted": highlighted,
            "docs_map": docs_map,
            "has_highlights": has_highlights,
            "recommendations": recommendations,
        },
    )


@app.get("/set-language/{lang}")
def set_language_endpoint(lang: str, request: Request):
    target = "en" if lang.lower() == "en" else "ru"
    referer = request.headers.get("referer") or "/"
    resp = RedirectResponse(referer, status_code=303)
    resp.set_cookie("uniplag_lang", target, max_age=365 * 86400, httponly=False)
    return resp


@app.get("/report/{check_id}/pdf")
def report_pdf_download(
    check_id: int,
    request: Request,
    lang: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    import re
    check = db.get(Check, check_id)
    if not check:
        raise HTTPException(404, "Проверка не найдена")

    # Access control: students can only download certificate for their own works
    if getattr(user, "role", "student") == "student":
        if check.document.owner_id != user.id and check.document.author not in (user.username, user.full_name):
            raise HTTPException(403, "Доступ к чужой работе запрещён")

    import urllib.parse
    from .pdf_certificate import generate_check_pdf_certificate
    from .i18n import get_language
    
    active_lang = lang if lang and lang.lower() in ("ru", "en") else get_language(request)
    base_url = str(request.base_url).rstrip("/")
    pdf_bytes = generate_check_pdf_certificate(check, base_url=base_url, lang=active_lang)
    
    ascii_filename = f"Certificate_Check_{check.id}_{active_lang.upper()}.pdf"
    encoded_filename = urllib.parse.quote(f"Справка_Проверка_{check.id}_{active_lang.upper()}.pdf")
    content_disp = f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": content_disp},
    )


@app.post("/corpus/add-url")
def corpus_add_url(
    request: Request,
    url: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin),
):
    try:
        page = fetch_url(url.strip())
    except Exception as e:
        return templates.TemplateResponse(
            request, "corpus.html",
            {"user": user, "docs": list_documents(db), "msg": f"Ошибка: {e}"},
            status_code=400,
        )
    doc = Document(
        title=page["title"], kind="web", url=page["url"], domain=page["domain"],
        text=page["text"], words=len(page["text"].split()),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    corpus_index.add(doc.id, fingerprint(page["text"]))
    return RedirectResponse("/corpus", status_code=303)


@app.get("/corpus", response_class=HTMLResponse)
def corpus_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_teacher_or_admin)):
    return templates.TemplateResponse(
        request, "corpus.html", {"user": user, "docs": list_documents(db), "msg": ""}
    )


@app.get("/corpus/search_science", response_class=HTMLResponse)
def corpus_search_science_page(
    request: Request,
    q: Optional[str] = None,
    msg: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin),
):
    from .scientific_crawler import search_all_scientific_repositories
    results = search_all_scientific_repositories(q) if q else []
    return templates.TemplateResponse(
        request,
        "science_search.html",
        {"user": user, "query": q or "", "results": results, "success_msg": msg or ""},
    )


@app.post("/corpus/ingest_science")
async def corpus_ingest_science(
    request: Request,
    title: str = Form(...),
    authors: str = Form(""),
    url: str = Form(""),
    summary: str = Form(""),
    source: str = Form("arXiv"),
    q: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher_or_admin),
):
    from .scientific_crawler import ingest_scientific_article
    import urllib.parse
    article_data = {
        "title": title,
        "authors": authors,
        "url": url,
        "summary": summary,
        "source": source,
        "full_text": f"{title}\n\nАвторы: {authors}\n\nАннотация: {summary}\n\nИсточник: {url}",
    }
    doc = ingest_scientific_article(db, article_data, owner_id=user.id)
    msg = f"✓ Статья «{doc.title[:45]}...» успешно добавлена в корпус проверки!"
    return RedirectResponse(f"/corpus/search_science?q={urllib.parse.quote(q)}&msg={urllib.parse.quote(msg)}", status_code=303)


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(require_teacher_or_admin)):
    doc = db.get(Document, doc_id)
    if doc:
        corpus_index.remove(doc_id)
        db.delete(doc)
        db.commit()
    return {"ok": True}


def list_documents(db: Session, limit: int = 200):
    return db.query(Document).order_by(Document.uploaded_at.desc()).limit(limit).all()


def build_highlighted_html(db: Session, check: Check) -> str:
    import html as html_mod
    from .plagiarism import merge_spans

    if not check or not check.document or not check.document.text:
        return "<p class='muted' style='text-align: center; padding: 30px 0;'>Текст документа отсутствует или не был загружен.</p>"

    text = check.document.text
    text_len = len(text)
    
    spans = []
    if check.matches:
        for m in check.matches:
            for fr in m.fragments:
                spans.append((max(0, min(fr.q_start, text_len)), max(0, min(fr.q_end, text_len))))

    ai = json.loads(check.ai_json) if check.ai_json else {}
    ai_spans = []
    for s in ai.get("sentences", []):
        if s.get("ai", 0) >= config.AI_THRESHOLD_WARN:
            ai_spans.append((max(0, min(s.get("start", 0), text_len)), max(0, min(s.get("end", 0), text_len))))

    plag_set = set(merge_spans(spans))
    ai_set = set(merge_spans(ai_spans))
    all_spans = sorted(plag_set | ai_set)

    parts, pos = [], 0
    for s, e in all_spans:
        s = max(0, min(s, text_len))
        e = max(0, min(e, text_len))
        if s < pos or s >= e:
            continue
        parts.append(html_mod.escape(text[pos:s]))
        is_plag = any(ps <= s and e <= pe for ps, pe in plag_set)
        css = "frag-plag" if is_plag else "frag-ai"
        title = "Заимствование" if is_plag else "Возможный ИИ-текст"
        parts.append(f'<span class="{css}" title="{title}">{html_mod.escape(text[s:e])}</span>')
        pos = e
    parts.append(html_mod.escape(text[pos:]))
    return "".join(parts)


if _mount is not None:
    @app.get("/static/{file_path:path}")
    def serve_blackbox_static(file_path: str):
        normalized = file_path.replace("\\", "/").lstrip("/")
        raw = (
            _mount.get_resource_bytes(f"static/{normalized}") or
            _mount.get_resource_bytes(f"app/static/{normalized}")
        )
        if raw is None:
            raise HTTPException(404, "Static file not found")
        mime_type, _ = mimetypes.guess_type(normalized)
        return Response(content=raw, media_type=mime_type or "application/octet-stream")
else:
    static_dir = BASE / "static"
    if not static_dir.exists():
        static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

from .api import router as api_router  # noqa: E402

app.include_router(api_router)


# ---------------------------------------------------------------------------
# Aris Directive: ICG Admin Control Interface (/admin/icg)
# ---------------------------------------------------------------------------
def _require_admin(user):
    if not user or getattr(user, "role", "teacher") != "admin":
        raise HTTPException(403, "Только администратор")


_icg_deep_lock = threading.Lock()
_icg_deep_running = False


@app.get("/admin/icg", response_class=HTMLResponse)
def icg_admin_page(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    _require_admin(user)

    from .icg.icg_watchdog import last_health, DEGRADED_LEVELS
    from .db import ICGHealth

    health = last_health(db)
    health_hist = db.query(ICGHealth).order_by(ICGHealth.id.desc()).limit(20).all()

    # Recent checks with ICG payload
    checks = db.query(Check).order_by(Check.id.desc()).limit(100).all()
    rows = []
    for c in checks:
        icg = {}
        try:
            icg = json.loads(c.icg_json) if c.icg_json else {}
        except Exception:
            icg = {}
        ratios = icg.get("ratios", {})
        summary = icg.get("summary", {})
        doc = c.document
        rows.append({
            "id": c.id,
            "title": doc.title if doc and doc.title else f"Документ #{c.document_id}",
            "author": doc.author if doc and doc.author else "—",
            "student_id": doc.owner_id if doc and doc.owner_id else None,
            "filename": doc.filename if doc else "",
            "created": c.created_at.strftime("%d.%m %H:%M") if c.created_at else "",
            "doc_id": c.document_id,
            "icg_score": c.icg_score,
            "degraded": bool(icg.get("degraded")),
            "synthesis": round(ratios.get("synthesis", 0) * 100, 1),
            "inference": round(ratios.get("inference", 0) * 100, 1),
            "unsupported": round(ratios.get("unsupported", 0) * 100, 1),
            "contradictory": round(ratios.get("contradictory", 0) * 100, 1),
            "novelty": round(summary.get("novelty_score", 0) * 100, 1),
            "coherence": round(summary.get("reasoning_coherence", 0) * 100, 1),
            "evidence": round(summary.get("evidence_coverage", 0) * 100, 1),
        })

    d = {
        "health": None if health is None else {
            "id": health.id,
            "ts": health.ts.strftime("%d.%m %H:%M") if health.ts else "",
            "blind": f"{health.blind_score}/{health.blind_tot}",
            "red": f"{health.red_score}/{health.red_tot}",
            "level": DEGRADED_LEVELS.get(int(health.degraded), "ok"),
            "degraded": bool(health.degraded),
            "details": json.loads(health.details_json) if health.details_json else {},
        },
        "health_hist": [{
            "id": h.id,
            "ts": h.ts.strftime("%d.%m %H:%M") if h.ts else "",
            "blind": f"{h.blind_score}/{h.blind_tot}",
            "red": f"{h.red_score}/{h.red_tot}",
            "level": DEGRADED_LEVELS.get(int(h.degraded), "ok"),
        } for h in health_hist],
        "rows": rows,
        "baselines": {"blind": "19/22", "red": "17/30"},
    }
    return templates.TemplateResponse(request, "icg_admin.html", {"user": user, "d": d})


@app.post("/admin/icg/watchdog", response_class=HTMLResponse)
def icg_admin_trigger_watchdog(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    _require_admin(user)
    from .icg.icg_watchdog import run_watchdog_once
    res = run_watchdog_once(db)
    return RedirectResponse("/admin/icg", status_code=303)


@app.post("/admin/icg/deep/{check_id}", response_class=HTMLResponse)
def icg_admin_deep_recheck(check_id: int, request: Request, db: Session = Depends(get_db),
                           user: User = Depends(current_user)):
    _require_admin(user)
    global _icg_deep_running
    check = db.get(Check, check_id)
    if not check:
        raise HTTPException(404)
    if _icg_deep_lock.acquire(blocking=False):
        try:
            if _icg_deep_running:
                return RedirectResponse("/admin/icg", status_code=303)
            _icg_deep_running = True
        finally:
            _icg_deep_lock.release()
    else:
        return RedirectResponse("/admin/icg", status_code=303)

    def _run():
        global _icg_deep_running
        try:
            from .icg.integration import check_icg_deep
            from .db import SessionLocal
            with SessionLocal() as db2:
                c2 = db2.get(Check, check_id)
                doc = c2.document
                _, _, payload = check_icg_deep(str(doc.id), doc.text)
                obj = json.loads(c2.icg_json or "{}")
                deep = json.loads(payload)
                deep["contour"] = "deep"
                obj["deep"] = deep
                c2.icg_json = json.dumps(obj, ensure_ascii=False)
                db2.commit()
        except Exception:
            pass
        finally:
            _icg_deep_running = False

    from .checker import submit_heavy_icg
    submit_heavy_icg(_run)
    return RedirectResponse("/admin/icg", status_code=303)


# ---------------------------------------------------------------------------
# Multi-Role User Management Interface (/admin/users)
# ---------------------------------------------------------------------------
@app.get("/admin/users", response_class=HTMLResponse)
def users_admin_page(
    request: Request,
    role: Optional[str] = None,
    msg: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    query = db.query(User).order_by(User.role, User.username)
    if role and role in ("admin", "teacher", "student"):
        query = query.filter(User.role == role)
    users_list = query.all()
    teachers = db.query(User).filter(User.role == "teacher").order_by(User.full_name, User.username).all()
    
    stats = {
        "total": db.query(func.count(User.id)).scalar() or 0,
        "admins": db.query(func.count(User.id)).filter(User.role == "admin").scalar() or 0,
        "teachers": db.query(func.count(User.id)).filter(User.role == "teacher").scalar() or 0,
        "students": db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0,
    }
    return templates.TemplateResponse(
        request, "users_admin.html",
        {
            "user": user,
            "users_list": users_list,
            "teachers": teachers,
            "stats": stats,
            "current_role": role or "all",
            "msg": msg,
        }
    )


@app.post("/admin/users/create")
def user_create(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("student"),
    full_name: str = Form(""),
    group_name: str = Form(""),
    teacher_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    clean_username = username.strip().lower()
    if not clean_username or not password.strip():
        return RedirectResponse("/admin/users?msg=Логин+и+пароль+обязательны", status_code=303)
    
    if db.query(User).filter(User.username == clean_username).first():
        return RedirectResponse(f"/admin/users?msg=Пользователь+{clean_username}+уже+существует", status_code=303)
    
    new_user = User(
        username=clean_username,
        role=role if role in ("admin", "teacher", "student") else "student",
        full_name=full_name.strip(),
        group_name=group_name.strip() if role == "student" else "",
        teacher_id=teacher_id if role == "student" else None,
    )
    new_user.set_password(password.strip())
    db.add(new_user)
    db.commit()
    return RedirectResponse(f"/admin/users?msg=Пользователь+{clean_username}+успешно+создан", status_code=303)


@app.post("/admin/users/{target_user_id}/assign-teacher")
def user_assign_teacher(
    target_user_id: int,
    teacher_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    target = db.get(User, target_user_id)
    if not target:
        raise HTTPException(404, "Пользователь не найден")
    target.teacher_id = teacher_id if teacher_id and teacher_id > 0 else None
    db.commit()
    return RedirectResponse(f"/admin/users?msg=Преподаватель+для+{target.username}+обновлён", status_code=303)


@app.post("/admin/users/{target_user_id}/reset-password")
def user_reset_password(
    target_user_id: int,
    password: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    target = db.get(User, target_user_id)
    if not target:
        raise HTTPException(404, "Пользователь не найден")
    if password.strip():
        target.set_password(password.strip())
        db.commit()
    return RedirectResponse(f"/admin/users?msg=Пароль+для+{target.username}+обновлён", status_code=303)


@app.post("/admin/users/{target_user_id}/delete")
def user_delete(
    target_user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if target_user_id == user.id:
        return RedirectResponse("/admin/users?msg=Нельзя+удалить+собственный+аккаунт", status_code=303)
    target = db.get(User, target_user_id)
    if target:
        db.delete(target)
        db.commit()
    return RedirectResponse("/admin/users?msg=Пользователь+удалён", status_code=303)


# ---------------------------------------------------------------------------
# Public Cryptographic Verification & Anti-Tamper Audit (/verify/{seal})
# ---------------------------------------------------------------------------
@app.get("/verify/{seal}", response_class=HTMLResponse)
def verify_seal_page(
    seal: str,
    request: Request,
    db: Session = Depends(get_db),
):
    from .integrity import verify_report_seal, verify_code_integrity
    
    check = db.query(Check).filter(Check.verification_seal == seal.strip()).first()
    
    code_integrity = verify_code_integrity()
    
    if not check:
        return templates.TemplateResponse(
            request, "verify_seal.html",
            {
                "seal": seal,
                "is_valid": False,
                "error_msg": "Цифровая печать не найдена в реестре выданных сертификатов сервера.",
                "check": None,
                "code_integrity": code_integrity,
            },
            status_code=404,
        )
        
    doc = check.document
    seal_valid = verify_report_seal(
        seal_token=check.verification_seal,
        check_id=check.id,
        doc_title=doc.title,
        doc_text=doc.text,
        plag_score=check.plag_score,
        ai_score=check.ai_score,
        icg_score=check.icg_score,
        created_at_iso=check.created_at.isoformat() if check.created_at else "",
    )
    
    return templates.TemplateResponse(
        request, "verify_seal.html",
        {
            "seal": seal,
            "is_valid": seal_valid,
            "error_msg": "" if seal_valid else "Контрольная сумма оценок или текста не совпадает с цифровой подписью!",
            "check": check,
            "doc": doc,
            "code_integrity": code_integrity,
        }
    )


@app.get("/api/integrity")
def api_integrity_status(user: User = Depends(require_admin)):
    from .integrity import verify_code_integrity
    res = verify_code_integrity()
    return res.summary()


# ---------------------------------------------------------------------------
# 512-bit Project Change Consensus & Audit Dashboard (/admin/consensus)
# ---------------------------------------------------------------------------
@app.get("/admin/consensus", response_class=HTMLResponse)
def consensus_admin_page(
    request: Request,
    msg: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    from .consensus import inspect_pending_changes, read_audit_ledger, verify_audit_ledger
    from .integrity import get_sovereign_key_info
    from .trusted_nodes import is_current_machine_trusted, list_trusted_developers, get_current_machine_fingerprint

    delta = inspect_pending_changes()
    blocks = read_audit_ledger()
    ledger_ok, ledger_msg = verify_audit_ledger()
    key_info = get_sovereign_key_info()
    
    is_trusted, current_record, trust_msg = is_current_machine_trusted()
    trusted_nodes = list_trusted_developers()
    machine_fp = get_current_machine_fingerprint()

    return templates.TemplateResponse(
        request, "consensus_admin.html",
        {
            "user": user,
            "delta": delta,
            "ledger_blocks": blocks,
            "ledger_ok": ledger_ok,
            "key_info": key_info,
            "is_trusted": is_trusted,
            "current_record": current_record,
            "trust_msg": trust_msg,
            "trusted_nodes": trusted_nodes,
            "machine_fp": machine_fp,
            "msg": msg,
        },
    )


@app.post("/admin/consensus/approve")
def consensus_approve_post(
    author: str = Form("Vlad & Aris"),
    description: str = Form("Approved changes"),
    user: User = Depends(require_admin),
):
    import urllib.parse
    from .consensus import approve_and_seal_changes
    block = approve_and_seal_changes(author=author, description=description)
    msg = f"Изменения успешно согласованы и запечатаны 512-битным ключом (Блок №{block.block_index})"
    return RedirectResponse(
        f"/admin/consensus?msg={urllib.parse.quote(msg)}",
        status_code=303,
    )


@app.post("/admin/consensus/register-node")
def consensus_register_node_post(
    developer_name: str = Form("Vlad & Aris (Sovereign Developers)"),
    machine_alias: str = Form("Primary Development Workstation"),
    user: User = Depends(require_admin),
):
    import urllib.parse
    from .trusted_nodes import register_current_machine_as_trusted
    record = register_current_machine_as_trusted(developer_name=developer_name, machine_alias=machine_alias)
    msg = f"Машина {record.hostname} успешно авторизована как доверенный узел ({record.developer_name})"
    return RedirectResponse(f"/admin/consensus?msg={urllib.parse.quote(msg)}", status_code=303)



