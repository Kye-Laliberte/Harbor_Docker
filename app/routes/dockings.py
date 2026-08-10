from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import DockingRead, DockingCreate, DockingUpdate
from app.services.docking_service import sev_list_dockings, sev_create_docking, sev_get_docking, sev_delete_docking

router = APIRouter(prefix="/dockings", tags=["dockings"])


@router.get("/list", response_model=list[DockingRead])
def list_dockings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List dockings with optional pagination."""
    return sev_list_dockings(db, skip, limit)


@router.post("/create", response_model=DockingRead, status_code=status.HTTP_201_CREATED)
def create_docking(payload: DockingCreate, db: Session = Depends(get_db)):
    """Create a new docking."""
    return sev_create_docking(db, payload)


@router.get("/{docking_id}/get", response_model=DockingRead)
def get_docking(docking_id: int, db: Session = Depends(get_db)):
    """Retrieve a docking by id."""
    return sev_get_docking(db, docking_id)


@router.delete("/{docking_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_docking(docking_id: int, db: Session = Depends(get_db)):
    """Delete a docking by id."""
    sev_delete_docking(db, docking_id)
    return None
