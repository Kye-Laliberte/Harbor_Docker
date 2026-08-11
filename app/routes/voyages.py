from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import VoyageCreate, VoyageRead
from app.services.voyage_service import VoyageService

router = APIRouter(prefix="/voyages", tags=["voyages"])


@router.get("/getall", response_model=list[VoyageRead])
def list_voyages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List voyages with optional pagination."""
    return VoyageService(db).list_voyages(skip=skip, limit=limit)


@router.post("/create", response_model=VoyageRead, status_code=status.HTTP_201_CREATED)
def create_voyage(payload: VoyageCreate, db: Session = Depends(get_db)):
    """Create a new voyage."""
    return VoyageService(db).create_voyage(payload)


@router.get("/{voyage_id}/get", response_model=VoyageRead)
def get_voyage(voyage_id: int, db: Session = Depends(get_db)):
    """Retrieve a voyage by id."""
    return VoyageService(db).get_voyage(voyage_id)


@router.delete("/{voyage_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_voyage(voyage_id: int, db: Session = Depends(get_db)):
    """Delete a voyage by id."""
    VoyageService(db).delete_voyage(voyage_id)
    return None
