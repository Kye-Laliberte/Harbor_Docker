from enum import Enum


class DockStatus(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    MAINTENANCE = 'maintenance'


class VesselSize(str, Enum):
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'


class ShipStatus(str, Enum):
    DOCKED = 'docked'
    SAILING = 'sailing'
    MAINTENANCE = 'maintenance'


class ShipClearanceStatus(str, Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    DENIED = 'denied'


class VoyageStatus(str, Enum):
    SCHEDULED = 'scheduled'
    DEPARTED = 'departed'
    ARRIVED = 'arrived'
    CANCELLED = 'cancelled'
