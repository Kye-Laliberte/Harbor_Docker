from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Harbor, Dock
from app.schemas import HarborBase, HarborRead, HarborUpdate, HarborCreate 

router = APIRouter(prefix="/harbors", tags=["harbors"])


@router.get("/home", response_model=list[HarborRead])
def list_harbors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Harbor).offset(skip).limit(limit).all()


@router.post("/new", response_model=HarborRead, status_code=status.HTTP_201_CREATED)
def create_harbor(payload: HarborCreate, db: Session = Depends(get_db)):
    
    harbor = Harbor(**payload.model_dump())
    val = db.query(Harbor).filter(Harbor.name == harbor.name).all()
    if  val:
        raise HTTPException(status_code=400,detail="harbor name already taken")
    db.add(harbor)
    db.commit()
    db.refresh(harbor)
    return harbor


@router.get("/{harbor_id}/get", response_model=HarborRead)
def get_harbor(harbor_id: int, db: Session = Depends(get_db)):
    harbor = db.query(Harbor).filter(Harbor.id == harbor_id).first()
    if not harbor:
        raise HTTPException(status_code=404, detail="Harbor not found")
    return harbor


@router.put("/{harbor_id}/update", response_model=HarborRead,status_code=status.HTTP_200_OK)
def update_harbor(harbor_id: int, payload: HarborUpdate, db: Session = Depends(get_db)):
    harbor = db.query(Harbor).filter(Harbor.id == harbor_id).first()
    if not harbor:
        raise HTTPException(status_code=404, detail="Harbor not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(harbor, field, value)

    db.commit()
    db.refresh(harbor)
    return HarborRead(id=harbor_id, timezone=harbor.timezone, name= harbor.name)

@router.delete("/{harbor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_harbor(harbor_id: int, db: Session = Depends(get_db)):
    harbor = db.query(Harbor).filter(Harbor.id == harbor_id).first()
    if not harbor:
        raise HTTPException(status_code=404, detail="Harbor not found")

    docks = db.query(Dock).filter(Dock.harbor_id == harbor_id).first()
    # this is a temparary soluton tell i flush out the service level
    if docks:
        raise HTTPException(status_code=500, detail="docks still active")

    db.delete(harbor)
    db.commit()
    return None
