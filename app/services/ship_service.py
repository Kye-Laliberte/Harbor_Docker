from datetime import datetime, timezone
import logging
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.enums import DockStatus, ShipStatus
from app.models import Ship,Docking,Harbor, Dock,Voyage
from app.schemas import DockingCreate, ShipCreate, ShipUpdate
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
        
    def create_ship(self,payload: ShipCreate, dock_id: Optional[int] = None) -> Ship:
        """Create a new ship after validating cargo and registration uniqueness."""
        
        if dock_id is None and payload.ship_status == ShipStatus.DOCKED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="dock is rquiered for docking")
        
        existing = self.db.query(Ship).filter(Ship.registration_number == payload.registration_number).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                detail="registration number already exists",)

        ship = Ship(**payload.model_dump())
    
        self.db.add(ship)
        
        if ship.ship_status in (ShipStatus.DOCKED, ShipStatus.MAINTENANCE):
            from app.services.docking_service import sev_create_docking

            if dock_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                detail="dock_id is required when creating a docked or maintenance ship",)

            docking_payload = DockingCreate(
            ship_id=ship.id, dock_id=dock_id,
            arrival_date=datetime.now(timezone.utc),
            purpose="initial docking",)

            self.db.flush()  # Flush to assign an ID to the ship before creating docking
            try:
                sev_create_docking(self.db, docking_payload, allow_initial_docking=True)
            except HTTPException as e:
                self.db.rollback()  # Rollback the ship creation if docking fails
                raise e
        self.db.commit()
        self.db.refresh(ship)

        return ship

    def sev_update_ship(self, payload: ShipUpdate) -> Ship:
        """Update an existing ship with provided fields."""
        if self.ship.ship_status in {ShipStatus.DOCKED, ShipStatus.MAINTENANCE,}:
            
            dock_id=self.curent_dock().dock_id
            
            dock = self.db.query(Dock).filter(Dock.id == dock_id).first()
            
            if not dock:
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dock selected not found.")
            
            if payload.current_cargo is not None:
                if dock.cargo_capacity < payload.current_cargo:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="ship cargo_capacity to hight for dock")
            if payload.ship_size is not None:
                if dock.dock_size > payload.ship_size:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="ship_size to larg for dock")
            
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(self.ship, field, value)

        if self.ship.current_cargo > self.ship.cargo_capacity:
            self.db.rollback()  # Rollback the changes to avoid leaving the ship in an inconsistent state
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                detail="current_cargo cannot exceed cargo_capacity",)

        self.db.commit()
        self.db.refresh(self.ship)
        return self.ship

    def delete_ship(self) -> None:
        """Delete a ship by id."""
        if self.ship is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
        self.db.delete(self.ship)
        self.db.commit()
        return None
    
    def curent_voyage(self) -> Voyage:
        if self.ship.ship_status is not ShipStatus.SAILING:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Ship is not currently sailing")

        out = (self.db.query(Voyage).join(Voyage.ship_id  == Ship.id).filter(Voyage.ship_id == self.ship.id, Voyage.arrival_date.is_(None)).first())

        if  out is None:
            return False

        return out
        
    def curent_dock(self) -> Docking:
        if self.ship.ship_status is not ShipStatus.DOCKED:
            logging.info(f"ship {self.ship.id} is not currently docked, status: {self.ship.ship_status}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Ship is not currently docked")
        
        out = (self.db.query(Docking).join(Dock, Dock.id == Docking.dock_id)
                .filter(Docking.ship_id == self.ship.id, Docking.departure_date.is_(None)).where(Dock.dock_status == DockStatus.INACTIVE).first())  
        
        if out is None:
            logging.info(f"No active docking found for ship {self.ship.id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ship is not currently docked (no active docking found)",)
        
        return out