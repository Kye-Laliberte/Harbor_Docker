from app.models import  Ship, Docking,Voyage
from datetime import datetime, timezone
import app.enums as enums
from sqlalchemy import text


def authenticated_client(app):
    from fastapi.testclient import TestClient
    from app.core.config import settings

    settings.API_KEY = "test-api-key"
    return TestClient(app, headers={"X-API-Key": settings.API_KEY})

def create_ship(db, name="Test Ship", status=enums.ShipStatus.DOCKED, cargo_capacity=500 ,cargo=1, ship_size=enums.VesselSize.SMALL):
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
    
    return ship

def get_ship_stat(db,ship_id):
    ship_status = db.execute(text("SELECT ship_status from ships WHERE id = :ship_id "),
                             {"ship_id":ship_id}).scalar_one()
    if ship_status:
        return ship_status
