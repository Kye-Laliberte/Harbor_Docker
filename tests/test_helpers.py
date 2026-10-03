from app.models import Base, Harbor, Dock, Ship, Docking,Voyage
from datetime import datetime, timezone
import app.enums as enums
from sqlalchemy import create_engine,text


def authenticated_client(app):
    from fastapi.testclient import TestClient
    from app.core.config import settings

    settings.API_KEY = "test-api-key"
    return TestClient(app, headers={"X-API-Key": settings.API_KEY})


def create_sample_harbor(db, name="Test Harbor",lat=10.0, long =20.0):
    harbor = Harbor(
        name=name,
        timezone="UTC",
        latitude=lat,
        longitude=long)
    
    db.add(harbor)
    db.commit()
    db.refresh(harbor)
    return harbor

def create_sample_dock(db, harbor_id,size=enums.VesselSize.SMALL, active=enums.DockStatus.ACTIVE):
    dock = Dock(
        dock_code = str(harbor_id),
        harbor_id=harbor_id,
        dock_size=size,
        dock_status=active,
        cargo_capacity = size*1000)

    db.add(dock)
    db.commit()
    db.refresh(dock)
    return dock

def create_ship(db, name="Test Ship", status=enums.ShipStatus.DOCKED, cargo_capacity=500 ,cargo=1, ship_size=enums.VesselSize.SMALL,dock_id=None):
    ship = Ship(
        ship_name=name,
        current_cargo = cargo,
        ship_status= status,
        registration_number = name,
        cargo_capacity = cargo_capacity,
        ship_size = ship_size)
    
    db.add(ship)
    db.commit()
    db.refresh(ship)
    if dock_id is not None:
        dock_ship(db,ship.id,dock_id)# add first doc
    return ship

def dock_ship(db, ship_id, dock_id):
    docking = Docking(
        ship_id = ship_id,
        dock_id = dock_id,
        arrival_date = datetime(2026, 4, 1, tzinfo=timezone.utc),
        purpose = "first docking",
        departure_date = None,
        ship_clearance_status = enums.ShipClearanceStatus.APPROVED)
    
    db.add(docking)
    db.commit()
    db.refresh(docking)
    return docking

def get_dock_stat(db,dock_id):
    dock_stat = db.execute(text("SELECT dock_status FROM docks WHERE id = :dock_id"),
                           {"dock_id": dock_id},).scalar_one()
    if dock_stat: 
        return dock_stat
    
def get_ship_stat(db,ship_id):
    ship_status = db.execute(text("SELECT ship_status from ships WHERE id = :ship_id "),
                             {"ship_id":ship_id}).scalar_one()
    if ship_status:
        return ship_status

def create_voyage(db, ship_id, origin_id, dest_id):
    voyage = Voyage(
        ship_id=ship_id,
        departure_harbor_id=origin_id,
        destination_harbor_id=dest_id,
        scheduled_departure="2024-01-01T00:00:00",
        arrival_date=None,
        departure_date=None,
        voyage_status=enums.VoyageStatus.SCHEDULED
    )
    db.add(voyage)
    db.commit()
    db.refresh(voyage)
    return voyage