from datetime import datetime
from typing import Optional, Any

from bson import ObjectId
from pydantic import (
    BaseModel,
    Field,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
            cls,
            source_type: Any,
            handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v: Any) -> str:
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            try:
                ObjectId(v)
                return v
            except Exception:
                pass
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(
            cls,
            core_schema: core_schema.CoreSchema,
            handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string", "format": "objectid"}


class TimestampModel(BaseModel):
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class Location(BaseModel):
    address: str
    coordinates: dict  # GeoJSON format
    zone: str
    landmark: Optional[str] = None
