from typing import List, Optional
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

import app.enums as enums
from app.models import Docking, Ship, Dock, Voyage
from app.schemas import DockingCreate, DockingUpdate,ShipUpdate,DockUpdate
from app.services.ship_service import sev_update_ship
from app.services.dock_service import sev_update_dock

class DockingService:


    def __init__(self,db:Session,docking_id:int):
        self.db = db
        self.docking =None
        if docking_id:
            self.docking =  self.sev_get_docking(docking_id)

    def sev_list_dockings(self, skip: int = 0, limit: int = 100) -> List[Docking]:
        """List dockings with optional pagination."""
        out = self.db.query(Docking).offset(skip).limit(limit).all()
        return out

    def sev_get_docking(self, docking_id: int) -> Docking:
        """Retrieve a docking by id or raise an error if it does not exist.
        Output: Returns the matching Docking object.
        """
        docking = self.db.query(Docking).filter(Docking.id == docking_id).first()
        if not docking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docking not found")
        return docking

    def sev_delete_docking(self, docking_id: int) -> bool:
        """Delete a docking by id.
        Output:Returns True after the docking has been removed."""
        
        if not self.docking:
            docking = self.sev_get_docking(self.db, docking_id)

            self.docking = docking

        self.db.delete(docking)
        self.db.commit()
        return True

    def status_update(self,docking_id:int):
        """"""
        if self.docking is None:
            self.docking = self.sev_get_docking(self.db, docking_id)
            
        ship_up = ShipUpdate(ship_status= enums.ShipStatus.DOCKED)
        dock_up = DockUpdate(dock_status= enums.DockStatus.INACTIVE)
        sev_update_ship(db=self.db, ship_id=self.docking.ship_id,payload=ship_up)
        sev_update_dock(db=self.db,dock_id=self.docking.dock_id,payload=dock_up)


def validate_docking_input(dock_id: int, ship_id: int, arrival_date: datetime, departure_date: Optional[datetime], db: Session):
    """Validate docking business rules before creating a docking."""
    dock = db.query(Dock).filter(Dock.id == dock_id).first()
    if not dock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dock not found")
    if str(dock.dock_status.value) != enums.DockStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Dock is not active for new dockings (current status: {dock.dock_status.value})")
    ship = db.query(Ship).filter(Ship.id == ship_id).first()
    if not ship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
    if str(ship.ship_status.value) != enums.ShipStatus.SAILING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ship is not sailing (current status: {ship.ship_status.value})")
    if not _check_size_compatibility(dock, ship):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ship size incompatible with dock size")
    # Cargo capacity rule: dock must be able to accept ship's current cargo
    if dock.cargo_capacity is not None and ship.current_cargo is not None and dock.cargo_capacity < ship.current_cargo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dock cannot accept ship's current cargo based on capacity")
    return True
    
def _ends_at(dt: Optional[datetime]) -> datetime:
    """Normalize a datetime to an end-of-range value for overlap comparisons.
    """
    # Treat None as an open-ended interval to the far future (UTC-aware)
    if dt is None:
        return datetime.max.replace(tzinfo=timezone.utc)

    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _ensure_aware_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure a datetime is timezone-aware in UTC.
    Inputs:
        dt: Optional datetime to normalize.
    Output:
        Returns the same datetime with UTC timezone information when present, or None.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _check_size_compatibility(dock: Dock, ship: Ship) -> bool:
    """Check whether a dock can accommodate a ship based on size."""
    # Dock must be able to accommodate ship size (dock size rank >= ship size rank)
    dock_rank = dock.dock_size
    ship_rank = ship.ship_size
    if dock_rank is None or ship_rank is None:
        return False
    return dock_rank >= ship_rank


