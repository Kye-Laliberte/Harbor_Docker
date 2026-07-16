from app.database import SessionLocal
import logging
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logging.error(f"Error: {e}")
    finally:
        db.close()