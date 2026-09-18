from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.dependencies import get_db
from app.schemas import  HarborRead,  DockRead, HarborBase
import app.enums as enums
from app.services.harbor_service import HarborService, HarborOperations


router = APIRouter(prefix="/harbors", tags=["harbors"])


@router.get("/home", response_model=list[HarborRead])
def list_harbors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all harbors with optional pagination."""
    return HarborService(db).all_harbors(skip=skip, limit=limit)


@router.post("/new", response_model=HarborRead, status_code=status.HTTP_201_CREATED)
def create_harbor(payload: HarborBase, db: Session = Depends(get_db)):
    """Create a new harbor from the provided payload."""
    return HarborService(db).create_harbor(payload)


@router.get("/{harbor_id}/get", response_model=HarborRead, status_code= status.HTTP_200_OK)
def get_harbor(harbor_id: int, db: Session = Depends(get_db)):
    """Retrieve a single harbor by its identifier."""
    return HarborService(db).get_harbor(harbor_id)



@router.get("/{harbor_id}/active_docks", response_model=list[DockRead], status_code=status.HTTP_200_OK)
def get_active_docks(harbor_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Return active docks for the specified harbor."""
    docks = HarborOperations(db, harbor_id).active_docks(skip=skip, limit=limit)
    if not docks:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail=f"No active docks found for harbor_id {harbor_id}")
    return docks

@router.get("/{harbor_id}/docks_above_size/{min_size}", response_model=list[DockRead],status_code=status.HTTP_200_OK)
def get_docks_above_size(harbor_id: int, min_size: enums.VesselSize, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Return docks in the harbor at or above the specified vessel size.
    `min_size` must be one of the values from `enums.VesselSize` (e.g. SMALL, MEDIUM, LARGE).
    """
    if not isinstance(min_size, enums.VesselSize):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"min_size must be a valid VesselSize enum value, got {min_size}")
    return HarborOperations(db, harbor_id).docks_above_size(min_size, skip=skip, limit=limit)


@router.delete("/{harbor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_harbor(harbor_id: int, db: Session = Depends(get_db)):
    """Delete a harbor when it has no attached docks."""
    HarborOperations(db,harbor_id).delete_harbor()
    return None
