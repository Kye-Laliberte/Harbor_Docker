from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use the project's Base and models
from app.database import Base
from app.models import Ship, Dock, Docking, Voyage
import app.enums as enums
from app.services.docking_service import leave_dock


def run_smoke_test():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # create ship
    ship = Ship(
        ship_name="test ship",
        current_cargo=0,
        registration_number="reg-123",
        ship_status=enums.ShipStatus.DOCKED,
        cargo_capacity=1000,
        ship_size=enums.VesselSize.MEDIUM,
    )

    # create dock
    dock = Dock(
        dock_code=1,
        dock_name="main dock",
        harbor_id=1,
        dock_status=enums.DockStatus.INACTIVE,
        cargo_capacity=1000,
        dock_size=enums.VesselSize.MEDIUM,
    )

    db.add(ship)
    db.add(dock)
    db.commit()
    db.refresh(ship)
    db.refresh(dock)

    # create docking with arrival_date but no departure_date (ship is at dock)
    arrival = datetime.now(timezone.utc) - timedelta(hours=2)
    docking = Docking(
        ship_id=ship.id,
        dock_id=dock.id,
        arrival_date=arrival,
        departure_date=None,
        ship_clearance_status=enums.ShipClearanceStatus.PENDING,
        purpose="loading",
    )

    db.add(docking)
    db.commit()
    db.refresh(docking)

    # create voyage with departed status
    dep_date = datetime.now(timezone.utc)
    voyage = Voyage(
        ship_id=ship.id,
        departure_date=dep_date,
        estimated_arrival=dep_date + timedelta(days=5),
        arrival_date=None,
        travel_status=enums.VoyageStatus.DEPARTED,
        departure_harbor_id=1,
        destination_harbor_id=2,
    )

    db.add(voyage)
    db.commit()
    db.refresh(voyage)

    print("Before leave_dock:")
    d = db.query(Docking).filter(Docking.id == docking.id).first()
    s = db.query(Ship).filter(Ship.id == ship.id).first()
    dk = db.query(Dock).filter(Dock.id == dock.id).first()
    print("Docking departure_date:", d.departure_date)
    print("Docking clearance:", d.ship_clearance_status)
    print("Ship status:", s.ship_status)
    print("Dock status:", dk.dock_status)

    # Run leave_dock
    leave_dock(db, voyage)

    print("After leave_dock:")
    db.expire_all()
    d = db.query(Docking).filter(Docking.id == docking.id).first()
    s = db.query(Ship).filter(Ship.id == ship.id).first()
    dk = db.query(Dock).filter(Dock.id == dock.id).first()
    print("Docking departure_date:", d.departure_date)
    print("Docking clearance:", d.ship_clearance_status)
    print("Ship status:", s.ship_status)
    print("Dock status:", dk.dock_status)


if __name__ == '__main__':
    run_smoke_test()
