from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import ShipCreate, ShipUpdate, ShipRead
from app.services.ship_service import (
    sev_create_ship,
    sev_delete_ship,
    sev_get_ship,
    sev_list_ships,
    sev_update_ship,
)

router = APIRouter(prefix="/ships", tags=["ships"])


@router.get("/list", response_model=list[ShipRead])
def list_ships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List ships with optional pagination."""
    return sev_list_ships(db, skip=skip, limit=limit)


@router.post("/new", response_model=ShipRead, status_code=status.HTTP_201_CREATED)
def add_ship(payload: ShipCreate, db: Session = Depends(get_db)):
    """Create a ship from the given payload."""
    return sev_create_ship(db, payload)


@router.get("/{ship_id}/get", response_model=ShipRead)
def get_ship(ship_id: int, db: Session = Depends(get_db)):
    """Retrieve a ship by its id."""
    return sev_get_ship(db, ship_id)


@router.put("/{ship_id}/update", response_model=ShipRead)
def update_ship(ship_id: int, payload: ShipUpdate, db: Session = Depends(get_db)):
    """Update a ship using the provided fields."""
    return sev_update_ship(db, ship_id, payload)


@router.delete("/{ship_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_ship(ship_id: int, db: Session = Depends(get_db)):
    """Delete a ship by its id."""
    sev_delete_ship(db, ship_id)
    return None
