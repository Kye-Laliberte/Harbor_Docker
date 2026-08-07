from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.dependencies import get_db
from app.models import Ship
from app.schemas import ShipCreate, ShipUpdate, ShipRead
from app.enums import ShipStatus,VesselSize
router = APIRouter(prefix="/ships", tags=["ships"])


@router.get("/list", response_model=list[ShipRead])
def list_ships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Ship).offset(skip).limit(limit).all()


@router.post("/new", response_model=ShipRead, status_code=status.HTTP_201_CREATED)
def add_ship(payload: ShipCreate, db: Session = Depends(get_db)):
    if payload.cargo_capacity < payload.current_cargo:
        raise HTTPException(status_code=400, detail="Current cargo cannot exceed cargo capacity")

    ship = Ship(**payload.model_dump())
    db.add(ship)
    db.commit()
    db.refresh(ship)
    return ship


@router.get("/{ship_id}/get", response_model=ShipRead)
def get_ship(ship_id: int, db: Session = Depends(get_db)):
    ship = db.query(Ship).filter(Ship.id == ship_id).first()
    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")
    return ship


@router.put("/{ship_id}/update", response_model=ShipRead)
def update_ship(ship_id: int, payload: ShipUpdate, db: Session = Depends(get_db)):
    ship = db.query(Ship).filter(Ship.id == ship_id).first()
    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ship, field, value)

    db.commit()
    db.refresh(ship)
    return ship


@router.delete("/{ship_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_ship(ship_id: int, db: Session = Depends(get_db)):
    ship = db.query(Ship).filter(Ship.id == ship_id).first()
    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    db.delete(ship)
    db.commit()
    return None
