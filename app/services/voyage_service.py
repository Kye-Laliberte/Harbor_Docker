import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Dock, Docking, Ship, Voyage
from app.schemas import Updatedates, VoyageArrivalUpdate, VoyageCreate
from app.services.harbor_service import sev_list_docks_above_size as size_filter
from app.enums import DockStatus, ShipClearanceStatus, ShipStatus, VoyageStatus
from app.services.harbor_service import HarborService
from app.services.travel_time_service import estimate_arrival
from app.services.ship_service import shipService
logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class VoyageService:
    """Service class that encapsulates voyage CRUD operations."""

    def __init__(self, db: Session, v_id: int):
        self.db = db
        self.voyage = None
        self.ship_sev = shipService(db,ship_id=None)
        if v_id:
            self.voyage = self.get_voyage(voyage_id=v_id)
            self.ship_sev.ship = self.ship_sev.sev_get_ship(ship_id=self.voyage.ship_id)

    def date_validation(self,departure_date: Optional[object],arrival_date: 
                Optional[object],estimated_arrival: Optional[object],):
        """Validate the chronological order of voyage dates."""

        departure_date = _as_utc(departure_date)
        arrival_date = _as_utc(arrival_date)
        estimated_arrival = _as_utc(estimated_arrival)

        if arrival_date is not None and departure_date is not None and arrival_date < departure_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="arrival_date cannot be before departure_date",
            )
        if estimated_arrival is not None and departure_date is not None and estimated_arrival < departure_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="estimated_arrival cannot be before departure_date",
            )

    def list_voyages(self, skip: int = 0, limit: int = 100) -> list[Voyage]:
        """Return a paginated list of voyages."""
        return self.db.query(Voyage).offset(skip).limit(limit).all()

    def leave_dock(self) -> Voyage:
        """Release the ship's active docking and mark the voyage departed."""
        if self.voyage is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voyage not found")
        if self.voyage.travel_status != VoyageStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voyage must be approved before leaving the dock",)

        ship = self.ship_sev.ship or self.ship_sev.sev_get_ship(self.voyage.ship_id)
        if ship.ship_status not in (ShipStatus.DOCKED, ShipStatus.SAILING):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ship cannot leave dock while {ship.ship_status.value}",)

        docking = (
            self.db.query(Docking)
            .filter(Docking.ship_id == ship.id, Docking.departure_date.is_(None))
            .order_by(Docking.arrival_date.desc()).first())
        
        if docking is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ship is not currently docked",)

        departure_date = _as_utc(self.voyage.departure_date) or _utcnow()
        if departure_date > _utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voyage departure_date is in the future",)

        docking.departure_date = departure_date
        docking.ship_clearance_status = ShipClearanceStatus.APPROVED
        if docking.dock is not None:
            docking.dock.dock_status = DockStatus.ACTIVE
        ship.ship_status = ShipStatus.SAILING
        self.voyage.departure_date = departure_date
        self.voyage.travel_status = VoyageStatus.DEPARTED

        self.db.commit()
        self.db.refresh(self.voyage)
        return self.voyage


    def create_voyage(self, payload: VoyageCreate) -> Voyage:
        """Create a new voyage after validating business rules.

        Business rules added:
        - Ship must exist and be currently docked.
        - Ship must have an active docking (no departure_date) at the provided departure_harbor_id.
        - On successful creation, the docking.departure_date is set, the ship status is set to SAILING,
          and the dock's dock_status is set to ACTIVE (ship has left).
        """
        harborsev = HarborService(self.db)
        if not self.ship_sev.ship:
           self.ship_sev.ship = self.ship_sev.sev_get_ship(ship_id=payload.ship_id)

        destination = harborsev.get_harbor(harbor_id=payload.destination_harbor_id)

        if payload.departure_harbor_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="destination_harbor_id is required")
        departure_harbor = harborsev.get_harbor(harbor_id=payload.departure_harbor_id)

        if None in (departure_harbor.latitude,
            departure_harbor.longitude,
            destination.latitude,
            destination.longitude,):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                detail="departure and destination harbors must have latitude and longitude",)

        # Find current docking (arrival recorded, no departure yet)
        lastdock = self.ship_sev.curent_dock()

        # Confirm the docking's harbor matches the voyage departure harbor
        if lastdock.dock.harbor_id != payload.departure_harbor_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ship is not located at the specified departure harbor",)

        size_filter(self.db, payload.destination_harbor_id, self.ship_sev.ship.ship_size)
        departure_date = payload.departure_date or None
        estimated_arrival, _, _ = estimate_arrival(self.db, self.ship_sev.ship, departure_harbor, destination, departure_date)
        self.date_validation(departure_date, payload.arrival_date, estimated_arrival)

        data = payload.model_dump()
        data.update(departure_date=departure_date, estimated_arrival=estimated_arrival, arrival_date=None)
        voyage = Voyage(**data)

        self.db.add(voyage)

        self.db.commit()
        self.db.refresh(voyage)
        self.voyage = voyage
        return voyage

    def get_voyage(self, voyage_id: int) -> Voyage:
        """Fetch a voyage by id or raise 404 if it does not exist."""
        voyage = self.db.query(Voyage).filter(Voyage.id == voyage_id).first()
        if not voyage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voyage not found")
        return voyage

    def update_dates(self, payload: Updatedates) -> Voyage:
        """Update voyage date fields with basic validation."""
        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one voyage field is required",
            )

        for field, value in data.items():
            if field == "ship_id":
                continue
            setattr(self.voyage, field, value)

        self.date_validation(self.voyage.departure_date, self.voyage.arrival_date, self.voyage.estimated_arrival)
        self.db.commit()
        self.db.refresh(self.voyage)
        return self.voyage

    def change_destonaton(self, harbor_id: int, payload: Updatedates):
        if self.voyage is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voyage not found")

        harbor_sev =HarborService(db=self.db)
        ship = self.db.query(Ship).filter(Ship.id == self.voyage.ship_id).first()
        if not ship:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")

        size_filter(self.db, harbor_id, ship.ship_size)
        destination = harbor_sev.get_harbor( harbor_id)
        departure_harbor = harbor_sev.get_harbor( harbor_id=self.voyage.departure_harbor_id)

        if None in (
            departure_harbor.latitude,
            departure_harbor.longitude,
            destination.latitude,
            destination.longitude,):

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="departure and destination harbors must have latitude and longitude",)
        
        departure_date = payload.departure_date or self.voyage.departure_date or _utcnow()
        estimated_arrival, _, _ = estimate_arrival(self.db, ship, departure_harbor, destination, departure_date)
        self.date_validation(departure_date, payload.arrival_date, estimated_arrival)

        self.voyage.destination_harbor_id = harbor_id
        self.voyage.departure_date = departure_date
        if payload.arrival_date is not None:
            self.voyage.arrival_date = payload.arrival_date
        self.voyage.estimated_arrival = estimated_arrival

        self.db.commit()
        self.db.refresh(self.voyage)
        return self.voyage


    def record_arrival(self, payload: VoyageArrivalUpdate) -> Voyage:
        if self.voyage is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voyage not found")
        if self.voyage.travel_status != VoyageStatus.DEPARTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voyage must be departed before recording arrival",
            )
        arrival_date = payload.arrival_date
        departure_date = _as_utc(self.voyage.departure_date)
        arrival_date = _as_utc(arrival_date)
        if departure_date and arrival_date < departure_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="arrival_date cannot be before departure_date")
        ship = self.db.query(Ship).filter(Ship.id == self.voyage.ship_id).first()
        if ship is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")
        self.voyage.arrival_date = arrival_date
        self.voyage.travel_status = VoyageStatus.ARRIVED
        ship.ship_status = ShipStatus.DOCKED
        self.db.commit()
        self.db.refresh(self.voyage)
        self.db.refresh(ship)
        return self.voyage

    def approve_voyage(self) -> Voyage:
        if self.voyage is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voyage not found")
        if self.voyage.travel_status != VoyageStatus.SCHEDULED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only scheduled voyages can be approved",)

        if self.voyage.departure_date is None:
            self.voyage.departure_date =  _utcnow

        self.voyage.travel_status = VoyageStatus.APPROVED
        self.db.commit()
        self.db.refresh(self.voyage)
        return self.voyage

    def delete_voyage(self, voyage_id: int) -> bool:
        """Delete a voyage by id."""
        voyage = self.get_voyage(voyage_id)
        self.db.delete(voyage)
        self.db.commit()
        return True

   