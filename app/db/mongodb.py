# app/db/mongodb.py

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import monitoring

from app.core.configs import settings
from app.db.utils import ColorMongoLogger

# monitoring.register(CommandLogger())
monitoring.register(ColorMongoLogger())

client: Optional[AsyncIOMotorClient] = None


# MongoDB connection example
def get_mongo_connection_uri():
    if settings.ENVIRONMENT == "local":
        return settings.MONGO_DATABASE_URI
    return f"mongodb://{settings.MONGO_USERNAME}:{settings.MONGO_PASSWORD}@{settings.MONGO_HOST}:{settings.MONGO_PORT}"


async def connect_to_db():
    global client
    client = AsyncIOMotorClient(
        get_mongo_connection_uri(),
        # Enable server selection logging
        serverSelectionTimeoutMS=3000,
        # Enable command monitoring
    )


async def close_db_connection():
    global client
    if client:
        client.close()


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncIOMotorClient, None]:
    try:
        db = client[settings.MONGO_DATABASE_NAME]
        yield db
    finally:
        pass
