import logging
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Dock, Harbor,Docking
from app.schemas import DockCreate, DockUpdate


def sev_list_docks(db: Session, skip: int = 0, limit: int = 100) -> List[Dock]:
    """Return a paginated list of docks."""
    return db.query(Dock).offset(skip).limit(limit).all()


def sev_create_dock(db: Session, payload: DockCreate) -> Dock:
    """Create a new dock after validating the harbor exists."""
    harbor = db.query(Harbor).filter(Harbor.id == payload.harbor_id).first()
    if not harbor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Harbor not found")

    dock = Dock(**payload.model_dump())
    db.add(dock)
    db.commit()
    db.refresh(dock)
    return dock


def sev_get_dock(db: Session, dock_id: int) -> Dock:
    """Fetch a dock by id or raise 404 if missing."""
    dock = db.query(Dock).filter(Dock.id == dock_id).first()
    if not dock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dock not found")
    return dock


class DockService:
    def __init__(self,db:Session,dock_id):
        self.db=db
        self.dock_id = dock_id
        self.dock = self.get_dock(dock_id)

    def get_dock(self,dock_id) ->Dock:
        """Fetch a dock by id or raise 404 if missing."""
        dock = self.db.query(Dock).filter(Dock.id == dock_id).first()
        if not dock:
            logging.exception("404 Dock not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dock not found")
        return dock

    def update_dock(self, payload: DockUpdate) -> Dock:
        """Update an existing dock with provided fields."""
        if not self.dock:
            self.dock = sev_get_dock(self.db, self.dock.id)
        data = payload.model_dump(exclude_unset=True)
        harbor = self.db.query(Harbor).filter(Harbor.id == self.dock.harbor_id).first()
        if not harbor:
            logging.error(f"Harbor with id {self.dock.harbor_id} not found while updating dock {self.dock.id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Harbor not found")
        for field, value in data.items():
            setattr(self.dock, field, value)

        self.db.commit()
        self.db.refresh(self.dock)
        return self.dock
    
    def in_dock(self) -> bool:
        """find if a ship is curently in the dock"""
        return self.db.query(
            self.db.query(Docking).filter(
                Docking.departure_date.is_(None),Docking.dock_id==self.dock_id).exists()).scalar()
        
        
    def delete_dock(self) -> None:
        """deletes a dock however a ship can't be in the dock at the time"""
        if self.in_dock():
            logging.error(f"Attempted to delete dock {self.dock_id} while a ship is currently docked.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="ship curently in dock")
        try:
            self.db.delete(self.dock)
        except:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="upcoming voyage or docking")
        self.db.commit()
        logging.info(f"dock {self.dock_id} delate")
        return None