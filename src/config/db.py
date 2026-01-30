from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from src.config.settings import settings
from src.models.user import User
from src.models.vault_item import VaultItem
from src.models.deletion_log import DeletionLog


async def connect_db():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    await init_beanie(
        database=client.get_default_database(),
        document_models=[User, VaultItem, DeletionLog],
    )
    print(f"Connected to MongoDB: {settings.mongodb_uri}")


async def disconnect_db():
    pass
