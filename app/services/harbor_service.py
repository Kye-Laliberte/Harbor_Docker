from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.enums import VesselSize
from app.models import Dock, Harbor
from app.schemas import HarborCreate, HarborUpdate

def sev_list_active_docks(db, harbor_id: int, skip: int = 0, limit: int = 100) -> List[Dock]:
    """Return a paginated list of active docks for a specific harbor."""
    out= db.query(Dock).filter(Dock.harbor_id == harbor_id, Dock.dock_status == "active").offset(skip).limit(limit).all()
    if not out:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No active docks found for harbor_id {harbor_id}")
    return out

def sev_list_docks_above_size(db, harbor_id: int, min_size: str, skip: int = 0, limit: int = 100) -> List[Dock]:
    """Return a paginated list of docks for a specific harbor that are at or above the specified size."""

    if min_size is VesselSize.LARGE:
        return db.query(Dock).filter(Dock.harbor_id == harbor_id, Dock.dock_size == VesselSize.LARGE, Dock.dock_status == "active").offset(skip).limit(limit).all()
    elif min_size is VesselSize.MEDIUM:
        return db.query(Dock).filter(Dock.harbor_id == harbor_id, Dock.dock_size == VesselSize.MEDIUM, Dock.dock_status == "active").offset(skip).limit(limit).all()
    elif min_size is VesselSize.SMALL:
        return db.query(Dock).filter(Dock.harbor_id == harbor_id, (Dock.dock_size == VesselSize.SMALL) | (Dock.dock_size == VesselSize.MEDIUM), Dock.dock_status == "active").offset(skip).limit(limit).all()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"min_size must be 'SMALL', 'MEDIUM', or 'LARGE', got {min_size}")

def sev_list_harbors(db: Session, skip: int = 0, limit: int = 100) -> List[Harbor]:
    """Return a paginated list of harbors from the database."""
    return db.query(Harbor).offset(skip).limit(limit).all()


def sev_create_harbor(db: Session, payload: HarborCreate) -> Harbor:
    """Create a new harbor after validating that the name is unique."""
    harbor = Harbor(**payload.model_dump())
    existing = db.query(Harbor).filter(Harbor.name == harbor.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="harbor name already taken")

    db.add(harbor)
    db.commit()
    db.refresh(harbor)
    return harbor

def harbor_active_docks(db: Session, harbor_id: int, dock_size: str) -> list[Dock]:
    """Return the list of docks associated with the given harbor and size."""
    dock = db.query(Dock).filter((Dock.harbor_id == harbor_id, Dock.dock_status == "active")).all()
    if dock.filter(Dock.dock_size >= dock_size):
        return dock
def sev_get_harbor(db: Session, harbor_id: int) -> Harbor:
    """Fetch a single harbor by its identifier or raise a 404 error."""
    harbor = db.query(Harbor).filter(Harbor.id == harbor_id).first()
    if not harbor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Harbor not found")
    return harbor


def sev_update_harbor(db: Session, harbor_id: int, payload: HarborUpdate) -> Harbor:
    """Update an existing harbor with the provided fields after validating the new name."""
    harbor = sev_get_harbor(db, harbor_id)
    data = payload.model_dump(exclude_unset=True)

    if "name" in data and data["name"] is not None:
        existing = db.query(Harbor).filter(Harbor.name == data["name"], Harbor.id != harbor_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="harbor name already taken")

    for field, value in data.items():
        setattr(harbor, field, value)

    db.commit()
    db.refresh(harbor)
    return harbor


def sev_delete_harbor(db: Session, harbor_id: int) -> None:
    """Delete a harbor unless it still has docks attached to it."""
    harbor = sev_get_harbor(db, harbor_id)
    docks = db.query(Dock).filter(Dock.harbor_id == harbor_id).first()
    if docks:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="docks still active")

    db.delete(harbor)
    db.commit()
    return None
