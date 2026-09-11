from typing import Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import app.enums as enums
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


# harbor schemas
class HarborBase(BaseModel):
    name: str
    timezone: str
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        value = value.strip()
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone name") from exc
        return value


class HarborRead(HarborBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class HarborUpdate(BaseModel):
    name: Optional[str] = None
    timezone: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone name") from exc
        return value


# dock schemas
class DockBase(BaseModel):
    dock_code: int
    dock_status: enums.DockStatus
    cargo_capacity: float = Field(..., ge=0)
    harbor_id: int
    dock_size: enums.VesselSize



class DockCreate(DockBase):
    dock_status: Optional[enums.DockStatus] = enums.DockStatus.ACTIVE


class DockRead(DockBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class DockUpdate(BaseModel):
    dock_code: Optional[int] = None
    dock_status: Optional[enums.DockStatus] = None
    cargo_capacity: Optional[float] = Field(None, ge=0)
    harbor_id: Optional[int] = None
    dock_size: Optional[enums.VesselSize] = None


# ship schemas
class ShipBase(BaseModel):
    ship_name: str
    current_cargo: float = Field(default=0, ge=0)
    registration_number: str
    ship_status: enums.ShipStatus
    cargo_capacity: float = Field(default=0, ge=0)
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
    current_cargo: Optional[float] = Field(None, ge=0)
    registration_number: Optional[str] = None
    ship_status: Optional[enums.ShipStatus] = None
    cargo_capacity: Optional[float] = Field(None, ge=0)
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
    estimated_arrival: Optional[datetime] = None
    arrival_date: Optional[datetime] = None
    travel_status: Optional[enums.VoyageStatus] = enums.VoyageStatus.SCHEDULED
    destination_harbor_id: int
    departure_harbor_id: int
    
    @model_validator(mode="after")
    def check_dates(self):
        departure_date = self.departure_date
        arrival_date = self.arrival_date
        departure_date = _as_utc(self.departure_date)
        arrival_date = _as_utc(self.arrival_date)
        estimated_arrival = _as_utc(self.estimated_arrival)
        if departure_date is not None and arrival_date is not None and arrival_date < departure_date:
            raise ValueError("arrival_date cannot be before departure_date")
        if departure_date is not None and estimated_arrival is not None and estimated_arrival < departure_date:
            raise ValueError("estimated_arrival cannot be before departure_date")
        return self


class VoyageCreate(VoyageBase):
    pass


class Updatedates(BaseModel):
    ship_id: Optional[int] = None
    departure_date: Optional[datetime] = None
    arrival_date: Optional[datetime] = None
    travel_status: Optional[enums.VoyageStatus] = None
    estimated_arrival: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def check_dates(self):
        departure_date = self.departure_date
        arrival_date = self.arrival_date
        departure_date = _as_utc(self.departure_date)
        arrival_date = _as_utc(self.arrival_date)
        estimated_arrival = _as_utc(self.estimated_arrival)
        if departure_date is not None and arrival_date is not None and arrival_date < departure_date:
            raise ValueError("arrival_date cannot be before departure_date")
        if departure_date is not None and estimated_arrival is not None and estimated_arrival < departure_date:
            raise ValueError("estimated_arrival cannot be before departure_date")
        return self


class VoyageArrivalUpdate(BaseModel):
    arrival_date: datetime


class VoyagePrediction(BaseModel):
    ship_id: int
    departure_harbor_id: int
    destination_harbor_id: int
    distance_km: float
    predicted_speed_kmh: float
    average_voyage_time_hours: float
    training_samples: int
    ship_training_samples: int
    model_trained: bool
    regression_model: str
    optimizer: str
    training_loss: Optional[float] = None
    epochs_run: int


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