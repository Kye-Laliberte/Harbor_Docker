from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, Enum
from  sqlalchemy.orm import backref, relationship, declarative_base
from datetime import datetime
from app.database import Base


class  Dock(Base):
    __tablename__ = 'docks'
    id = Column(Integer, primary_key=True, index=True)
    dock_code = Column(Integer, unique=True, nullable=False)
    port_name = Column(String(100), nullable=False)
    harbor_id = Column(Integer, ForeignKey('harbors.id'), nullable=False)
    dock_status = Column(Enum('active', 'inactive', 'maintenance', name='dock_status_enum'), default='active', nullable=False)
    harbor = relationship("Harbor", back_populates="docks")
    cargo_capacity = Column(Integer, CheckConstraint('cargo_capacity >= 0'), nullable=False)

class Captain(Base):
    __tablename__ = 'captains'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), default='Unknown Captain', nullable=False)
    experience_years = Column(Integer, CheckConstraint('experience_years >= 0'), default=0, nullable=False)

class Ship(Base):
    __tablename__ = 'ships'
    id = Column(Integer, primary_key=True, index=True)
    ship_name = Column(String(100), default='Unknown Ship', nullable=False)
    captain_id = Column(Integer, ForeignKey('captains.id'), nullable=False)
    cargo_size = Column(Integer, CheckConstraint('cargo_size >= 0'), nullable=False)
    registration_number = Column(String(100), unique=True, nullable=False)
    ship_status = Column(Enum('docked', 'sailing', 'maintenance', name='ship_status_enum'), default='docked', nullable=False)
    captain = relationship("Captain", backref="ships")
    cargo_capacity = Column(Integer, CheckConstraint('cargo_capacity >= 0'), nullable=False)
    total_cargo = Column(Integer, CheckConstraint('total_cargo >= 0'), nullable=False)

class Docking(Base):
    __tablename__ = 'dockings'
    __table_args__ = (
        CheckConstraint('departure_date IS NULL OR departure_date >= arrival_date', name='check_departure_after_arrival'),
        Enum('ship_clearance_status_enum', 'pending', 'approved', 'denied', name='ship_clearance_status_enum')
    )

    id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(Integer, ForeignKey('ships.id'), nullable=False)
    dock_id = Column(Integer, ForeignKey('docks.id'), nullable=False)
    arrival_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    departure_date = Column(DateTime, CheckConstraint('departure_date IS NULL OR departure_date >= arrival_date'), nullable=True)
    ship_clearance_status = Column(Enum('pending', 'approved', 'denied', name='ship_clearance_status_enum'), default='pending', nullable=False)
    purpose = Column(String(200), nullable=True)

    ship = relationship("Ship", backref="dockings")
    dock = relationship("Dock", backref="dockings")

class Harbor(Base):
    __tablename__ = 'harbors'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    harbor_status = Column(Enum('active', 'inactive', name='harbor_status_enum'),default='active', nullable=False)
    dock_count = Column(Integer, CheckConstraint('dock_count >= 0'), default=0, nullable=False)