from typing import Optional

from app.db.managers.base import DBManager
from app.db.models.users import UserCreate, UserInDB, UserCreateInDB


class UserManager(DBManager):
    def __init__(self):
        super().__init__("users", UserInDB)

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        return await self.get_by_field("email", email)

    async def get_by_phone(self, phone: str) -> Optional[UserInDB]:
        return await self.get_by_field("phone", phone)

    async def create_user(self, user: UserCreate) -> UserInDB:
        user_dict = user.dict()
        if 'password' in user_dict:
            from app.core.security import get_password_hash
            user_dict['hashed_password'] = get_password_hash(user_dict.pop('password'))
        return await self.create(UserCreateInDB(**user_dict))


def get_user_manager() -> UserManager:
    return UserManager()
