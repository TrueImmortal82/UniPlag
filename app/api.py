from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import _sessions, get_db
from .checker import run_check
from .crawler import fetch_url
from .db import Check, Document, User
from .fingerprint import fingerprint

router = APIRouter(prefix="/api")


def api_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = _sessions.get(request.cookies.get("uniplag_session", ""))
    if not user_id:
        raise HTTPException(401, "Требуется авторизация")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(401, "Требуется авторизация")
    return user


@router.get("/health")
def health():
    return {"status": "ok"}


class CheckTextRequest(BaseModel):
    text: str
    title: str = "Вставленный текст"
    author: str = ""
    mode: str = "both"
    quality: bool = False


@router.post("/check-text")
def check_text(body: CheckTextRequest, db: Session = Depends(get_db), user: User = Depends(api_user)):
    if len(body.text.strip()) < 200:
        raise HTTPException(400, "Текст слишком короткий (минимум 200 символов)")
    doc = Document(
        title=body.title[:300], author=body.author, kind="inline",
        text=body.text, words=len(body.text.split()),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    do_plag = body.mode in ("plag", "both")
    do_ai = body.mode in ("ai", "both")
    check = run_check(db, doc, do_plag=do_plag, do_ai=do_ai, do_quality=body.quality)
    return format_check(db, check)


@router.get("/checks/{check_id}")
def get_check(check_id: int, db: Session = Depends(get_db), user: User = Depends(api_user)):
    check = db.get(Check, check_id)
    if not check:
        raise HTTPException(404)
    return format_check(db, check)


@router.get("/checks/{check_id}/status")
def check_status(check_id: int, db: Session = Depends(get_db), user: User = Depends(api_user)):
    check = db.get(Check, check_id)
    if not check:
        raise HTTPException(404)
    data = {
        "check_id": check.id,
        "status": getattr(check, "status", "pending"),
        "progress": getattr(check, "progress", 0),
        "status_msg": getattr(check, "status_msg", ""),
        "document_title": check.document.title if check.document else "",
    }
    if getattr(check, "status", "") == "done":
        data["plagiarism_percent"] = check.plag_score
        data["originality_percent"] = round(100.0 - check.plag_score, 2)
        data["ai_score"] = check.ai_score
        data["icg_score"] = getattr(check, "icg_score", 0.0)
        data["report_url"] = f"/report/{check.id}"
    return data


class ICGRequest(BaseModel):
    text: str
    document_id: str = "doc_inline"
    use_llm: bool = False


@router.post("/icg/graph")
def analyze_icg_graph(body: ICGRequest, user: User = Depends(api_user)):
    if len(body.text.strip()) < 50:
        raise HTTPException(400, "Текст слишком короткий для графового анализа (минимум 50 символов)")
    from .icg.graph_builder import ICGGraphBuilder
    builder = ICGGraphBuilder()
    graph = builder.build_graph(document_id=body.document_id, text=body.text, use_llm=body.use_llm)
    return graph.model_dump()


def format_check(db: Session, check: Check) -> dict:
    ai = {}
    if check.ai_json:
        try:
            ai = json_loads(check.ai_json)
        except Exception:
            pass
    quality = {}
    if check.quality_json:
        try:
            quality = json_loads(check.quality_json)
        except Exception:
            pass
    icg = {}
    if getattr(check, "icg_json", None):
        try:
            icg = json_loads(check.icg_json)
        except Exception:
            pass
    return {
        "check_id": check.id,
        "document": {"id": check.document.id, "title": check.document.title, "words": check.document.words},
        "originality_percent": round(100.0 - check.plag_score, 2),
        "plagiarism_percent": check.plag_score,
        "ai_score": check.ai_score,
        "ai_method": check.ai_method,
        "icg_score": getattr(check, "icg_score", 0.0),
        "icg": icg,
        "quality": quality,
        "sources": [
            {
                "source_id": m.source_doc_id,
                "label": m.source_label,
                "similarity_percent": m.sim,
            }
            for m in sorted(check.matches, key=lambda x: -x.sim)
        ],
        "fragments": [
            {"start": fr.q_start, "end": fr.q_end, "text": fr.text, "match_id": fr.match_id}
            for m in check.matches for fr in m.fragments
        ],
        "ai_sentences": ai.get("sentences", []),
        "ai_note": ai.get("note", ""),
        "created_at": check.created_at.isoformat(),
    }


def json_loads(s: str) -> dict:
    import json
    return json.loads(s)


@router.post("/crawl")
def crawl(urls: list[str], db: Session = Depends(get_db), user: User = Depends(api_user)):
    added, failed = [], []
    for url in urls:
        try:
            page = fetch_url(url.strip())
        except Exception as e:
            failed.append({"url": url, "error": str(e)})
            continue
        doc = Document(
            title=page["title"], kind="web", url=page["url"], domain=page["domain"],
            text=page["text"], words=len(page["text"].split()),
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        from .plagiarism import corpus_index as ci
        ci.add(doc.id, fingerprint(page["text"]))
        added.append({"url": url, "doc_id": doc.id})
    return {"added": added, "failed": failed}
