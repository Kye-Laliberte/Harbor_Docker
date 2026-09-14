from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas import ShipCreate, ShipUpdate, ShipRead,DockingRead
from app.services.ship_service import shipService, sev_list_ships
from app.enums import ShipStatus


router = APIRouter(prefix="/ships", tags=["ships"])


@router.get("/list", response_model=list[ShipRead])
def list_ships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List ships with optional pagination."""
    return sev_list_ships(db=db, skip=skip, limit=limit)


@router.post("/new", response_model=ShipRead, status_code=status.HTTP_201_CREATED)
def add_ship(payload: ShipCreate, dock_id: int | None = None, db: Session = Depends(get_db)):
    """Create a ship from the given payload."""
    return shipService(db=db,ship_id=None).create_ship( payload, dock_id=dock_id)

@router.get("/{ship_id}/get", response_model=ShipRead)
def get_ship(ship_id: int, db: Session = Depends(get_db)):
    """Retrieve a ship by its id."""
    return shipService(db,ship_id).ship


@router.put("/{ship_id}/update", response_model=ShipRead)
def update_ship(ship_id: int, payload: ShipUpdate, db: Session = Depends(get_db)):
    """Update a ship using the provided fields."""
    ship=shipService(db,ship_id)

    if ship.ship.ship_status is ShipStatus.SAILING:
        raise
        
    return ship.sev_update_ship(payload)


@router.delete("/{ship_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_ship(ship_id: int, db: Session = Depends(get_db)):
    """Delete a ship by its id."""
    shipService(db=db, ship_id=ship_id).delete_ship()
    return None

@router.get("/{ship_id}/last_docking",response_model=DockingRead,status_code=status.HTTP_200_OK)
def curent_dock_locaton(ship_id:int,db: Session = Depends(get_db)):
    """gets last docking"""
    # Find current docking (arrival recorded, no departure yet)
    out=shipService(db,ship_id).curent_dock()
    
    return out
            # Confirm the docking's harbor matches the voyage departure harbor
    
   