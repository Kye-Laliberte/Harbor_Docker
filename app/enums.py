from enum import Enum


class DockStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    MAINTENANCE = 'maintenance'


class VesselSize(Enum):
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'


class ShipStatus(Enum):
    DOCKED = 'docked'
    SAILING = 'sailing'
    MAINTENANCE = 'maintenance'


class ShipClearanceStatus(Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    DENIED = 'denied'


class VoyageStatus(Enum):
    SCHEDULED = 'scheduled'
    DEPARTED = 'departed'
    ARRIVED = 'arrived'
    CANCELLED = 'cancelled'
