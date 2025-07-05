from datetime import datetime
from typing import List, Optional

from app.db.managers.base import DBManager
from app.db.models.base import PyObjectId
from app.db.models.reports import Report, ReportCreate, ReportSearch


class ReportManager(DBManager):
    def __init__(self):
        super().__init__("reports", Report)

    async def create_report(self, report: ReportCreate, citizen_id: str) -> Report:
        if not report.citizen_id:
            report.citizen_id = PyObjectId(citizen_id)
        return await self.create(report)

    async def update_report_status(
            self,
            report_id: str,
            new_status: str,
            user_id: str,
            comment: Optional[str] = None
    ) -> Optional[Report]:
        update_data = {
            "$set": {"status": new_status},
            "$push": {
                "status_history": {
                    "status": new_status,
                    "date": datetime.utcnow(),
                    "userId": PyObjectId(user_id),
                    "comment": comment or ""
                }
            }
        }
        return await self.update(report_id, update_data)

    async def add_media_to_report(self, report_id: str, media_item: dict) -> Optional[Report]:
        return await self.update(report_id, {"$push": {"media": media_item}})

    async def search_reports(self, search: ReportSearch, skip: int = 0, limit: int = 100) -> List[Report]:
        filters = {}

        if search.category:
            filters["category"] = search.category
        if search.status:
            filters["status"] = search.status
        if search.priority:
            filters["priority"] = search.priority
        if search.zone:
            filters["location.zone"] = search.zone
        if search.near_location and search.radius:
            lat, lng = search.near_location
            filters["location.coordinates"] = {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "$maxDistance": search.radius
                }
            }

        return await self.get_many(filters, skip=skip, limit=limit)

    async def increment_engagement(
            self,
            report_id: str,
            field: str,
            amount: int = 1
    ) -> Optional[Report]:
        return await self.update(
            report_id,
            {"$inc": {f"engagement.{field}": amount}}
        )


def get_report_manager() -> ReportManager:
    return ReportManager()
