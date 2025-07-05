from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.db.managers.users import get_user_manager
from app.core.configs import settings
from app.db.models.auth import Token
from app.db.models.users import UserInDB

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class AuthService:
    def __init__(self):
        self.user_manager = get_user_manager()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ENCRYPTION_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=30)  # Default 30 days for refresh token
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ENCRYPTION_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_refresh_token(token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ENCRYPTION_ALGORITHM])
            if payload.get("type") != "refresh":
                return None
            email: str = payload.get("sub")
            if email is None:
                return None
            return email
        except JWTError:
            return None

    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ENCRYPTION_ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                return None
            return email
        except JWTError:
            return None

    @staticmethod
    def verify_email_token(token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ENCRYPTION_ALGORITHM])
            if payload.get("purpose") != "verify_email":
                return None
            email: str = payload.get("sub")
            if email is None:
                return None
            return email
        except JWTError:
            return None

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        user = await self.user_manager.get_by_email(email)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> UserInDB:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ENCRYPTION_ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = await self.user_manager.get_by_email(email)
        if user is None:
            raise credentials_exception
        return user

    async def create_tokens(self, email: str) -> Token:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": email},
            expires_delta=access_token_expires
        )

        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = self.create_refresh_token(
            data={"sub": email},
            expires_delta=refresh_token_expires
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    def create_password_reset_token(self, email: str) -> str:
        expires = timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        return self.create_access_token({"sub": email}, expires_delta=expires)

    def create_email_verification_token(self, email: str) -> str:
        expires = timedelta(hours=settings.EMAIL_VERIFY_TOKEN_EXPIRE_HOURS)
        return self.create_access_token({"sub": email, "purpose": "verify_email"}, expires_delta=expires)


def get_auth_service() -> AuthService:
    return AuthService()
