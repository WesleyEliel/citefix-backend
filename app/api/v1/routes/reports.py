from typing import List

# from app.services.report import ReportService, get_report_service
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from app.api.deps import get_current_active_user
from app.api.v1.routes.utils import response_helper
from app.api.v1.services.services import ReportService, get_report_service
from app.db.models.reports import (
    ReportCreate,
    ReportPublic,
    ReportUpdate,
    ReportSearch
)
from app.db.models.users import UserPublic

router = APIRouter()


@router.post("/", response_model=ReportPublic)
async def create_report(
        report_create: ReportCreate,
        # media_files: Optional[List[UploadFile]] = File(None),
        current_user: UserPublic = Depends(get_current_active_user),
        report_service: ReportService = Depends(get_report_service)
):
    """Create a new report"""
    report = await report_service.create_report(
        report_create,
        str(current_user.id),
        # media_files
    )
    return response_helper(report)


@router.get("/{report_id}", response_model=ReportPublic)
async def get_report(
        report_id: str,
        report_service: ReportService = Depends(get_report_service)
):
    """Get a specific report"""
    report = await report_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Track view count
    await report_service.increment_views(report_id)
    return report


@router.put("/{report_id}", response_model=ReportPublic)
async def update_report(
        report_id: str,
        update_data: ReportUpdate,
        current_user: UserPublic = Depends(get_current_active_user),
        report_service: ReportService = Depends(get_report_service)
):
    """Update a report"""
    report = await report_service.update_report(
        report_id,
        update_data,
        str(current_user.id)
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/search", response_model=List[ReportPublic])
async def search_reports(
        search: ReportSearch,
        # Todo: Check this usage to make pagination
        # skip: int = 0,
        # limit: int = 100,
        report_service: ReportService = Depends(get_report_service)
):
    """Search reports with filters"""
    return await report_service.search_reports(search)


@router.post("/{report_id}/media", response_model=ReportPublic)
async def add_report_media(
        report_id: str,
        media_file: UploadFile = File(...),
        # current_user: UserPublic = Depends(get_current_active_user),
        report_service: ReportService = Depends(get_report_service)
):
    """Add media to a report"""
    # Todo: make checks on the current_user that is adding media to report
    report = await report_service.add_media(report_id, media_file)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/{report_id}/confirm")
async def confirm_report(
        report_id: str,
        # current_user: UserPublic = Depends(get_current_active_user),
        report_service: ReportService = Depends(get_report_service)
):
    """Confirm a report (community validation)"""
    # Todo: make checks on the current_user that is adding media to report
    report = await report_service.increment_views(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report confirmed"}
