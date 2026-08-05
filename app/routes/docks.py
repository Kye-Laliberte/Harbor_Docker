from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import DockRead,DockBase
from app.dependencies import get_db
from app.models import Dock,Ship,Harbor


router = APIRouter(prefix="/docks", tags=["docks"])



@router.get("/", response_model=list[DockRead])
def list_docks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Dock).offset(skip).limit(limit).all()


@router.post("/newDock", response_model=DockRead, status_code=status.HTTP_201_CREATED)
def create_dock(payload: DockBase, db: Session = Depends(get_db)):
    dock = Dock(**payload.model_dump())

    harbor=db.query(Harbor).filter(Harbor.id == dock.harbor_id).first()
    if not harbor:
        raise HTTPException(status_code=404,detail="no harbor found at id")
    
    db.add(dock)
    db.commit() 
    db.refresh(dock)
    return DockRead(id=dock.id,harbor_id=dock.harbor_id, dock_status=dock.dock_status,
                    cargo_capacity=dock.cargo_capacity,dock_size=dock.cargo_capacity,
                    dock_name=dock.dock_name,dock_code=dock.dock_name)
    
    
@router.get("/{dock_id}", response_model=DockRead)
def get_dock(dock_id: int, db: Session = Depends(get_db)):
    dock = db.query(Dock).filter(Dock.id == dock_id).first()
    if not dock:
        raise HTTPException(status_code=404, detail="Dock not found")
    return dock


