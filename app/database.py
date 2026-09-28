from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import BASE_DIR, settings


def _normalise_database_url(url: str) -> str:
    if url.startswith("sqlite:///./"):
        relative = url.replace("sqlite:///./", "", 1)
        absolute = BASE_DIR / relative
        absolute.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{absolute.as_posix()}"
    return url


DATABASE_URL = _normalise_database_url(settings.database_url)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    # Import models before create_all so SQLAlchemy knows every table.
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
