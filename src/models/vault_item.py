from typing import Optional

from beanie import Document
from pydantic import BaseModel, Field

ALLOWED_STORES = [
    "image-presets",
    "svg-projects",
    "three-scenes",
    "pdf-documents",
    "spreadsheet-workbooks",
    "markdown-documents",
    "color-palettes",
    "devtools-snippets",
    "api-collections",
    "phone-configs",
    "map-projects",
    "invoice-configs",
    "kanban-boards",
]


class EncryptedPayload(BaseModel):
    salt: str
    iv: str
    data: str


class VaultItem(Document):
    user_id: str
    store_name: str
    item_id: str
    item_name: str = Field(max_length=200)
    encrypted_payload: Optional[EncryptedPayload] = None
    payload_size: int = 0
    updated_at: int  # Client timestamp in milliseconds

    class Settings:
        name = "vaultitems"
        indexes = [
            [("user_id", 1), ("store_name", 1), ("item_id", 1)],
            [("user_id", 1), ("updated_at", 1)],
        ]
