from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import HarborCreate, HarborRead, HarborUpdate
from app.services.harbor_service import (
    sev_create_harbor,
    sev_delete_harbor,
    sev_get_harbor,
    sev_list_harbors,
    sev_update_harbor,
)

router = APIRouter(prefix="/harbors", tags=["harbors"])


@router.get("/home", response_model=list[HarborRead])
def list_harbors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all harbors with optional pagination."""
    return sev_list_harbors(db, skip=skip, limit=limit)


@router.post("/new", response_model=HarborRead, status_code=status.HTTP_201_CREATED)
def create_harbor(payload: HarborCreate, db: Session = Depends(get_db)):
    """Create a new harbor from the provided payload."""
    return sev_create_harbor(db, payload)


@router.get("/{harbor_id}/get", response_model=HarborRead)
def get_harbor(harbor_id: int, db: Session = Depends(get_db)):
    """Retrieve a single harbor by its identifier."""
    return sev_get_harbor(db, harbor_id)


@router.put("/{harbor_id}/update", response_model=HarborRead, status_code=status.HTTP_200_OK)
def update_harbor(harbor_id: int, payload: HarborUpdate, db: Session = Depends(get_db)):
    """Update the details for an existing harbor."""
    return sev_update_harbor(db, harbor_id, payload)


@router.delete("/{harbor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_harbor(harbor_id: int, db: Session = Depends(get_db)):
    """Delete a harbor when it has no attached docks."""
    sev_delete_harbor(db, harbor_id)
    return None
