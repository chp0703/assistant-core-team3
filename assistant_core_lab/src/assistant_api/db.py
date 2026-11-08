"""SQLModel persistence primitives for Lab 5.

Only privacy-safe interaction metadata is stored.  Raw session identifiers and
question text never enter these models or repository methods.
"""

import hashlib
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select


def utcnow() -> datetime:
    """Return an aware UTC timestamp for persisted records."""
    return datetime.now(timezone.utc)


class ChatSession(SQLModel, table=True):
    """A privacy-preserving, salted-hash conversation session."""

    __tablename__ = "chat_session"

    id: str = Field(primary_key=True, max_length=16)
    channel: str = Field(default="web", max_length=16)
    created_at: datetime = Field(default_factory=utcnow)
    interactions: list["Interaction"] = Relationship(back_populates="session")


class Interaction(SQLModel, table=True):
    """Metadata for one completed assistant request."""

    __tablename__ = "interaction"

    id: int | None = Field(default=None, primary_key=True)
    request_id: str = Field(index=True, unique=True, max_length=32)
    session_id: str = Field(foreign_key="chat_session.id", index=True, max_length=16)
    intent: str = Field(index=True, max_length=16)
    topic: str | None = Field(default=None, max_length=32)
    resolved: bool = Field(default=True)
    degraded: bool = Field(default=False)
    latency_ms: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    session: ChatSession | None = Relationship(back_populates="interactions")
    feedback: list["Feedback"] = Relationship(back_populates="interaction")


class Feedback(SQLModel, table=True):
    """Feedback linked to an interaction by its public request id."""

    __tablename__ = "feedback"
    __table_args__ = (CheckConstraint("rating IN (-1, 0, 1)", name="ck_feedback_rating"),)

    id: int | None = Field(default=None, primary_key=True)
    request_id: str = Field(foreign_key="interaction.request_id", index=True, max_length=32)
    rating: int
    comment: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utcnow)
    interaction: Interaction | None = Relationship(back_populates="feedback")


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:  # noqa: ANN001
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def make_engine(url: str) -> Engine:
    """Create the single application engine, enforcing SQLite foreign keys."""
    if url in {"sqlite://", "sqlite:///:memory:"}:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
    if url.startswith("sqlite"):
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def init_db(engine: Engine) -> None:
    """Create the application tables when they do not yet exist."""
    SQLModel.metadata.create_all(engine)


def hash_session(raw: str, salt: str) -> str:
    """Return the stable, truncated SHA-256 identifier for a raw session id."""
    if not salt or not salt.strip():
        raise ValueError("A non-empty session salt is required.")
    return hashlib.sha256((salt + raw).encode("utf-8")).hexdigest()[:16]


class Repository:
    """The boundary through which the application persists interaction data."""

    def __init__(self, engine: Engine, salt: str):
        if not salt or not salt.strip():
            raise ValueError("A non-empty session salt is required.")
        self.engine = engine
        self.salt = salt

    def list_feedback(self, limit: int = 100) -> list[Feedback]:
        with Session(self.engine) as db:
            query = select(Feedback).order_by(Feedback.created_at.desc(), Feedback.id.desc()).limit(limit)
            return list(db.exec(query).all())

    def record_interaction(
        self,
        raw_session: str,
        request_id: str,
        intent: str,
        topic: str | None,
        resolved: bool,
        degraded: bool,
        latency_ms: float,
    ) -> None:
        """Atomically persist a session (if new) and its interaction metadata."""
        session_id = hash_session(raw_session, self.salt)
        with Session(self.engine) as db, db.begin():
            if db.get(ChatSession, session_id) is None:
                db.add(ChatSession(id=session_id))
            db.add(
                Interaction(
                    request_id=request_id,
                    session_id=session_id,
                    intent=intent,
                    topic=topic,
                    resolved=resolved,
                    degraded=degraded,
                    latency_ms=latency_ms,
                )
            )

    def add_feedback(self, request_id: str, rating: int, comment: str | None) -> Feedback | None:
        """Save feedback for an existing interaction and return its persisted fields."""
        with Session(self.engine) as db:
            interaction = db.exec(select(Interaction).where(Interaction.request_id == request_id)).first()
            if interaction is None:
                return None
            feedback = Feedback(request_id=request_id, rating=rating, comment=comment)
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            return feedback
