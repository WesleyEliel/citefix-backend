from typing import List, Optional

from app.db.managers.users import get_user_manager
from app.db.models.base import PyObjectId
from app.db.models.users import UserPublic, UserSearch, UserUpdate


class UserService:
    def __init__(self):
        self.user_manager = get_user_manager()

    async def get_user_by_id(self, user_id: PyObjectId) -> Optional[UserPublic]:
        return await self.user_manager.get(user_id)

    async def get_user_by_email(self, email: str) -> Optional[UserPublic]:
        return await self.user_manager.get_by_email(email)

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserPublic]:
        return await self.user_manager.get_many({}, skip=skip, limit=limit)

    async def search_users(self, search_params: UserSearch) -> List[UserPublic]:
        filters = {}
        if search_params.query:
            filters["$or"] = [
                {"email": {"$regex": search_params.query, "$options": "i"}},
                {"username": {"$regex": search_params.query, "$options": "i"}},
                {"full_name": {"$regex": search_params.query, "$options": "i"}}
            ]
        if search_params.role:
            filters["role"] = search_params.role
        if search_params.status:
            filters["status"] = search_params.status

        return await self.user_manager.get_many(filters)

    async def update_user(self, user_id: PyObjectId, update_data: UserUpdate) -> UserPublic:
        # Remove None values to avoid overwriting with null
        update_data = {k: v for k, v in update_data.dict().items() if v is not None}
        return await self.user_manager.update(user_id, update_data)

    async def delete_user(self, user_id: PyObjectId) -> bool:
        return await self.user_manager.delete(user_id)

    # Todo

    async def update_user_stats(
            self,
            user_id: PyObjectId,
            stats_update: dict
    ) -> UserPublic:
        """Update user statistics (reportsCount, confirmationsCount, etc.)"""
        update_data = {}
        for stat, value in stats_update.items():
            update_data[f"stats.{stat}"] = value

        return await self.user_manager.update(user_id, {"$inc": update_data})

    async def update_technician_availability(
            self,
            user_id: PyObjectId,
            availability: str
    ) -> UserPublic:
        """Update technician availability status"""
        return await self.user_manager.update(
            user_id,
            {"technician.availability": availability}
        )

    async def get_active_reporting_users(self, skip: int = 0, limit: int = 100) -> List[UserPublic]:
        """
        Get active users who have created reports
        """
        # First get users who have reports
        collection = await self.user_manager.get_collection()

        reporting_users = collection.aggregate([
            {
                "$lookup": {
                    "from": "reports",
                    "localField": "_id",
                    "foreignField": "citizen_id",
                    "as": "reports"
                }
            },
            {
                "$match": {
                    "status": "active",
                    "reports": {"$ne": []}
                }
            },
            {
                "$addFields": {
                    "report_count": {"$size": "$reports"}
                }
            },
            {"$skip": skip},
            {"$limit": limit}
        ]).to_list(length=None)
        print(reporting_users, 14414)

        return [UserPublic(**user) for user in reporting_users]
