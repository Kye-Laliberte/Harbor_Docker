from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Docking
from app.schemas import DockingRead, DockingCreate, DockingUpdate
from app.services.docking_service import sev_list_dockings, sev_create_docking, sev_get_docking, sev_delete_docking


router = APIRouter(prefix="/dockings", tags=["dockings"])


@router.get("/list", response_model=list[DockingRead])
def list_dockings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return sev_list_dockings(db, skip, limit)


@router.post("/create", response_model=DockingRead, status_code=status.HTTP_201_CREATED)
def create_docking(payload: DockingCreate, db: Session = Depends(get_db)):
    docking = sev_create_docking(db, payload)
    db.add(docking)
    db.commit()
    db.refresh(docking)
    return docking

@router.get("/{docking_id}/get", response_model=DockingRead)
def get_docking(docking_id: int, db: Session = Depends(get_db)):
    docking = sev_get_docking(db, docking_id)
    if not docking:
        raise HTTPException(status_code=404, detail="Docking not found")
    return docking
    
@router.delete("/{docking_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_docking(docking_id: int, db: Session = Depends(get_db)):
    sev_delete_docking(db, docking_id)
    return None
