from fastapi import Depends, HTTPException, status

from app.api.v1.services.auth import AuthService, get_auth_service, oauth2_scheme
from app.db.models.users import UserPublic, UserInDB


async def get_current_active_user(
        auth_service: AuthService = Depends(get_auth_service),
        token: str = Depends(oauth2_scheme)
) -> UserInDB:
    user = await auth_service.get_current_user(token)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def get_current_admin_user(
        current_user: UserPublic = Depends(get_current_active_user)
) -> UserPublic:
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
