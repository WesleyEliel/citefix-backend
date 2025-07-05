from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.db.models.base import PyObjectId, TimestampModel


class InterventionStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    SUCCESSED = "SUCCESSED"


class MaterialItem(BaseModel):
    name: str
    quantity: float
    unit: str
    cost: float  # in local currency


class InterventionStep(BaseModel):
    name: str
    completed: bool = False
    completed_at: Optional[datetime] = None


class InterventionBase(BaseModel):
    report_id: PyObjectId
    technician_ids: List[PyObjectId]  # Changed from single technician_id to list
    title: str
    description: str
    status: InterventionStatus = InterventionStatus.SCHEDULED
    priority: str
    is_primary: bool = False


class InterventionCreate(InterventionBase):
    materials: List[MaterialItem] = []
    estimated_duration: int  # in minutes


class Intervention(InterventionBase, TimestampModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    materials: List[MaterialItem] = []
    scheduling: dict = Field(default_factory=dict)
    progress: dict = Field(default_factory=dict)
    photos: List[dict] = Field(default_factory=list)
    costs: dict = Field(default_factory=dict)
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class InterventionPublic(InterventionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    materials: List[MaterialItem]
    progress: dict
    created_at: datetime


class InterventionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[InterventionStatus] = None
    notes: Optional[str] = None
