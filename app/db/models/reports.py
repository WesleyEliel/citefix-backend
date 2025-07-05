from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.db.models.base import PyObjectId, Location, TimestampModel


class ReportStatus(str, Enum):
    REPORTED = "REPORTED"
    VALIDATED = "VALIDATED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class ReportPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ReportCategory(str, Enum):
    LIGHTING = "LIGHTING"
    ROAD = "ROAD"
    WASTE = "WASTE"
    SAFETY = "SAFETY"
    OTHER = "OTHER"


class MediaItem(BaseModel):
    type: str  # "image" or "video"
    url: str
    thumbnail: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class ReportBase(BaseModel):
    title: str
    description: str
    category: ReportCategory
    priority: ReportPriority = ReportPriority.MEDIUM
    status: ReportStatus = ReportStatus.REPORTED


class ReportCreate(ReportBase):
    location: Location
    citizen_id: PyObjectId = None
    anonymous: bool = False


class Report(ReportBase, TimestampModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    location: Location
    citizen_id: PyObjectId
    media: List[MediaItem] = []
    engagement: dict = Field(default_factory=dict)
    assignment: Optional[dict] = None
    status_history: List[dict] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class ReportPublic(ReportBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    location: Location
    citizen_id: PyObjectId
    media: List[MediaItem]
    created_at: datetime


class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ReportCategory] = None
    priority: Optional[ReportPriority] = None
    status: Optional[ReportStatus] = None
    tags: Optional[List[str]] = None


class ReportSearch(BaseModel):
    category: Optional[ReportCategory] = None
    status: Optional[ReportStatus] = None
    priority: Optional[ReportPriority] = None
    zone: Optional[str] = None
    near_location: Optional[tuple[float, float]] = None  # (lat, lng)
    radius: Optional[float] = None  # in meters
