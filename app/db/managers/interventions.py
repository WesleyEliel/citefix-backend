from datetime import datetime
from typing import Optional, List

from app.db.managers.base import DBManager
from app.db.models.base import PyObjectId
from app.db.models.interventions import Intervention, InterventionCreate


class InterventionManager(DBManager):
    def __init__(self):
        super().__init__("interventions", Intervention)

    async def create_intervention(self, intervention: InterventionCreate) -> Intervention:
        intervention.progress = {
            "percentage": 0,
            "current_step": "",
            "steps": []
        }
        intervention.costs = {
            "materials": sum(item.cost for item in intervention.materials),
            "labor": 0,
            "transport": 0,
            "total": sum(item.cost for item in intervention.materials)
        }
        return await self.create(intervention)

    async def update_progress(
            self,
            intervention_id: str,
            percentage: int,
            current_step: str,
            steps: Optional[list] = None
    ) -> Optional[Intervention]:
        update_data = {
            "$set": {
                "progress.percentage": percentage,
                "progress.current_step": current_step
            }
        }
        if steps:
            update_data["$set"]["progress.steps"] = steps

        return await self.update(intervention_id, update_data)

    async def add_intervention_photo(
            self,
            intervention_id: str,
            photo_url: str,
            photo_type: str = "progress"
    ) -> Optional[Intervention]:
        return await self.update(
            intervention_id,
            {
                "$push": {
                    "photos": {
                        "type": photo_type,
                        "url": photo_url,
                        "taken_at": datetime.utcnow()
                    }
                }
            }
        )

    async def complete_step(
            self,
            intervention_id: str,
            step_name: str
    ) -> Optional[Intervention]:
        return await self.update(
            intervention_id,
            {
                "$push": {
                    "progress.steps": {
                        "name": step_name,
                        "completed": True,
                        "completed_at": datetime.utcnow()
                    }
                }
            }
        )

    async def assign_technicians(
            self,
            intervention_id: str,
            technician_ids: List[str],
            is_primary: bool = False
    ) -> Optional[Intervention]:
        return await self.update(
            intervention_id,
            {
                "$set": {
                    "technician_ids": [PyObjectId(tid) for tid in technician_ids],
                    "is_primary": is_primary
                }
            }
        )

    async def get_report_interventions(
            self,
            report_id: str,
            status: Optional[str] = None
    ) -> List[Intervention]:
        filters = {"report_id": PyObjectId(report_id)}
        if status:
            filters["status"] = status
        return await self.get_many(filters)

    async def get_technician_interventions(
            self,
            technician_id: str,
            status: Optional[str] = None
    ) -> List[Intervention]:
        filters = {"technician_ids": PyObjectId(technician_id)}
        if status:
            filters["status"] = status
        return await self.get_many(filters)


def get_intervention_manager() -> InterventionManager:
    return InterventionManager()
