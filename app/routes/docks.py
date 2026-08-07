from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import DockRead,DockBase,DockUpdate,DockCreate
from app.dependencies import get_db
from app.models import Dock,Ship,Harbor


router = APIRouter(prefix="/docks", tags=["docks"])



@router.get("/getall", response_model=list[DockRead])
def list_docks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Dock).offset(skip).limit(limit).all()


@router.post("/newDock", response_model=DockRead, status_code=status.HTTP_201_CREATED)
def create_dock(payload: DockCreate, db: Session = Depends(get_db)):
    dock = Dock(**payload.model_dump())

    harbor=db.query(Harbor).filter(Harbor.id == dock.harbor_id).first()
    if not harbor:
        raise HTTPException(status_code=404,detail="no harbor found at id")
    
    db.add(dock)
    db.commit() 
    db.refresh(dock)
    return dock
    
    
@router.get("/{dock_id}/get", response_model=DockRead)
def get_dock(dock_id: int, db: Session = Depends(get_db)):
    dock = db.query(Dock).filter(Dock.id == dock_id).first()
    if not dock:
        raise HTTPException(status_code=404, detail="Dock not found")
    return dock


@router.put("/{dock_id}/update", response_model=DockRead)
def update_dock(dock_id: int, payload: DockUpdate, db: Session = Depends(get_db)):
    dock = db.query(Dock).filter(Dock.id == dock_id).first()
    if not dock:
        raise HTTPException(status_code=404, detail="Dock not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(dock, field, value)

    db.commit()
    db.refresh(dock)
    return dock


@router.delete("/{dock_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_dock(dock_id: int, db: Session = Depends(get_db)):
    dock = db.query(Dock).filter(Dock.id == dock_id).first()
    if not dock:
        raise HTTPException(status_code=404, detail="Dock not found")

    db.delete(dock)
    db.commit()
    return None
