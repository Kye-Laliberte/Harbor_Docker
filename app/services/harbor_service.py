from datetime import datetime, timezone
from typing import Any, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.enums import DockStatus, ShipClearanceStatus, ShipStatus, VesselSize, VoyageStatus
from app.models import Dock, Docking, Harbor, Ship, Voyage
from app.schemas import DockCreate, DockingCreate, HarborUpdate,HarborBase

SIZE_RANK = {
    VesselSize.SMALL: 1,
    VesselSize.MEDIUM: 2,
    VesselSize.LARGE: 3,
}


def _normalize_size(min_size: VesselSize | int) -> VesselSize:
    """Accept either an enum value or its integer rank and normalize it."""
    if isinstance(min_size, VesselSize):
        return min_size
    if isinstance(min_size, int):
        try:
            return VesselSize(min_size)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"min_size must be one of {', '.join(s.name for s in VesselSize)}, got {min_size}",
            ) from exc
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"min_size must be a valid VesselSize value, got {min_size}",
    )

def sev_list_active_docks(db, harbor_id: int, skip: int = 0, limit: int = 100) -> List[Dock]:
    """Return a paginated list of active docks for a specific harbor."""
    out= db.query(Dock).filter(Dock.harbor_id == harbor_id, Dock.dock_status == "active").offset(skip).limit(limit).all()
    if not out:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No active docks found for harbor_id {harbor_id}")
    return out

def sev_list_docks_above_size(db, harbor_id: int, min_size: VesselSize | int, skip: int = 0, limit: int = 100) -> List[Dock]:
    """Return docks for a harbor that are at or above the requested vessel-size rank."""
    normalized = _normalize_size(min_size)
    allowed_ranks = [rank for size, rank in SIZE_RANK.items() if rank >= SIZE_RANK[normalized]]

    out = (db.query(Dock)
           .filter(Dock.harbor_id == harbor_id, Dock.dock_size.in_(allowed_ranks), Dock.dock_status == "active")
           .offset(skip)
           .limit(limit)
           .all()
    )

    if not out:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {normalized.name.lower()} or larger docks found at harbor_id {harbor_id}",
        )
    return out

def sev_create_harbor(db: Session, payload: HarborBase) -> Harbor:
    """Create a new harbor after validating that the name is unique."""
    harbor = Harbor(**payload.model_dump())
    existing = db.query(Harbor).filter(Harbor.name == harbor.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="harbor name already taken")

    db.add(harbor)
    db.commit()
    db.refresh(harbor)
    return harbor

def harbor_active_docks(db: Session, harbor_id: int, dock_size: VesselSize | int) -> list[Dock]:
    """Return active docks in the harbor at or above the given size."""
    normalized = _normalize_size(dock_size)
    allowed_ranks = [rank for size, rank in SIZE_RANK.items() if rank >= SIZE_RANK[normalized]]

    return (db.query(Dock).filter(Dock.harbor_id == harbor_id, Dock.dock_status == "active", 
                                  Dock.dock_size.in_(allowed_ranks)).all())


def sev_delete_harbor(db: Session, harbor_id: int) -> None:
    """Delete a harbor unless it still has docks attached to it."""
    harbor = HarborService(db).get_harbor(db, harbor_id)
    docks = db.query(Dock).filter(Dock.harbor_id == harbor_id).first()
    if docks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="docks still attached")

    db.delete(harbor)
    db.commit()
    return None

class HarborService:
    """CRUD and query operations for harbors."""

    def __init__(self, db: Session):
        self.db = db
    def get_harbor(self, harbor_id: int) -> Harbor:
        harbor = self.db.query(Harbor).filter(Harbor.id == harbor_id).first()
        if not harbor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Harbor not found")
        return harbor

    def all_harbors(self, skip: int = 0, limit: int = 100) -> List[Harbor]:
        """Return a paginated list of harbors from the database."""
        return self.db.query(Harbor).offset(skip).limit(limit).all()

    def create_harbor(self, payload: HarborBase) -> Harbor:
        return sev_create_harbor(self.db, payload)

    def update_harbor(self, harbor_id: int, payload: HarborUpdate) -> Harbor:
        data = payload.model_dump(exclude_unset=True)

        harbor = self.get_harbor(harbor_id)

        if "name" in data and data["name"] is not None:
            existing = self.db.query(Harbor).filter(Harbor.name == data["name"], Harbor.id != harbor_id).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="harbor name already taken")
        
        for field, value in data.items():
            setattr(harbor, field, value)
        
        self.db.commit()
        self.db.refresh(harbor)
        return harbor

