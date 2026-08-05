import app.enums as enums 
from pydantic import BaseModel, model_validator, root_validator, validator, Field
from typing import Optional 
from datetime import datetime

class HarborBase(BaseModel):
    name: str
    timezone: datetime
    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip().lower()

class HarborRead(HarborBase):
    id: int
    class Config:
        from_attributes = True

class HarborUpdate(BaseModel):
    name: Optional[str] = None
    timezone: Optional[datetime] = None 


class DockBase(BaseModel):
    dock_code: int
    dock_status: Optional[enums.DockStatus] = enums.DockStatus.ACTIVE
    dock_name: str
    cargo_capacity: int = Field(..., ge=0)
    harbor_id:int
    dock_size: enums.VesselSize
    @field_validator("dock_name")
    @classmethod
    def normalize(cls, value: str) -> str:
        return value.strip().lower()

class DockRead(DockBase):
    id:int
    



class ShipBase(BaseModel):
    ship_name: Optional[str] = "unknown ship"
    current_cargo: int = 0
    registration_number: str
    ship_status: Optional[enums.ShipStatus] = enums.ShipStatus.DOCKED
    cargo_capacity: int
    ship_size: enums.VesselSize

    @validator("current_cargo", "cargo_capacity")
    def non_negative(cls, v):
        if v is None:
            return v
        if v < 0:
            raise ValueError("must be >= 0")
        return v

    @model_validator(mode="after")
    def check_cargo_vs_capacity(self):
        current = self.get("current_cargo")
        capacity = self.get("cargo_capacity")
        if current is not None and capacity is not None:
            if current > capacity:
                raise ValueError("current_cargo cannot exceed cargo_capacity")
        return self


class ShipCreate(ShipBase):
    pass

class ShipUpdate(BaseModel):
    ship_name: Optional[str] =None
    current_cargo: Optional[int] = None
    registration_number: Optional[str] = None
    ship_status: Optional[enums.ShipStatus] = None
    cargo_capacity: Optional[int] = None
    ship_size: Optional[enums.VesselSize]= None
    @field_validator("ship_name", "registration_number")
    @classmethod
    def normalizes(cls, value: str) -> str:
        return value.strip().lower()

    @validator("current_cargo", "cargo_capacity")
    def non_negative(cls, v):
        if v is None:
            return v
        if v < 0:
            raise ValueError("must be >= 0")
        return v
    
    @model_validator(mode="after")
    def check_cargo_vs_capacity(self):
        current = self.get("current_cargo")
        capacity = self.get("cargo_capacity")
        if current is not None and capacity is not None:
            if current > capacity:
                raise ValueError("current_cargo cannot exceed cargo_capacity")
        return self

class ShipOut(ShipBase):
    id: int

    class Config:
        orm_mode = True
