import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Dock, Docking, Ship, Voyage
from app.schemas import Updatedates, VoyageCreate
from app.services.harbor_service import sev_list_docks_above_size as size_filter
from app.enums import DockStatus, ShipClearanceStatus, ShipStatus, VoyageStatus
from app.services.harbor_service import sev_get_harbor

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def leave_dock_for_voyage(db: Session, voyage: Voyage) -> None:
    """Apply the departure state transition for a voyage."""
    logger.debug("leave_dock_for_voyage called for voyage id=%s", getattr(voyage, "id", None))

    if voyage is None:
        logger.error("leave_dock_for_voyage received no voyage")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voyage is required")

    departed = voyage.travel_status == VoyageStatus.DEPARTED
    if departed and voyage.departure_date is not None:
        departure_date = voyage.departure_date
        if departure_date.tzinfo is None:
            departure_date = departure_date.replace(tzinfo=timezone.utc)
        departed = departure_date <= _utcnow()

    if not departed:
        logger.info("Voyage id=%s is not ready to depart", voyage.id)
        return

    ship = db.query(Ship).filter(Ship.id == voyage.ship_id).first()
    if ship is None:
        logger.warning("Ship id=%s not found for voyage id=%s", voyage.ship_id, voyage.id)
        return

    ship.ship_status = ShipStatus.SAILING
    docking = (
        db.query(Docking)
        .filter(Docking.ship_id == ship.id)
        .order_by(Docking.arrival_date.desc()).first())
    
    dock = None
    if docking is not None:
        if docking.departure_date is None or (
            voyage.departure_date is not None
            and docking.departure_date > voyage.departure_date):

            docking.departure_date = voyage.departure_date
        docking.ship_clearance_status = ShipClearanceStatus.APPROVED
        dock = db.query(Dock).filter(Dock.id == docking.dock_id).first()
        if dock is not None:
            dock.dock_status = DockStatus.ACTIVE

    voyage.travel_status = VoyageStatus.DEPARTED

    try:
        db.add(ship)
        if docking is not None:
            db.add(docking)
        if dock is not None:
            db.add(dock)
        db.add(voyage)
        db.commit()
        db.refresh(voyage)
        db.refresh(ship)
        if docking is not None:
            db.refresh(docking)
    except Exception:
        logger.exception("Failed to process departure for voyage id=%s", voyage.id)
        raise

    logger.info("Completed departure for voyage id=%s", voyage.id)


class VoyageService:
    """Service class that encapsulates voyage CRUD operations."""

    def __init__(self, db: Session, v_id: int):
        self.db = db
        self.voyage = None
        if v_id:
            self.voyage = self.get_voyage(voyage_id=v_id)

    def date_validation(self,departure_date: Optional[object],arrival_date: 
                Optional[object],estimated_arrival: Optional[object],):
        """Validate the chronological order of voyage dates."""

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

    def create_voyage(self, payload: VoyageCreate) -> Voyage:
        """Create a new voyage after validating business rules.

        Business rules added:
        - Ship must exist and be currently docked.
        - Ship must have an active docking (no departure_date) at the provided departure_harbor_id.
        - On successful creation, the docking.departure_date is set, the ship status is set to SAILING,
          and the dock's dock_status is set to ACTIVE (ship has left).
        """
        from app.models import Docking, Dock
        from app.enums import ShipStatus

        ship = self.db.query(Ship).filter(Ship.id == payload.ship_id).first()
        if not ship:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")

        #validats destenatons 
        h1=sev_get_harbor(db=self.db,harbor_id=payload.destination_harbor_id)
        h2 =sev_get_harbor(db=self.db,harbor_id=payload.departure_harbor_id)
        
        # Ensure ship is currently docked
        if str(ship.ship_status.value) != ShipStatus.DOCKED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ship must be docked to start a voyage (current status: {ship.ship_status.value})",
            )

        # Find current docking (arrival recorded, no departure yet)
        docking = (
            self.db.query(Docking).join(Dock)
            .filter(Docking.ship_id == ship.id, Dock.id == Dock.id, Dock.id == Dock.id)
            .filter(Docking.departure_date == None).first()
        )

        # More robust: query docking where ship has no departure_date
        if docking is None:
            docking =( self.db.query(Docking)
                .filter(Docking.ship_id == ship.id,Docking.departure_date == None).first())

            if docking is None:
                raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ship is not currently docked (no active docking found)",)

        # Confirm the docking's harbor matches the voyage departure harbor
        if docking.dock is None or docking.dock.harbor_id != payload.departure_harbor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ship is not located at the specified departure harbor",
            )


        size_filter(self.db, payload.destination_harbor_id, ship.ship_size)
        self.date_validation(payload.departure_date, payload.arrival_date, payload.estimated_arrival)

        voyage = Voyage(**payload.model_dump())

        self.db.add(voyage)

        docking.departure_date = voyage.departure_date

        if docking.dock is not None:
            docking.dock.dock_status = DockStatus.ACTIVE

        # Update ship status to sailing
        ship.ship_status = ShipStatus.SAILING

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

        ship = self.db.query(Ship).filter(Ship.id == self.voyage.ship_id).first()
        if not ship:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ship not found")

        size_filter(self.db, harbor_id, ship.ship_size)
        self.date_validation(payload.departure_date, payload.arrival_date, payload.estimated_arrival)

        self.voyage.destination_harbor_id = harbor_id
        if payload.departure_date is not None:
            self.voyage.departure_date = payload.departure_date
        if payload.arrival_date is not None:
            self.voyage.arrival_date = payload.arrival_date
        if payload.estimated_arrival is not None:
            self.voyage.estimated_arrival = payload.estimated_arrival

        self.db.commit()
        self.db.refresh(self.voyage)
        return self.voyage

    def approve_voyage(self) -> bool:
        return False

    def delete_voyage(self, voyage_id: int) -> bool:
        """Delete a voyage by id."""
        voyage = self.get_voyage(voyage_id)
        self.db.delete(voyage)
        self.db.commit()
        return True

   