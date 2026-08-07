from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import DockingRead, DockingCreate, DockingUpdate
from app.services.docking_service import (
    list_dockings as service_list_dockings,
    create_docking as service_create_docking,
    get_docking as service_get_docking,
    update_docking as service_update_docking,
    delete_docking as service_delete_docking,
)


router = APIRouter(prefix="/dockings", tags=["dockings"])


@router.get("/list", response_model=list[DockingRead])
def list_dockings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service_list_dockings(db, skip=skip, limit=limit)


@router.post("/create", response_model=DockingRead, status_code=201)
def create_docking(payload: DockingCreate, db: Session = Depends(get_db)):
    return service_create_docking(db, payload)


@router.get("/{docking_id}/get", response_model=DockingRead)
def get_docking(docking_id: int, db: Session = Depends(get_db)):
    return service_get_docking(db, docking_id)


@router.put("/{docking_id}/update", response_model=DockingRead)
def update_docking(docking_id: int, payload: DockingUpdate, db: Session = Depends(get_db)):
    return service_update_docking(db, docking_id, payload)


@router.delete("/{docking_id}/delete", status_code=204)
def delete_docking(docking_id: int, db: Session = Depends(get_db)):
    return service_delete_docking(db, docking_id)
