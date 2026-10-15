import logging
from collections.abc import Generator
from sqlalchemy.orm import Session
from app.database import SessionLocal


logger = logging.getLogger(__name__)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        logger.exception("Database request failed")
        raise
    finally:
        db.close()