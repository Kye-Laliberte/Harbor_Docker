from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Ship, Voyage
from app.schemas import Updatedates, VoyageCreate
from app.services.harbor_service import sev_list_docks_above_size as size_filter


class VoyageService:
    """Service class that encapsulates voyage CRUD operations."""

    def __init__(self, db: Session, v_id: int):
        self.db = db
        self.voyage = None
        if v_id:
            self.voyage = self.get_voyage(voyage_id=v_id)

    def date_validation(self, departure_date: Optional[str], arrival_date: Optional[str], estimated_arrival: Optional[str]):
        """Validate the chronological order of voyage dates."""
        if arrival_date is not None and arrival_date < departure_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="arrival_date cannot be before departure_date",
            )
        if estimated_arrival is not None and estimated_arrival < departure_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="estimated_arrival cannot be before departure_date",
            )

    def list_voyages(self, skip: int = 0, limit: int = 100) -> list[Voyage]:
        """Return a paginated list of voyages."""
        return self.db.query(Voyage).offset(skip).limit(limit).all()

    def create_voyage(self, payload: VoyageCreate) -> Voyage:
        """Create a new voyage after validating business rules."""
        ship_size = self.db.query(Ship).filter(Ship.id == payload.ship_id).first().ship_size
       
        # this line checks if there are docks available at the destination harbor that can accommodate the ship size
        
        size_filter(self.db, payload.destination_harbor_id, ship_size)
           
        
        self.date_validation(payload.departure_date, payload.arrival_date, payload.estimated_arrival)

        voyage = Voyage(**payload.model_dump())
        self.db.add(voyage)
        self.db.commit()
        self.db.refresh(voyage)
        return voyage

    def get_voyage(self, voyage_id: int) -> Voyage:
        """Fetch a voyage by id or raise 404 if it does not exist."""
        voyage = self.db.query(Voyage).filter(Voyage.id == voyage_id).first()
        if not voyage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voyage not found")
        return voyage

    def update_dates(self, voyage_id: int, payload: VoyageUpdate) -> Voyage:
        """"""

    def change_destonaton():
        pass

    def approve_voyage() -> bool:
        pass
    
    def delete_voyage(self, voyage_id: int) -> None:
        """Delete a voyage by id."""
        voyage = self.get_voyage(voyage_id)
        self.db.delete(voyage)
        self.db.commit()
        return None
