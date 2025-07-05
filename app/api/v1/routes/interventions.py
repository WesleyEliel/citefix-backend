from typing import Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from app.api.deps import get_current_active_user
from app.api.v1.services.interventions import InterventionService, get_intervention_service
from app.db.models.base import PyObjectId
from app.db.models.interventions import (
    InterventionCreate,
    InterventionPublic,
    InterventionUpdate
)
from app.db.models.users import UserInDB

router = APIRouter()


@router.post("/", response_model=InterventionPublic)
async def create_intervention(
        intervention_data: InterventionCreate,
        current_user: UserInDB = Depends(get_current_active_user),
        intervention_service: InterventionService = Depends(get_intervention_service)
):
    """Create a new intervention (admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create interventions"
        )

    return await intervention_service.create_intervention(intervention_data)


@router.get("/{intervention_id}", response_model=InterventionPublic)
async def get_intervention(
        intervention_id: str,
        intervention_service: InterventionService = Depends(get_intervention_service)
):
    """Get intervention details"""
    intervention = await intervention_service.get_intervention(intervention_id)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return intervention


@router.put("/{intervention_id}/status", response_model=InterventionPublic)
async def update_intervention_status(
        intervention_id: str,
        report_id: str,
        new_status: str,
        current_user: UserInDB = Depends(get_current_active_user),
        intervention_service: InterventionService = Depends(get_intervention_service)
):
    """Update intervention status (technician only)"""
    return await intervention_service.update_intervention_status(
        intervention_id,
        report_id,
        new_status,
        str(current_user.id)
    )


@router.post("/{intervention_id}/photos", response_model=InterventionPublic)
async def add_intervention_photo(
        intervention_id: str,
        photo: UploadFile = File(...),
        photo_type: str = "progress",
        current_user: UserInDB = Depends(get_current_active_user),
        intervention_service: InterventionService = Depends(get_intervention_service)
):
    """Add photo to intervention (technician only)"""
    # Todo: check current user rights
    return await intervention_service.add_intervention_photo(
        intervention_id,
        photo,
        photo_type
    )


@router.post("/{intervention_id}/complete-step", response_model=InterventionPublic)
async def complete_step(
        intervention_id: str,
        step_name: str,
        current_user: UserInDB = Depends(get_current_active_user),
        # Todo: check current user rights
        intervention_service: InterventionService = Depends(get_intervention_service)
):
    """Mark a step as completed (technician only)"""
    return await intervention_service.complete_intervention_step(
        intervention_id,
        step_name
    )


@router.put("/{intervention_id}", response_model=InterventionPublic)
async def update_intervention(
        intervention_id: str,
        update_data: InterventionUpdate,
        current_user: UserInDB = Depends(get_current_active_user),
        # Todo: check current user rights
        intervention_service: InterventionService = Depends(get_intervention_service)
):
    """Update intervention details (technician only)"""
    intervention = await intervention_service.intervention_manager.update(
        intervention_id,
        update_data.dict(exclude_unset=True)
    )
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return intervention


@router.post("/{intervention_id}/assign-technicians", response_model=InterventionPublic)
async def assign_technicians(
        intervention_id: str,
        technician_ids: List[str],
        is_primary: bool = False,
        current_user: UserInDB = Depends(get_current_active_user),
        intervention_service: InterventionService = Depends(get_intervention_service)
):
    """Assign technicians to intervention (admin only)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign technicians"
        )

    return await intervention_service.assign_technicians_to_intervention(
        intervention_id,
        technician_ids,
        is_primary
    )


@router.post("/{intervention_id}/complete", response_model=InterventionPublic)
async def complete_intervention(
        intervention_id: str,
        report_id: str,
        current_user: UserInDB = Depends(get_current_active_user),
        intervention_service: InterventionService = Depends(get_intervention_service)
):
    """Mark intervention as completed (assigned technician only)"""
    # Verify current user is assigned to this intervention
    intervention = await intervention_service.get_intervention(intervention_id)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    if PyObjectId(current_user.id) not in intervention.technician_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this intervention"
        )

    return await intervention_service.complete_intervention(
        intervention_id,
        report_id,
        str(current_user.id)
    )


@router.get("/report/{report_id}", response_model=List[InterventionPublic])
async def get_report_interventions(
        report_id: str,
        intervention_status: Optional[str] = None,
        intervention_service: InterventionService = Depends(get_intervention_service)
):
    """Get all interventions for a report"""
    return await intervention_service.intervention_manager.get_report_interventions(
        report_id,
        intervention_status
    )


@router.get("/technician/{technician_id}", response_model=List[InterventionPublic])
async def get_technician_interventions(
        technician_id: str,
        intervention_status: Optional[str] = None,
        current_user: UserInDB = Depends(get_current_active_user),
        intervention_service: InterventionService = Depends(get_intervention_service)
):
    """Get all interventions for a technician"""
    # Admins can view any technician's interventions
    if current_user.role not in ["admin", "super_admin"] and str(current_user.id) != technician_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own interventions"
        )

    return await intervention_service.intervention_manager.get_technician_interventions(
        technician_id,
        intervention_status
    )
