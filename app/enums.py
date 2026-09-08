from enum import Enum


class SessionStatus(str, Enum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class InteractionType(str, Enum):
    CLICK = "CLICK"
    SCROLL = "SCROLL"
    TYPE = "TYPE"
    BACK = "BACK"
    SWIPE = "SWIPE"


class IssueType(str, Enum):
    PERFORMANCE = "PERFORMANCE"
    MEMORY = "MEMORY"
    BATTERY = "BATTERY"
    CPU = "CPU"
    TEMPERATURE = "TEMPERATURE"
    FRAME_DROP = "FRAME_DROP"
    UI = "UI"
    CRASH = "CRASH"
    ANOMALY = "ANOMALY"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
