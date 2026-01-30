from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import EmailStr


class User(Document):
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    vault_salt: list[int]
    refresh_token_hash: Optional[str] = None
    reset_token_hash: Optional[str] = None
    reset_token_expiry: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "users"
