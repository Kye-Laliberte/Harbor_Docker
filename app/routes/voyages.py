from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Ship
from app.schemas import VoyageArrivalUpdate, VoyageCreate, VoyagePrediction, VoyageRead, Updatedates
from app.services.harbor_service import HarborService
from app.services.travel_time_service import predict_voyage_metrics, training_sample_count
from app.services.voyage_service import VoyageService
router = APIRouter(prefix="/voyages", tags=["voyages"])


@router.get("/getall", response_model=list[VoyageRead])
def list_voyages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List voyages with optional pagination."""
    return VoyageService(db=db, v_id=None).list_voyages(skip=skip, limit=limit)

@router.post("/create", response_model=VoyageRead, status_code=status.HTTP_201_CREATED)
def create_voyage(payload: VoyageCreate, db: Session = Depends(get_db)):
    """Create a new voyage."""
    
    voyage = VoyageService(db=db, v_id=None).create_voyage(payload)
    return voyage

@router.get("/predict", response_model=VoyagePrediction)
def predict_voyage(ship_id: int,departure_harbor_id: int,destination_harbor_id: int,db: Session = Depends(get_db),):
    """Predict ship speed and average voyage time from completed voyages."""

    ship = db.query(Ship).filter(Ship.id == ship_id).first()
    if ship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
    harbor_service = HarborService(db)
    origin = harbor_service.get_harbor(departure_harbor_id)
    destination = harbor_service.get_harbor(destination_harbor_id)
    if None in (origin.latitude, origin.longitude, destination.latitude, destination.longitude):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="both harbors must have latitude and longitude",)

    return predict_voyage_metrics(db, ship, origin, destination)

@router.get("/{voyage_id}/get", response_model=VoyageRead)
def get_voyage(voyage_id: int, db: Session = Depends(get_db)):
    """Retrieve a voyage by id."""
    return VoyageService(db=db,v_id=voyage_id).get_voyage(voyage_id)

@router.put("/{voyage_id}/update_dates", response_model=VoyageRead, status_code=status.HTTP_200_OK)
def update_voyage_dates(voyage_id: int, payload: Updatedates, db: Session = Depends(get_db)):
    """Update voyage dates and status with chronological validation."""
    voy =VoyageService(db=db, v_id=voyage_id)
    return voy.update_dates(payload)

@router.post("/{voyage_id}/approve", response_model=VoyageRead, status_code=status.HTTP_200_OK)
def approve_voyage(voyage_id: int, db: Session = Depends(get_db)):
    """Approve a scheduled voyage before departure."""
    return VoyageService(db=db, v_id=voyage_id).approve_voyage()

@router.post("/{voyage_id}/leave_dock", response_model=VoyageRead, status_code=status.HTTP_200_OK)
def leave_voyage_dock(voyage_id: int, db: Session = Depends(get_db)):
    """Release the ship from its dock and mark the voyage departed."""
    return VoyageService(db=db, v_id=voyage_id).leave_dock()

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

@router.post("/trane")
def trane_data(db:Session =Depends(get_db)):
    training_sample_count(db=db)