from enum import Enum, IntEnum


class DockStatus(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    MAINTENANCE = 'maintenance'


class VesselSize(IntEnum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3


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
