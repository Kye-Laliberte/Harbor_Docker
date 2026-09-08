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

class shipService:
    """"""
    def __init__(self,db:Session,ship_id:int):
        self.db = db 
        self.ship = None
        if ship_id:
            self.ship = self.sev_get_ship(ship_id)

    def sev_get_ship(self, ship_id: int) -> Ship:
        """Fetch a ship by id or raise 404 if missing."""
        ship = self.db.query(Ship).filter(Ship.id == ship_id).first()
        if not ship:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")

        self.ship = ship
        return ship
        
    def sev_create_ship(self,payload: ShipCreate, dock_id: Optional[int] = None) -> Ship:
        """Create a new ship after validating cargo and registration uniqueness."""
        if payload.current_cargo > payload.cargo_capacity:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="current_cargo cannot exceed cargo_capacity",)
    

        existing = self.db.query(Ship).filter(Ship.registration_number == payload.registration_number).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="registration number already exists",)

        ship = Ship(**payload.model_dump())
    
        self.db.add(ship)
        self.db.commit()
        self.db.refresh(ship)
        
        if ship.ship_status in (ShipStatus.DOCKED, ShipStatus.MAINTENANCE):
            from app.services.docking_service import sev_create_docking

            if dock_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                detail="dock_id is required when creating a docked or maintenance ship",)

            docking_payload = DockingCreate(
            ship_id=ship.id, dock_id=dock_id,
            arrival_date=datetime.now(timezone.utc),
            purpose="initial docking",)
            
            sev_create_docking(self.db, docking_payload, allow_initial_docking=True)
        
        return ship

    def sev_update_ship(self, payload: ShipUpdate) -> Ship:
        """Update an existing ship with provided fields."""

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(self.ship, field, value)

        if self.ship.current_cargo > self.ship.cargo_capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="current_cargo cannot exceed cargo_capacity",)

        self.db.commit()
        self.db.refresh(self.ship)
        return self.ship
    

    def sev_delete_ship(self) -> None:
        """Delete a ship by id."""
        if self.ship is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
        self.db.delete(self.ship)
        self.db.commit()
        return None
