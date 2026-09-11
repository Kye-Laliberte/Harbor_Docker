from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import DockRead, DockUpdate, DockCreate
from app.services.dock_service import DockService, sev_list_docks, sev_create_dock

router = APIRouter(prefix="/docks", tags=["docks"])


@router.get("/getall", response_model=list[DockRead],status_code=status.HTTP_200_OK)
def list_docks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List docks with optional pagination."""
    return sev_list_docks(db, skip=skip, limit=limit)


@router.post("/newDock", response_model=DockRead, status_code=status.HTTP_201_CREATED)
def create_dock(payload: DockCreate, db: Session = Depends(get_db)):
    """Create a new dock with a valid harbor."""
    return sev_create_dock(db, payload)


@router.get("/{dock_id}/get", response_model=DockRead,status_code=status.HTTP_200_OK)
def get_dock(dock_id: int, db: Session = Depends(get_db)):
    """Retrieve a dock by its identifier."""
    return DockService(db,dock_id).dock


@router.put("/{dock_id}/update", response_model=DockRead,status_code=status.HTTP_200_OK)
def update_dock(dock_id: int, payload: DockUpdate, db: Session = Depends(get_db)):
    """Update a dock's attributes."""
    return DockService(db,dock_id).update_dock(payload)


@router.delete("/{dock_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_dock(dock_id: int, db: Session = Depends(get_db)):
    """Delete a dock by its identifier."""
    DockService(db, dock_id).delete_dock()
    return None
