from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Ship
from app.schemas import DockingCreate, ShipCreate, ShipUpdate
from app.enums import ShipStatus
def sev_list_ships(db: Session, skip: int = 0, limit: int = 100) -> List[Ship]:
    """Return a paginated list of ships from the database."""
    return db.query(Ship).offset(skip).limit(limit).all()


def sev_create_ship(db: Session, payload: ShipCreate, dock_id: Optional[int] = None) -> Ship:
    """Create a new ship after validating cargo and registration uniqueness."""
    if payload.current_cargo > payload.cargo_capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="current_cargo cannot exceed cargo_capacity",
        )
    

    existing = db.query(Ship).filter(Ship.registration_number == payload.registration_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="registration number already exists",
        )

    ship = Ship(**payload.model_dump())
    db.add(ship)
    db.commit()
    db.refresh(ship)

    if ship.ship_status in (ShipStatus.DOCKED, ShipStatus.MAINTENANCE):
        from app.services.docking_service import sev_create_docking

        if dock_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="dock_id is required when creating a docked or maintenance ship",
            )

        docking_payload = DockingCreate(
            ship_id=ship.id,
            dock_id=dock_id,
            arrival_date=datetime.now(timezone.utc),
            purpose="initial docking",)
        
        sev_create_docking(db, docking_payload, allow_initial_docking=True)

    return ship


def sev_get_ship(db: Session, ship_id: int) -> Ship:
    """Fetch a ship by id or raise 404 if missing."""
    ship = db.query(Ship).filter(Ship.id == ship_id).first()
    if not ship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
    return ship


def sev_update_ship(db: Session, ship_id: int, payload: ShipUpdate) -> Ship:
    """Update an existing ship with provided fields."""
    ship = sev_get_ship(db, ship_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ship, field, value)

    if ship.current_cargo > ship.cargo_capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="current_cargo cannot exceed cargo_capacity",
        )

    db.commit()
    db.refresh(ship)
    return ship


def sev_delete_ship(db: Session, ship_id: int) -> None:
    """Delete a ship by id."""
    ship = sev_get_ship(db, ship_id)
    db.delete(ship)
    db.commit()
    return None
