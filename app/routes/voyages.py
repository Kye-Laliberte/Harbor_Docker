from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas import VoyageCreate, VoyageRead, Updatedates
from app.services.voyage_service import VoyageService, leave_dock_for_voyage

router = APIRouter(prefix="/voyages", tags=["voyages"])


@router.get("/getall", response_model=list[VoyageRead])
def list_voyages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List voyages with optional pagination."""
    return VoyageService(db=db, v_id=None).list_voyages(skip=skip, limit=limit)


@router.post("/create", response_model=VoyageRead, status_code=status.HTTP_201_CREATED)
def create_voyage(payload: VoyageCreate, db: Session = Depends(get_db)):
    """Create a new voyage."""
    voyage = VoyageService(db=db, v_id=None).create_voyage(payload)
    leave_dock_for_voyage(db, voyage)
    return voyage

@router.get("/{voyage_id}/get", response_model=VoyageRead)
def get_voyage(voyage_id: int, db: Session = Depends(get_db)):
    """Retrieve a voyage by id."""
    return VoyageService(db=db,v_id=voyage_id).get_voyage(voyage_id)
    
@router.post("/{voyage_id}/update_status", status_code=status.HTTP_200_OK)
def upstatus(voyage_id:int, db:Session =Depends(get_db)):
    """"""
    voy = VoyageService(db=db,v_id=voyage_id).get_voyage(voyage_id)
    leave_dock_for_voyage(db,voy)

@router.post("/{voyage_id}/update_destonaton/{harbor_id}/", status_code=status.HTTP_200_OK)
def updestination(harbor_id:int, voyage_id:int, payload: Updatedates,db:Session =Depends(get_db)):
    """updates destenaton harbor for given voyage"""
    VoyageService(db=db,v_id=voyage_id).change_destonaton(harbor_id,payload)

@router.delete("/{voyage_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_voyage(voyage_id: int, db: Session = Depends(get_db)):
    """Delete a voyage by id."""
    VoyageService(db=db,v_id=voyage_id).delete_voyage(voyage_id)
    return None
