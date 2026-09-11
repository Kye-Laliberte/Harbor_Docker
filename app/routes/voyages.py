from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Ship
from app.schemas import VoyageArrivalUpdate, VoyageCreate, VoyagePrediction, VoyageRead, Updatedates
from app.services.harbor_service import sev_get_harbor
from app.services.travel_time_service import predict_voyage_metrics
from app.services.voyage_service import VoyageService, leave_dock_for_voyage
from app.services.harbor_service import HarborService
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

@router.get("/predict", response_model=VoyagePrediction)
def predict_voyage(ship_id: int,departure_harbor_id: int,destination_harbor_id: int,db: Session = Depends(get_db),):
    """Predict ship speed and average voyage time from completed voyages."""

    ship = db.query(Ship).filter(Ship.id == ship_id).first()
    if ship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
    HarborS = HarborService(db)
    origin = HarborS.get_harbor(departure_harbor_id)
    destination = HarborS.get_harbor(db, destination_harbor_id)
    if None in (origin.latitude, origin.longitude, destination.latitude, destination.longitude):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="both harbors must have latitude and longitude",)

    return predict_voyage_metrics(db, ship, origin, destination)

@router.get("/{voyage_id}/get", response_model=VoyageRead)
def get_voyage(voyage_id: int, db: Session = Depends(get_db)):
    """Retrieve a voyage by id."""
    return VoyageService(db=db,v_id=voyage_id).get_voyage(voyage_id)
    
@router.post("/{voyage_id}/update_status", status_code=status.HTTP_200_OK)
def update_voyage_status(voyage_id:int, db:Session =Depends(get_db)):
    """Update voyage status and handle departure if applicable."""
    voy = VoyageService(db=db,v_id=voyage_id).get_voyage(voyage_id)
    leave_dock_for_voyage(db,voy)
    return {"status": "updated", "voyage_id": voyage_id}

@router.post("/{voyage_id}/update_destination/{harbor_id}/", status_code=status.HTTP_200_OK)
def update_voyage_destination(harbor_id:int, voyage_id:int, payload: Updatedates,db:Session =Depends(get_db)):
    """Update destination harbor for given voyage."""
    VoyageService(db=db,v_id=voyage_id).change_destonaton(harbor_id,payload)
    return {"status": "updated", "voyage_id": voyage_id, "new_destination_harbor_id": harbor_id}

@router.post("/{voyage_id}/arrive", response_model=VoyageRead, status_code=status.HTTP_200_OK)
def arrive_voyage(voyage_id: int, payload: VoyageArrivalUpdate, db: Session = Depends(get_db)):
    """Record actual arrival and use it as supervised training data."""
    return VoyageService(db=db, v_id=voyage_id).record_arrival(payload)

@router.delete("/{voyage_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_voyage(voyage_id: int, db: Session = Depends(get_db)):
    """Delete a voyage by id."""
    VoyageService(db=db,v_id=voyage_id).delete_voyage(voyage_id)
    return None
