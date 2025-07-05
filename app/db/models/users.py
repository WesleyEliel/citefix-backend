from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.db.models.base import PyObjectId, TimestampModel, Location


class UserRole(str, Enum):
    CITIZEN = "CITIZEN"
    TECHNICIAN = "TECHNICIAN"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"


class UserBase(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    phone: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    preferences: Optional[dict] = None
    role: UserRole = UserRole.CITIZEN
    status: UserStatus = UserStatus.ACTIVE  # "active", "inactive", "suspended", "pending"

    @property
    def full_name(self):
        return f"{self.firstname} {self.lastname}"

    @property
    def is_active(self):
        return self.status == UserStatus.ACTIVE

    @property
    def is_verified(self):
        return self.status in [UserStatus.ACTIVE, UserStatus.SUSPENDED]

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "name": "Fatou Diarra",
                "email": "fatou.diarra@email.com",
                "phone": "+229 XX XX XX XX",
                "role": "citizen",
                "status": "active"
            }
        }


class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str


class UserPublic(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    _id: str


class UserCreate(UserBase):
    password: str


class UserCreateInDB(UserBase):
    hashed_password: str


class UserUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    preferences: Optional[dict] = None
    hashed_password: str = None


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    status: UserStatus


class UserSearch(BaseModel):
    query: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    zone: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class User(UserPublic, TimestampModel):
    location: Optional[Location] = None
    profile: Optional[dict] = None
    stats: Optional[dict] = None
    technician: Optional[dict] = None
    security: Optional[dict] = None
    last_active: Optional[datetime] = None
    report_count: int = 0
