from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import VoyageCreate, VoyageRead, VoyageUpdate
from app.dependencies import get_db
from app.models import Voyage


router = APIRouter(prefix="/voyages", tags=["voyages"])


@router.get("/getall", response_model=list[VoyageRead])
def list_voyages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Voyage).offset(skip).limit(limit).all()


@router.post("/create", response_model=VoyageRead, status_code=status.HTTP_201_CREATED)
def create_voyage(payload: VoyageCreate, db: Session = Depends(get_db)):
    voyage = Voyage(**payload.model_dump())
    db.add(voyage)
    db.commit()
    db.refresh(voyage)
    return voyage

@router.get("/{voyage_id}/get", response_model=VoyageRead)
def get_voyage(voyage_id: int, db: Session = Depends(get_db)):
    voyage = db.query(Voyage).filter(Voyage.id == voyage_id).first()
    if not voyage:
        raise HTTPException(status_code=404, detail="Voyage not found")
    return voyage


@router.put("/{voyage_id}/update", response_model=VoyageRead)
def update_voyage(voyage_id: int, payload: VoyageUpdate, db: Session = Depends(get_db)):
    voyage = db.query(Voyage).filter(Voyage.id == voyage_id).first()
    if not voyage:
        raise HTTPException(status_code=404, detail="Voyage not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(voyage, field, value)

    db.commit()
    db.refresh(voyage)
    return voyage


@router.delete("/{voyage_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_voyage(voyage_id: int, db: Session = Depends(get_db)):
    voyage = db.query(Voyage).filter(Voyage.id == voyage_id).first()
    if not voyage:
        raise HTTPException(status_code=404, detail="Voyage not found")

    db.delete(voyage)
    db.commit()
    return None
