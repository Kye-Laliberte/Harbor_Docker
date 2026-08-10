from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.dependencies import get_db
from app.schemas import HarborCreate, HarborRead, HarborUpdate, DockRead
import app.enums as enums
from app.services.harbor_service import (
    sev_create_harbor,
    sev_delete_harbor,
    sev_get_harbor,
    sev_list_harbors,
    sev_update_harbor,
    sev_list_active_docks,
    sev_list_docks_above_size,
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



@router.get("/{harbor_id}/active_docks", response_model=list[DockRead])
def get_active_docks(harbor_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Return active docks for the specified harbor."""
    docks= sev_list_active_docks(db, harbor_id, skip=skip, limit=limit)
    if not docks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No active docks found for harbor_id {harbor_id}")
    return docks

@router.get("/{harbor_id}/docks_above_size/{min_size}", response_model=list[DockRead])
def get_docks_above_size(harbor_id: int, min_size: enums.VesselSize, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Return docks in the harbor at or above the specified vessel size.
    `min_size` must be one of the values from `enums.VesselSize` (e.g. SMALL, MEDIUM, LARGE).
    """
    if not isinstance(min_size, enums.VesselSize):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"min_size must be a valid VesselSize enum value, got {min_size}")
    return sev_list_docks_above_size(db, harbor_id, min_size, skip=skip, limit=limit)


@router.put("/{harbor_id}/update", response_model=HarborRead, status_code=status.HTTP_200_OK)
def update_harbor(harbor_id: int, payload: HarborUpdate, db: Session = Depends(get_db)):
    """Update the details for an existing harbor."""
    return sev_update_harbor(db, harbor_id, payload)


@router.delete("/{harbor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_harbor(harbor_id: int, db: Session = Depends(get_db)):
    """Delete a harbor when it has no attached docks."""
    sev_delete_harbor(db, harbor_id)
    return None
