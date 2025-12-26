from enum import Enum

class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    SALESPERSON = "SALESPERSON"

class CallStatusEnum(str, Enum):
    OPEN = "OPEN"
    OVERDUE = "OVERDUE"
    CLOSED = "CLOSED"