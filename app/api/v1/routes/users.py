from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException

from app.api.deps import get_current_active_user
from app.api.v1.services.auth import get_auth_service, AuthService
from app.api.v1.services.file import FileService
from app.api.v1.services.user import UserService
from app.db.models.base import PyObjectId
from app.db.models.users import UserPublic, UserSearch, UserUpdate, PasswordChange, UserRoleUpdate, UserStatusUpdate

router = APIRouter()


# ----------------------
# Public Endpoints
# ----------------------

@router.post("/search", response_model=List[UserPublic])
async def search_users(
        search_params: UserSearch,
        user_service: UserService = Depends(UserService)
):
    """Search users with filters"""
    return await user_service.search_users(search_params)


@router.get("/actives", response_model=List[UserPublic])
async def get_active_users(
        skip: int = 0,
        limit: int = 100,
        user_service: UserService = Depends(UserService),
):
    """
    Get active users with reports (optimized aggregation version)
    """
    return await user_service.get_active_reporting_users(skip, limit)


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
        user_id: PyObjectId,
        user_service: UserService = Depends(UserService)
):
    """Get public user profile"""
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ----------------------
# Authenticated User Endpoints
# ----------------------

@router.get("/me", response_model=UserPublic)
async def get_my_profile(
        current_user: UserPublic = Depends(get_current_active_user)
):
    """Get current user's profile"""
    return current_user


@router.put("/me", response_model=UserPublic)
async def update_my_profile(
        update_data: UserUpdate,
        current_user: UserPublic = Depends(get_current_active_user),
        user_service: UserService = Depends(UserService)
):
    """Update current user's profile"""
    return await user_service.update_user(current_user.id, update_data)


@router.put("/me/password")
async def change_my_password(
        password_change: PasswordChange,
        current_user: UserPublic = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service),
        user_service: UserService = Depends(UserService)
):
    """Change current user's password"""
    # Verify current password
    if not auth_service.verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Update password
    new_hashed_password = auth_service.get_password_hash(password_change.new_password)
    await user_service.update_user(current_user.id, UserUpdate(hashed_password=new_hashed_password))

    return {"message": "Password updated successfully"}


@router.put("/me/avatar")
async def update_my_avatar(
        avatar: UploadFile = File(...),
        current_user: UserPublic = Depends(get_current_active_user),
        user_service: UserService = Depends(UserService),
        file_service: FileService = Depends(FileService)
):
    """Upload and update user avatar"""
    avatar_url = await file_service.upload_avatar(avatar, current_user.id)
    return await user_service.update_user(current_user.id, UserUpdate(avatar=avatar_url))


# ----------------------
# Admin Endpoints
# ----------------------

@router.get("/", response_model=List[UserPublic])
async def list_users(
        skip: int = 0,
        limit: int = 100,
        current_user: UserPublic = Depends(get_current_active_user),
        user_service: UserService = Depends(UserService)
):
    """List all users (admin only)"""
    # Todo: Check current user role before sending the users list
    return await user_service.list_users(skip, limit)


@router.put("/{user_id}/role", response_model=UserPublic)
async def update_user_role(
        user_id: PyObjectId,
        role_update: UserRoleUpdate,
        current_user: UserPublic = Depends(get_current_active_user),
        user_service: UserService = Depends(UserService)
):
    """Update user role (admin only)"""
    # Todo: Check current user role and authorizations before
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    return await user_service.update_user(user_id, UserUpdate(role=role_update.role))


@router.put("/{user_id}/status", response_model=UserPublic)
async def update_user_status(
        user_id: PyObjectId,
        status_update: UserStatusUpdate,
        current_user: UserPublic = Depends(get_current_active_user),
        user_service: UserService = Depends(UserService)
):
    """Update user status (admin only)"""
    # Todo: Check current user role and authorizations before
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot change your own status")
    return await user_service.update_user(user_id, UserUpdate(role=status_update.status))


@router.delete("/{user_id}")
async def delete_user(
        user_id: PyObjectId,
        current_user: UserPublic = Depends(get_current_active_user),
        user_service: UserService = Depends(UserService)
):
    """Delete user (admin only)"""
    # Todo: Check current user role and authorizations before
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await user_service.delete_user(user_id)
    return {"message": "User deleted successfully"}
