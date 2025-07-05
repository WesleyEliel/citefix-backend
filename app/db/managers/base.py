from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel

from app.db.models.base import PyObjectId
from app.db.mongodb import get_db

ModelType = TypeVar('ModelType', bound=BaseModel)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


class DBManager:
    def __init__(self, collection_name: str, model: Type[ModelType]):
        self.collection_name = collection_name
        self._model = model

    def model(self, **kwargs):
        kwargs["_id"] = str(kwargs["_id"])
        return self._model(**kwargs)

    async def get_collection(self) -> AsyncIOMotorCollection:
        async with get_db() as db:
            return db[self.collection_name]

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        collection = await self.get_collection()
        obj_dict = obj_in.copy()
        if not isinstance(obj_in, dict):
            obj_dict = obj_in.dict()
        # if '_id' in obj_dict:
        #     obj_dict['_id'] = PyObjectId(obj_dict.pop('id'))
        result = await collection.insert_one(obj_dict)
        return await self.get(result.inserted_id)

    async def create_if_not_exists(
            self,
            filter: Dict[str, Any],
            obj_in: CreateSchemaType
    ) -> ModelType:
        collection = await self.get_collection()
        existing = await collection.find_one(filter)
        if existing:
            return self.model(**existing)
        return await self.create(obj_in)

    async def get_or_create(
            self,
            filter: Dict[str, Any],
            obj_in: CreateSchemaType
    ) -> tuple[ModelType, bool]:
        collection = await self.get_collection()
        existing = await collection.find_one(filter)
        if existing:
            return self.model(**existing), False
        created = await self.create(obj_in)
        return created, True

    async def bulk_create(self, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        collection = await self.get_collection()
        obj_dicts = [obj_in.dict() for obj_in in objs_in]
        for obj in obj_dicts:
            if 'id' in obj:
                obj['_id'] = PyObjectId(obj.pop('id'))
        result = await collection.insert_many(obj_dicts)
        return [await self.get(id) for id in result.inserted_ids]

    async def get(self, _id: Union[str, ObjectId]) -> Optional[ModelType]:
        collection = await self.get_collection()
        if isinstance(id, str):
            _id = PyObjectId(id)
        obj = await collection.find_one({"_id": _id})
        return self.model(**obj) if obj else None

    async def get_many(
            self,
            filter: Optional[Dict[str, Any]] = None,
            skip: int = 0,
            limit: int = 100,
            sort: Optional[List[tuple[str, int]]] = None
    ) -> List[ModelType]:
        collection = await self.get_collection()
        filter = filter or {}
        cursor = collection.find(filter).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        return [self.model(**obj) async for obj in cursor]

    async def get_by_field(
            self,
            field: str,
            value: Any,
            first_only: bool = True
    ) -> Union[Optional[ModelType], List[ModelType]]:
        collection = await self.get_collection()
        if first_only:
            obj = await collection.find_one({field: value})
            return self.model(**obj) if obj else None
        else:
            return [self.model(**obj) async for obj in collection.find({field: value})]

    async def update(
            self,
            _id: Union[str, PyObjectId],
            obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Optional[ModelType]:
        collection = await self.get_collection()
        if isinstance(_id, str):
            _id = PyObjectId(_id)

        if isinstance(obj_in, BaseModel):
            update_data = obj_in.dict(exclude_unset=True)
        else:
            update_data = obj_in

        if 'id' in update_data:
            del update_data['id']

        result = await collection.update_one(
            {"_id": _id},
            {"$set": update_data}
        )
        if result.modified_count:
            return await self.get(_id)
        return None

    async def bulk_update(
            self,
            filter: Dict[str, Any],
            update_data: Dict[str, Any]
    ) -> int:
        collection = await self.get_collection()
        result = await collection.update_many(
            filter,
            {"$set": update_data}
        )
        return result.modified_count

    async def delete(self, id: Union[str, ObjectId]) -> bool:
        collection = await self.get_collection()
        if isinstance(id, str):
            id = ObjectId(id)
        result = await collection.delete_one({"_id": id})
        return result.deleted_count > 0

    async def bulk_delete(self, filter: Dict[str, Any]) -> int:
        collection = await self.get_collection()
        result = await collection.delete_many(filter)
        return result.deleted_count

    async def count(self, filter: Optional[Dict[str, Any]] = None) -> int:
        collection = await self.get_collection()
        return await collection.count_documents(filter or {})

    async def exists(self, filter: Dict[str, Any]) -> bool:
        collection = await self.get_collection()
        return await collection.count_documents(filter) > 0

    async def find(self, filter: Dict = {}, limit: int = 100) -> List[Dict]:
        collection = await self.get_collection()
        cursor = collection.find(filter).limit(limit)
        return await cursor.to_list(length=limit)


def get_db_manager(collection_name: str, model: Type[ModelType]):
    return DBManager(collection_name, model)
