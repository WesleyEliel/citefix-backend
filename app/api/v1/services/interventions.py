from typing import Optional, List

from fastapi import UploadFile

from app.api.v1.services.file import get_file_service
from app.db.managers.interventions import get_intervention_manager
from app.db.managers.reports import get_report_manager
from app.db.models.interventions import Intervention, InterventionPublic, InterventionCreate


class InterventionService:
    def __init__(self):
        self.intervention_manager = get_intervention_manager()
        self.report_manager = get_report_manager()
        self.file_service = get_file_service()

    async def create_intervention(
            self,
            intervention_data: InterventionCreate
    ) -> Intervention:
        # Convert single technician_id to list for backward compatibility
        if not isinstance(intervention_data.technician_ids, list):
            intervention_data.technician_ids = [intervention_data.technician_ids]

        # Update report status to "assigned" if first intervention
        existing_interventions = await self.intervention_manager.get_report_interventions(
            str(intervention_data.report_id)
        )

        if not existing_interventions:
            await self.report_manager.update_report_status(
                str(intervention_data.report_id),
                "assigned",
                str(intervention_data.technician_ids[0]),
                "Initial intervention created"
            )

        return await self.intervention_manager.create_intervention(intervention_data)

    async def get_intervention(self, intervention_id: str) -> Optional[InterventionPublic]:
        return await self.intervention_manager.get(intervention_id)

    async def update_intervention_status(
            self,
            intervention_id: str,
            new_status: str,
            report_id: str,
            user_id: str
    ) -> Optional[Intervention]:
        intervention = await self.intervention_manager.update(
            intervention_id,
            {"status": new_status}
        )

        if new_status == "in_progress":
            report_status = "in_progress"
        elif new_status == "completed":
            report_status = "resolved"
        else:
            report_status = "assigned"

        await self.report_manager.update_report_status(
            report_id,
            report_status,
            user_id,
            f"Intervention status changed to {new_status}"
        )

        return intervention

    async def add_intervention_photo(
            self,
            intervention_id: str,
            photo_file: UploadFile,
            photo_type: str = "progress"
    ) -> Optional[Intervention]:
        intervention = await self.intervention_manager.get(intervention_id)

        photo_url = await self.file_service.upload_report_attachment(
            photo_file,
            report_id=intervention.report_id
        )
        return await self.intervention_manager.add_intervention_photo(
            intervention_id,
            photo_url,
            photo_type
        )

    async def complete_intervention_step(
            self,
            intervention_id: str,
            step_name: str
    ) -> Optional[Intervention]:
        return await self.intervention_manager.complete_step(
            intervention_id,
            step_name
        )

    async def complete_intervention(
            self,
            intervention_id: str,
            report_id: str,
            user_id: str
    ) -> Optional[Intervention]:
        # Mark intervention as completed
        intervention = await self.intervention_manager.update(
            intervention_id,
            {"status": "completed"}
        )

        # Check if all interventions are completed
        all_interventions = await self.intervention_manager.get_report_interventions(report_id)
        completed_interventions = [i for i in all_interventions if i.status == "completed"]

        if len(completed_interventions) == len(all_interventions):
            # All interventions completed, mark report as resolved
            await self.report_manager.update_report_status(
                report_id,
                "resolved",
                user_id,
                "All interventions completed"
            )

        return intervention

    async def assign_technicians_to_intervention(
            self,
            intervention_id: str,
            technician_ids: List[str],
            is_primary: bool = False
    ) -> Optional[Intervention]:
        return await self.intervention_manager.assign_technicians(
            intervention_id,
            technician_ids,
            is_primary
        )


def get_intervention_service() -> InterventionService:
    return InterventionService()
