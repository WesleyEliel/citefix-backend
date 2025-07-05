from datetime import datetime
from typing import List, Optional

from fastapi import UploadFile, HTTPException

from app.api.v1.services.file import get_file_service
from app.db.managers.interventions import get_intervention_manager
from app.db.managers.reports import get_report_manager
from app.db.models.base import PyObjectId
from app.db.models.reports import Report, ReportPublic, ReportCreate, ReportUpdate
from app.db.models.reports import ReportSearch


class ReportService:
    def __init__(self):
        self.report_manager = get_report_manager()
        self.intervention_manager = get_intervention_manager()
        self.file_service = get_file_service()

    async def create_report(
            self,
            report_data: ReportCreate,
            citizen_id: str,
            media_files: Optional[List[UploadFile]] = None
    ) -> Report:
        report = await self.report_manager.create_report(report_data, citizen_id)

        if media_files:
            for media_file in media_files:
                media_url = await self.file_service.upload_report_attachment(
                    media_file,
                    report.id
                )
                await self.report_manager.add_media_to_report(
                    str(report.id),
                    {
                        "type": "image",
                        "url": media_url,
                        "uploaded_at": datetime.utcnow()
                    }
                )

        return report

    async def get_report(self, report_id: str) -> Optional[ReportPublic]:
        return await self.report_manager.get(report_id)

    async def update_report(
            self,
            report_id: str,
            update_data: ReportUpdate,
            user_id: str
    ) -> Optional[Report]:
        if update_data.status:
            return await self.report_manager.update_report_status(
                report_id,
                update_data.status,
                user_id
            )
        return await self.report_manager.update(report_id, update_data.dict(exclude_unset=True))

    async def search_reports(self, search: ReportSearch) -> List[Report]:
        return await self.report_manager.search_reports(search)

    async def add_media(
            self,
            report_id: str,
            media_file: UploadFile
    ) -> Optional[Report]:
        media_url = await self.file_service.upload_report_attachment(media_file, PyObjectId(report_id))
        return await self.report_manager.add_media_to_report(
            report_id,
            {
                "type": "image",
                "url": media_url,
                "uploaded_at": datetime.utcnow()
            }
        )

    async def get_report_with_interventions(self, report_id: str) -> dict:
        """Get report with all its interventions"""
        report = await self.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        interventions = await self.intervention_manager.get_report_interventions(report_id)
        return {
            "report": report,
            "interventions": interventions
        }

    async def increment_views(self, report_id: str) -> Optional[Report]:
        return await self.report_manager.increment_engagement(report_id, "views")


def get_report_service() -> ReportService:
    return ReportService()