class HarborOperations:
    """Monitor and coordinate the operational state of one harbor."""

    def __init__(self, db: Session, harbor_id: int):
        self.db = db
        self.service = HarborService(db)
        if harbor_id:
            self.harbor = self.service.get_harbor(harbor_id)
        

    def dock_status(self, dock_id: int) -> dict[str, Any]:
        """Return availability and current ship information for one dock."""

        dock = (self.db.query(Dock)
            .filter(Dock.id == dock_id, Dock.harbor_id == self.harbor.id).first())
        if dock is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dock not found")

        docking = (self.db.query(Docking)
                   .filter(Docking.dock_id == dock.id, Docking.departure_date.is_(None))
                   .order_by(Docking.arrival_date.desc()).first())
        ship = self.db.query(Ship).filter(Ship.id == docking.ship_id).first() if docking else None

        return {"dock_id": dock.id,"dock_code": dock.dock_code,
            "dock_status": dock.dock_status,
            "is_available": dock.dock_status == DockStatus.ACTIVE and docking is None,
            "is_ship_docked": docking is not None,"ship_id": ship.id if ship else None,
            "ship_name": ship.ship_name if ship else None,"docking_id": docking.id if docking else None,
            "last_arrival": docking.arrival_date if docking else None,}

    def dock_statuses(self) -> List[dict[str, Any]]:
        """Return the operational status of every dock in this harbor."""
        
        return [self.dock_status(dock.id) for dock in self.harbor.docks]

    def last_docking(self, dock_id: int | None = None) -> Docking | None:
        """Return the latest docking for the harbor or for one of its docks."""
        
        query = (
            self.db.query(Docking).join(Dock)
            .filter(Dock.harbor_id == self.harbor.id))
        
        if dock_id is not None:
            query = query.filter(Docking.dock_id == dock_id)
        return query.order_by(Docking.arrival_date.desc()).first()

    def incoming_voyages(self) -> List[Voyage]:
        """Return non-terminal voyages currently heading to this harbor."""
        harbor = self.get_harbor()

        return (
            self.db.query(Voyage)
            .filter(
                Voyage.destination_harbor_id == harbor.id,
                Voyage.travel_status.notin_(
                    (VoyageStatus.ARRIVED, VoyageStatus.CANCELLED)
                ),
            )
            .order_by(Voyage.estimated_arrival.asc()).all()
        )

    def status(self) -> dict[str, Any]:
        """Return a complete operational snapshot for this harbor."""
        harbor = self.get_harbor()
        dock_statuses = self.dock_statuses()
        incoming = self.incoming_voyages()

        return {
            "harbor_id": harbor.id,
            "harbor_name": harbor.name,
            "dock_count": len(dock_statuses),
            "available_dock_count": sum(item["is_available"] for item in dock_statuses),
            "docked_ship_count": sum(item["is_ship_docked"] for item in dock_statuses),
            "docks": dock_statuses,
            "last_docking": self.last_docking(),
            "incoming_voyages": incoming,}

    def create_dock(self, payload: DockCreate) -> Dock:
        """Create a dock in the selected harbor."""
        harbor = self.get_harbor()
        if payload.harbor_id != harbor.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dock must belong to the selected harbor",
            )

        from app.services.dock_service import sev_create_dock

        return sev_create_dock(self.db, payload)

    def create_docking(self,payload: DockingCreate,
        allow_initial_docking: bool = False,) -> Docking:
        """Dock a ship at one of this harbor's docks."""
        harbor = self.get_harbor()
        dock = self.db.query(Dock).filter(Dock.id == payload.dock_id).first()
        if dock is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dock not found")
        if dock.harbor_id != harbor.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dock does not belong to the selected harbor",)

        from app.services.docking_service import sev_create_docking

        return sev_create_docking(self.db, payload, allow_initial_docking=allow_initial_docking)

    def release_docking(self,docking_id: int,
        departure_date: datetime | None = None,) -> Docking:
        """Release a ship and its dock together."""
        docking = (
            self.db.query(Docking).join(Dock)
            .filter(Docking.id == docking_id, Dock.harbor_id == self.harbor.id).first())
        
        if docking is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docking not found")
        if docking.departure_date is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Docking has already been released",
            )

        released_at = departure_date or datetime.now(timezone.utc)
        if released_at.tzinfo is None:
            released_at = released_at.replace(tzinfo=timezone.utc)
        if released_at <= docking.arrival_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="departure_date must be after arrival_date",
            )

        ship = self.db.query(Ship).filter(Ship.id == docking.ship_id).first()
        if ship is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")

        docking.departure_date = released_at
        docking.ship_clearance_status = ShipClearanceStatus.APPROVED
        docking.dock.dock_status = DockStatus.ACTIVE
        ship.ship_status = ShipStatus.SAILING

        self.db.commit()
        self.db.refresh(docking)
        return docking

    def list_dockings(self,skip: int =0, limit:int = 100) -> List[Docking]:
        """List dockings that occurred at the selected harbor."""
        return (
            self.db.query(Docking).join(Dock)
            .filter(Dock.harbor_id == self.harbor.id).offset(skip).limit(limit).all())

    def active_docks(self, skip: int = 0, limit:int=100) -> List[Dock]:
        """Return active docks for the currently selected harbor."""
    
        return sev_list_active_docks(self.db, self.harbor.id, skip=skip, limit=limit)

    def docks_above_size(self,min_size: VesselSize | int,skip: int=0,limit:int=100,) -> List[Dock]:
        """Return active docks at or above the requested vessel size."""
        return sev_list_docks_above_size(self.db,self.harbor.id,min_size,skip=skip,limit=limit,)

    def delete_harbor(self):
        """Delete a harbor unless it still has docks attached to it."""
        harbor = self.service.get_harbor(self.db, self.harbor.id)
        docks = self.db.query(Dock).filter(Dock.harbor_id == self.harbor.id).first()
        if docks:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="docks still attached")
        self.db.delete(harbor)
        self.db.commit()

        self.harbor = None
        return None