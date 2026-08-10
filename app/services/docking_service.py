from typing import List, Optional
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import app.enums as enums
from app.models import Docking, Ship, Dock
from app.schemas import DockingCreate


SIZE_RANK = {
    enums.VesselSize.SMALL.value: 1,
    enums.VesselSize.MEDIUM.value: 2,
    enums.VesselSize.LARGE.value: 3,
}


def validate_docking_input(dock_id: int, ship_id: int, arrival_date: datetime, departure_date: Optional[datetime], db: Session):
    """Validate docking business rules before creating a docking.
    Inputs:
        dock_id: Identifier of the dock being requested.
        ship_id: Identifier of the ship requesting the docking.
        arrival_date: Planned arrival timestamp.
        departure_date: Optional planned departure timestamp.
        db: Database session used to fetch related records.
    Output:
        Returns True when the dock and ship pass all validation checks.
    """
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

    Inputs:
        dt: Optional datetime to normalize.

    Output:
        Returns a timezone-aware datetime suitable for interval comparison.
    """
    # Treat None as an open-ended interval to the far future (UTC-aware)
    if dt is None:
        return datetime.max.replace(tzinfo=timezone.utc)
    # ensure returned datetime is timezone-aware UTC
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


def sev_list_dockings(db: Session, skip: int = 0, limit: int = 100) -> List[Docking]:
    """List dockings with optional pagination.

    Inputs:
        db: Database session.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Output:
        Returns a list of Docking objects.
    """
    return db.query(Docking).offset(skip).limit(limit).all()


def _check_size_compatibility(dock: Dock, ship: Ship):
    """Check whether a dock can accommodate a ship based on size.

    Inputs:
        dock: Dock instance being evaluated.
        ship: Ship instance being evaluated.

    Output:
        Returns True when the dock size is large enough for the ship.
    """
    # Dock must be able to accommodate ship size (dock size rank >= ship size rank)
    dock_rank = SIZE_RANK.get(str(dock.dock_size.value), None)
    ship_rank = SIZE_RANK.get(str(ship.ship_size.value), None)
    if dock_rank is None or ship_rank is None:
        return False
    return dock_rank >= ship_rank


def _check_overlaps(db: Session, ship_id: int, dock_id: int, arrival: datetime, departure: Optional[datetime], exclude_id: Optional[int] = None):
    """Ensure a ship and dock do not have overlapping docking windows.

    Inputs:
        db: Database session.
        ship_id: Identifier of the ship being checked.
        dock_id: Identifier of the dock being checked.
        arrival: Planned arrival datetime.
        departure: Optional planned departure datetime.
        exclude_id: Optional docking id to ignore during the overlap check.

    Output:
        Raises an HTTP 400 error if an overlapping docking is found.
    """
    # arrival and departure must be timezone-aware UTC when passed in
    existing_for_dock = db.query(Docking).filter(Docking.dock_id == dock_id).all()
    existing_for_ship = db.query(Docking).filter(Docking.ship_id == ship_id).all()

    def overlaps(a1, d1, a2, d2):
        a1 = _ends_at(a1) if a1 is not None else None
        d1 = _ends_at(d1)
        a2 = _ends_at(a2) if a2 is not None else None
        d2 = _ends_at(d2)
        return not (d1 < a2 or d2 < a1)

    for ex in set(existing_for_dock + existing_for_ship):
        if exclude_id is not None and ex.id == exclude_id:
            continue
        if overlaps(ex.arrival_date, ex.departure_date, arrival, departure):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Overlapping docking exists for this ship or dock")


def sev_create_docking(db: Session, payload: DockingCreate) -> Docking:
    """Create a new docking after running validation and conflict checks.
    Inputs:
        db: Database session.
        payload: Pydantic payload containing docking details.

    Output: Returns the newly created Docking object.
    """
    # Basic existence checks moved here to keep pydantic models simpler
  
    validate_docking_input(payload.dock_id, payload.ship_id, payload.arrival_date, payload.departure_date, db)


    # Validate date ordering and normalize to UTC-aware
    arrival = _ensure_aware_utc(payload.arrival_date)
    departure = _ensure_aware_utc(payload.departure_date)
    if departure is not None and departure < arrival:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="arrival_date must be before departure_date")

    # Prevent overlapping dockings for same dock or same ship
    _check_overlaps(db, payload.ship_id, payload.dock_id, arrival, departure)

    data = payload.model_dump()
    data["arrival_date"] = arrival
    data["departure_date"] = departure

    docking = Docking(**data)
    db.add(docking)
    db.commit()
    db.refresh(docking)
    return docking

def sev_get_docking(db: Session, docking_id: int) -> Docking:
    """Retrieve a docking by id or raise an error if it does not exist.
    Inputs:
        db: Database session.
        docking_id: Identifier of the docking to fetch.
    Output:
        Returns the matching Docking object.
    """
    docking = db.query(Docking).filter(Docking.id == docking_id).first()
    if not docking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docking not found")
    return docking


def sev_delete_docking(db: Session, docking_id: int) -> None:
    """Delete a docking by id.
    Inputs:
        db: Database session.
        docking_id: Identifier of the docking to delete.
    Output:
        Returns None after the docking has been removed.
    """
    docking = sev_get_docking(db, docking_id)
    if not docking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docking not found")
    db.delete(docking)
    db.commit()
    return None


        
        

    