from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Harbor
from app.schemas import HarborBase, HarborRead

router = APIRouter(prefix="/harbors", tags=["harbors"])


@router.get("/home", response_model=list[HarborRead])
def list_harbors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Harbor).offset(skip).limit(limit).all()


@router.post("/new", response_model=HarborRead, status_code=status.HTTP_201_CREATED)
def create_harbor(payload: HarborBase, db: Session = Depends(get_db)):
    
    harbor = Harbor(**payload.model_dump())
    
    db.add(harbor)
    db.commit()
    db.refresh(harbor)
    return harbor


@router.get("/{harbor_id}", response_model=HarborRead)
def get_harbor(harbor_id: int, db: Session = Depends(get_db)):
    harbor = db.query(Harbor).filter(Harbor.id == harbor_id).first()
    if not harbor:
        raise HTTPException(status_code=404, detail="Harbor not found")
    return harbor
