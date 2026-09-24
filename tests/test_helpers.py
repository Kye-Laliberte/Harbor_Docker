from app.models import Base, Harbor, Dock, Ship, Docking
import app.enums as enums

def create_sample_harbor(db, name="Test Harbor"):
    harbor = Harbor(
        name=name,
        timezone="UTC",
        latitude=10.0,
        longitude=20.0)
    
    db.add(harbor)
    db.commit()
    db.refresh(harbor)
    return harbor

def create_sample_dock(db, harbor_id,size=enums.VesselSize.MEDIUM, active=enums.DockStatus.ACTIVE):
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
        ship_id=ship_id,
        dock_id=dock_id,
        arrival_time="2024-01-01T00:00:00",
        purpose = "first docking",
        departure_time=None,
        ship_clearance_status = enums.ShipClearanceStatus.APPROVED)
    
    db.add(docking)
    db.commit()
    db.refresh(docking)
    return docking