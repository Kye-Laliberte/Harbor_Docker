from email.policy import default
from typing import Optional
from datetime import datetime

import app.enums as enums
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# harbor schemas
class HarborBase(BaseModel):
    name: str
    timezone: datetime

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip().lower()


class HarborRead(HarborBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class HarborCreate(HarborBase):
    pass


class HarborUpdate(BaseModel):
    name: Optional[str] = None
    timezone: Optional[datetime] = None


# dock schemas
class DockBase(BaseModel):
    dock_code: int
    dock_status: enums.DockStatus
    #dock_name: str
    cargo_capacity: int = Field(..., ge=0)
    harbor_id: int
    dock_size: enums.VesselSize

    """@field_validator("dock_name")
    @classmethod
    def normalize(cls, value: str) -> str:
        return value.strip().lower()"""


class DockCreate(DockBase):
    dock_status: Optional[enums.DockStatus] = enums.DockStatus.ACTIVE


class DockRead(DockBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class DockUpdate(BaseModel):
    dock_code: Optional[int] = None
    dock_status: Optional[enums.DockStatus] = None
    cargo_capacity: Optional[int] = Field(None, ge=0)
    harbor_id: Optional[int] = None
    dock_size: Optional[enums.VesselSize] = None


# ship schemas
class ShipBase(BaseModel):
    ship_name: str
    current_cargo: int = Field(default=0, ge=0)
    registration_number: str
    ship_status: enums.ShipStatus
    cargo_capacity: int = Field(default=0, ge=0)
    ship_size: enums.VesselSize

    @field_validator("ship_name", "registration_number")
    @classmethod
    def normalize(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def check_cargo_vs_capacity(self):
        if self.current_cargo is not None and self.cargo_capacity is not None:
            if self.current_cargo > self.cargo_capacity:
                raise ValueError("current_cargo cannot exceed cargo_capacity")
        return self


class ShipCreate(ShipBase):
    ship_name: str = "unknown ship"
    ship_status: Optional[enums.ShipStatus] = enums.ShipStatus.DOCKED


class ShipUpdate(BaseModel):
    ship_name: Optional[str] = None
    current_cargo: Optional[int] = Field(None, ge=0)
    registration_number: Optional[str] = None
    ship_status: Optional[enums.ShipStatus] = None
    cargo_capacity: Optional[int] = Field(None, ge=0)
    ship_size: Optional[enums.VesselSize] = None

    @field_validator("ship_name", "registration_number")
    @classmethod
    def normalizes(cls, value: str) -> str:
        return value.strip().lower()


class ShipRead(ShipBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# voyage schemas
class VoyageBase(BaseModel):
    ship_id: int
    departure_date: Optional[datetime] = None
    estimated_arrival: datetime
    arrival_date: Optional[datetime] = None
    travel_status: Optional[enums.VoyageStatus] = enums.VoyageStatus.SCHEDULED
    destination_harbor_id: Optional[int] = None
    departure_harbor_id: int
    

    @model_validator(mode="after")
    def check_dates(self):
        departure_date = self.departure_date
        arrival_date = self.arrival_date
        if departure_date and arrival_date:
            if arrival_date < departure_date:
                raise ValueError("arrival_date must be after departure_date")
        return self


class VoyageCreate(VoyageBase):
    pass


class Updatedates(BaseModel):
    ship_id: int
    departure_date: Optional[datetime] = None
    arrival_date: Optional[datetime] = None
    travel_status: Optional[enums.VoyageStatus] = None
    estimated_arrival: datetime
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def check_dates(self):
        departure_date = self.departure_date
        arrival_date = self.arrival_date
        if departure_date is not None and arrival_date is not None:
            if arrival_date < departure_date:
                raise ValueError("arrival_date must be after departure_date")
        return self


class VoyageRead(VoyageBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class DockingBase(BaseModel):
    ship_id: int
    dock_id: int
    arrival_date: datetime
    departure_date: Optional[datetime] = None
    ship_clearance_status: enums.ShipClearanceStatus
    purpose: Optional[str] = None
    

    @model_validator(mode="after")
    def check_dates(self):
        if self.departure_date:
            if self.departure_date < self.arrival_date:
                raise ValueError("departure_date must be after arrival_date")
        return self


class DockingCreate(DockingBase):
    ship_clearance_status: Optional[enums.ShipClearanceStatus] = enums.ShipClearanceStatus.PENDING
   

class DockingUpdate(BaseModel):
    dock_id: Optional[int] = None
    arrival_date: Optional[datetime] = None
    departure_date: Optional[datetime] = None
    ship_clearance_status: Optional[enums.ShipClearanceStatus] = None
    purpose: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def check_dates(self):
        if self.arrival_date and self.departure_date:
            if self.departure_date < self.arrival_date:
                raise ValueError("departure_date must be after arrival_date")
        return self


class DockingRead(DockingBase):
    id: int
    model_config = ConfigDict(from_attributes=True)