def _voyage_state(voyage: Voyage, now: datetime) -> str:
    """Return the operational state used when validating a docking."""
    if voyage.travel_status in (enums.VoyageStatus.ARRIVED, enums.VoyageStatus.CANCELLED):
        return "past"

    departure = _ensure_aware_utc(voyage.departure_date)
    estimated_arrival = _ensure_aware_utc(voyage.estimated_arrival)
    if estimated_arrival <= now:
        return "past"
    if departure > now:
        return "pending"
    return "in_progress"


def _check_overlaps(db: Session, ship_id: int, dock_id: int, arrival: datetime, 
                    departure: Optional[datetime], exclude_id: Optional[int] = None):
    """Ensure a ship and dock do not have overlapping docking windows.
    Inputs:
        db: Database session.
        ship_id: Identifier of the ship being checked.
        dock_id: Identifier of the dock being checked.
        arrival: Planned arrival datetime.
        departure: Optional planned departure datetime.
        exclude_id: Optional docking_id to ignore during the overlap check.

    Output:
        Raises an HTTP 400 error if an overlapping docking is found.
    """
    # A docking remains a conflict regardless of its clearance status.
    existing_for_dock = db.query(Docking).filter(Docking.dock_id == dock_id).all()
    existing_for_ship = db.query(Docking).filter(Docking.ship_id == ship_id).all()
    now = datetime.now(timezone.utc)
    proposed_arrival = _ensure_aware_utc(arrival)
    proposed_departure = _ensure_aware_utc(departure)

    voyages = db.query(Voyage).filter(Voyage.ship_id == ship_id).all()

    def overlaps(a1, d1, a2, d2):
        a1 = _ends_at(a1) if a1 is not None else None
        d1 = _ends_at(d1)
        a2 = _ends_at(a2) if a2 is not None else None
        d2 = _ends_at(d2)
        return not (d1 < a2 or d2 < a1)

    for ex in set(existing_for_dock + existing_for_ship):
        if exclude_id is not None and ex.id == exclude_id:
            continue
        if overlaps(ex.arrival_date, ex.departure_date, proposed_arrival, proposed_departure):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Overlapping docking exists for this ship or dock")

    for voyage in voyages:
        state = _voyage_state(voyage, now)
        if state != "past" and overlaps(
            voyage.departure_date,
            voyage.estimated_arrival,
            proposed_arrival,
            proposed_departure,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ship has a {state} voyage during the requested docking",
            )


def sev_create_docking(db: Session, payload: DockingCreate) -> Docking:
    """Create a new docking after running validation and conflict checks.
    Inputs:
        db: Database session.
        payload: Pydantic payload containing docking details.

    Output: Returns the newly created Docking object.

    Side effects:
    - Marks the associated Dock as INACTIVE (occupied) when a docking is created.
    - Marks the associated Ship as DOCKED.
    """
    arrival = _ensure_aware_utc(payload.arrival_date)
    departure = _ensure_aware_utc(payload.departure_date)
    validate_docking_input(payload.dock_id, payload.ship_id, arrival, departure, db)

    # Validate date ordering and normalize to UTC-aware
    
    if departure is not None and departure < arrival:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="arrival_date must be before departure_date")

    _check_overlaps(db, payload.ship_id, payload.dock_id, arrival, departure)

    data = payload.model_dump()
    data["arrival_date"] = arrival
    data["departure_date"] = departure

    docking = Docking(**data)

    # Update dock and ship statuses symmetrically: when a ship docks, dock becomes INACTIVE (occupied)
    dock = db.query(Dock).filter(Dock.id == payload.dock_id).first()
    ship = db.query(Ship).filter(Ship.id == payload.ship_id).first()

    if dock is None or ship is None:
        # This should not happen because validate_docking_input already checked existence, but guard anyway
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dock or Ship not found during docking creation")

    dock.dock_status = enums.DockStatus.INACTIVE
    ship.ship_status = enums.ShipStatus.DOCKED

    db.add(docking)
    db.commit()
    db.refresh(docking)
    db.refresh(dock)
    db.refresh(ship)
    return docking








    