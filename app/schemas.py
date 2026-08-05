from email.policy import default

import app.enums as enums 
from pydantic import BaseModel, model_validator, root_validator, validator, field_validator, Field
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
    class Config:
            orm_mode = True

class DockUpdate(BaseModel):
    dock_code: Optional[int] = None
    dock_status: Optional[enums.DockStatus] = None
    dock_name: Optional[str] = None
    cargo_capacity: Optional[int] = Field(None, ge=0)
    harbor_id: Optional[int] = None
    dock_size: Optional[enums.VesselSize] = None
    



class ShipBase(BaseModel):
    ship_name: Optional[str] = "unknown ship"
    current_cargo: int = Field(0, ge=0)
    registration_number: str
    ship_status: Optional[enums.ShipStatus] = enums.ShipStatus.DOCKED
    cargo_capacity: int = Field(..., ge=0)
    ship_size: enums.VesselSize
    @field_validator("ship_name", "registration_number")
    @classmethod
    def normalize(cls, value: str) -> str:
        return value.strip().lower()

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
    current_cargo: Optional[int] = Field(None, ge=0)
    registration_number: Optional[str] = None
    ship_status: Optional[enums.ShipStatus] = None
    cargo_capacity: Optional[int]  = Field(None, ge=0)
    ship_size: Optional[enums.VesselSize]= None
    @field_validator("ship_name", "registration_number")
    @classmethod
    def normalizes(cls, value: str) -> str:
        return value.strip().lower()

    
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
