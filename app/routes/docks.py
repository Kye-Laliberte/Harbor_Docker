from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import DockRead, DockUpdate, DockCreate
from app.services.dock_service import (
    sev_create_dock,
    sev_delete_dock,
    sev_get_dock,
    sev_list_docks,
    sev_update_dock,
)

router = APIRouter(prefix="/docks", tags=["docks"])


@router.get("/getall", response_model=list[DockRead])
def list_docks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List docks with optional pagination."""
    return sev_list_docks(db, skip=skip, limit=limit)


@router.post("/newDock", response_model=DockRead, status_code=status.HTTP_201_CREATED)
def create_dock(payload: DockCreate, db: Session = Depends(get_db)):
    """Create a new dock with a valid harbor."""
    return sev_create_dock(db, payload)


@router.get("/{dock_id}/get", response_model=DockRead)
def get_dock(dock_id: int, db: Session = Depends(get_db)):
    """Retrieve a dock by its identifier."""
    return sev_get_dock(db, dock_id)


@router.put("/{dock_id}/update", response_model=DockRead)
def update_dock(dock_id: int, payload: DockUpdate, db: Session = Depends(get_db)):
    """Update a dock's attributes."""
    return sev_update_dock(db, dock_id, payload)


@router.delete("/{dock_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_dock(dock_id: int, db: Session = Depends(get_db)):
    """Delete a dock by its identifier."""
    sev_delete_dock(db, dock_id)
    return None
