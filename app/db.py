from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import create_engine, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from . import config
from .security import hash_password, verify_password


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="teacher")  # admin, teacher, student
    full_name: Mapped[str] = mapped_column(String(200), default="")
    group_name: Mapped[str] = mapped_column(String(50), default="")
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.password_hash)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    author: Mapped[str] = mapped_column(String(200), default="")
    kind: Mapped[str] = mapped_column(String(20), default="student")
    filename: Mapped[str] = mapped_column(String(400), default="")
    url: Mapped[str] = mapped_column(Text, default="")
    domain: Mapped[str] = mapped_column(String(200), default="")
    text: Mapped[str] = mapped_column(Text)
    words: Mapped[int] = mapped_column(Integer, default=0)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped[Optional["User"]] = relationship(foreign_keys=[owner_id])


class Check(Base):
    __tablename__ = "checks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    plag_score: Mapped[float] = mapped_column(Float, default=0.0)
    ai_score: Mapped[float] = mapped_column(Float, default=0.0)
    ai_method: Mapped[str] = mapped_column(String(40), default="")
    ai_json: Mapped[str] = mapped_column(Text, default="")
    quality_json: Mapped[str] = mapped_column(Text, default="")
    icg_score: Mapped[float] = mapped_column(Float, default=0.0)
    icg_json: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    status_msg: Mapped[str] = mapped_column(Text, default="")
    verification_seal: Mapped[str] = mapped_column(String(64), default="")

    document: Mapped["Document"] = relationship()
    matches: Mapped[list["Match"]] = relationship(back_populates="check", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    check_id: Mapped[int] = mapped_column(ForeignKey("checks.id"))
    source_doc_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    source_label: Mapped[str] = mapped_column(String(400))
    sim: Mapped[float] = mapped_column(Float, default=0.0)
    matched_words: Mapped[int] = mapped_column(Integer, default=0)

    check: Mapped["Check"] = relationship(back_populates="matches")
    fragments: Mapped[list["Fragment"]] = relationship(cascade="all, delete-orphan")


class Fragment(Base):
    __tablename__ = "fragments"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    q_start: Mapped[int]
    q_end: Mapped[int]
    text: Mapped[str] = mapped_column(Text)


class ICGHealth(Base):
    """Aris Directive: ICG Health black-box — history of system state vs v0.4 reference."""
    __tablename__ = "icg_health"
    id: Mapped[int] = mapped_column(primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    blind_score: Mapped[int] = mapped_column(Integer, default=0)
    blind_tot: Mapped[int] = mapped_column(Integer, default=0)
    red_score: Mapped[int] = mapped_column(Integer, default=0)
    red_tot: Mapped[int] = mapped_column(Integer, default=0)
    degraded: Mapped[int] = mapped_column(Integer, default=0)  # 0=ok, 1=warning, 2=critical
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    triggered_by: Mapped[str] = mapped_column(String(40), default="periodic")


engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine)


from sqlalchemy import text


def init_db() -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        # Migrations for checks
        for col, col_type in [
            ("icg_score", "FLOAT DEFAULT 0.0"),
            ("icg_json", "TEXT DEFAULT ''"),
            ("status", "VARCHAR(20) DEFAULT 'pending'"),
            ("progress", "INTEGER DEFAULT 0"),
            ("status_msg", "TEXT DEFAULT ''"),
            ("verification_seal", "VARCHAR(64) DEFAULT ''"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE checks ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass
        # Migrations for users
        for col, col_type in [
            ("full_name", "VARCHAR(200) DEFAULT ''"),
            ("group_name", "VARCHAR(50) DEFAULT ''"),
            ("teacher_id", "INTEGER REFERENCES users(id)"),
            ("created_at", "DATETIME"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass
        # Migrations for documents
        try:
            conn.execute(text("ALTER TABLE documents ADD COLUMN owner_id INTEGER REFERENCES users(id)"))
            conn.commit()
        except Exception:
            pass

    # Seed default users if empty
    with SessionLocal() as db:
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(username="admin", role="admin", full_name="Главный Администратор")
            admin.set_password("admin123")
            db.add(admin)
        if not db.query(User).filter(User.username == "teacher").first():
            teacher = User(username="teacher", role="teacher", full_name="проф. Смирнов А.В.")
            teacher.set_password("teacher123")
            db.add(teacher)
        if not db.query(User).filter(User.username == "student").first():
            student = User(username="student", role="student", full_name="Иванов Иван", group_name="ИТ-401")
            student.set_password("student123")
            db.add(student)
        try:
            db.commit()
        except Exception:
            db.rollback()


def recover_orphaned_checks(lifetime_minutes: float = 30.0) -> int:
    """Aris Directive (v0.4.1, STABILITY): на старте переводить зависшие
    проверки (status in pending/running старше lifetime_minutes) в error.

    Не ставим их в очередь повторно: если файл роняет воркер/ICG, повтор
    просто снова сломает проверку. Пользователь сам повторит загрузку.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=lifetime_minutes)
    with SessionLocal() as db:
        orphans = db.query(Check).filter(
            Check.status.in_(["pending", "running"]),
            Check.created_at < cutoff,
        ).all()
        for c in orphans:
            c.status = "error"
            c.progress = 0
            c.status_msg = "Проверка была прервана из-за перезапуска сервера"
        db.commit()
        return len(orphans)
