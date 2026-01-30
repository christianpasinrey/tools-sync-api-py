import base64

from src.models.vault_item import VaultItem, ALLOWED_STORES, EncryptedPayload
from src.models.deletion_log import DeletionLog

MAX_ITEMS_PER_BATCH = 50
MAX_PAYLOAD_BYTES = 10 * 1024 * 1024  # 10MB per item


def _validate_store_name(store_name: str) -> str | None:
    if store_name not in ALLOWED_STORES:
        return f"Invalid store name: {store_name}"
    return None


def _calculate_payload_size(payload: EncryptedPayload) -> int:
    try:
        return len(base64.b64decode(payload.data))
    except Exception:
        return 0


async def sync_status(user_id: str, since: int = 0):
    """Return item timestamps and deletions since a given timestamp."""
    items = await VaultItem.find(
        VaultItem.user_id == user_id,
        VaultItem.updated_at > since,
    ).to_list()

    item_timestamps = [
        {
            "storeName": item.store_name,
            "itemId": item.item_id,
            "updatedAt": item.updated_at,
        }
        for item in items
    ]

    deletions = await DeletionLog.find(
        DeletionLog.user_id == user_id,
        DeletionLog.deleted_at > since,
    ).to_list()

    deletion_list = [
        {
            "storeName": d.store_name,
            "itemId": d.item_id,
            "deletedAt": d.deleted_at,
        }
        for d in deletions
    ]

    return {"data": {"items": item_timestamps, "deletions": deletion_list}}


async def list_items(user_id: str, store_name: str):
    error = _validate_store_name(store_name)
    if error:
        return {"error": error, "status": 400}

    items = await VaultItem.find(
        VaultItem.user_id == user_id,
        VaultItem.store_name == store_name,
    ).to_list()

    return {
        "data": [
            {
                "itemId": item.item_id,
                "itemName": item.item_name,
                "payloadSize": item.payload_size,
                "updatedAt": item.updated_at,
            }
            for item in items
        ]
    }


async def get_item(user_id: str, store_name: str, item_id: str):
    error = _validate_store_name(store_name)
    if error:
        return {"error": error, "status": 400}

    item = await VaultItem.find_one(
        VaultItem.user_id == user_id,
        VaultItem.store_name == store_name,
        VaultItem.item_id == item_id,
    )
    if not item:
        return {"error": "Item not found", "status": 404}

    return {
        "data": {
            "itemId": item.item_id,
            "itemName": item.item_name,
            "encryptedPayload": item.encrypted_payload.model_dump()
            if item.encrypted_payload
            else None,
            "payloadSize": item.payload_size,
            "updatedAt": item.updated_at,
        }
    }


async def upsert_item(
    user_id: str,
    store_name: str,
    item_id: str,
    item_name: str,
    encrypted_payload: EncryptedPayload,
    updated_at: int,
):
    error = _validate_store_name(store_name)
    if error:
        return {"error": error, "status": 400}

    payload_size = _calculate_payload_size(encrypted_payload)
    if payload_size > MAX_PAYLOAD_BYTES:
        return {"error": "Payload exceeds 10MB limit", "status": 413}

    existing = await VaultItem.find_one(
        VaultItem.user_id == user_id,
        VaultItem.store_name == store_name,
        VaultItem.item_id == item_id,
    )

    if existing and updated_at < existing.updated_at:
        return {
            "error": "Conflict: remote is newer",
            "status": 409,
            "extra": {"remoteUpdatedAt": existing.updated_at},
        }

    if existing:
        existing.item_name = item_name
        existing.encrypted_payload = encrypted_payload
        existing.payload_size = payload_size
        existing.updated_at = updated_at
        await existing.save()
    else:
        item = VaultItem(
            user_id=user_id,
            store_name=store_name,
            item_id=item_id,
            item_name=item_name,
            encrypted_payload=encrypted_payload,
            payload_size=payload_size,
            updated_at=updated_at,
        )
        await item.insert()

    return {"data": {"success": True}}


async def delete_item(user_id: str, store_name: str, item_id: str, deleted_at: int):
    error = _validate_store_name(store_name)
    if error:
        return {"error": error, "status": 400}

    item = await VaultItem.find_one(
        VaultItem.user_id == user_id,
        VaultItem.store_name == store_name,
        VaultItem.item_id == item_id,
    )
    if not item:
        return {"error": "Item not found", "status": 404}

    await item.delete()

    log = DeletionLog(
        user_id=user_id,
        store_name=store_name,
        item_id=item_id,
        deleted_at=deleted_at,
    )
    await log.insert()

    return {"data": {"success": True}}


async def batch_push(user_id: str, items: list[dict]):
    if len(items) > MAX_ITEMS_PER_BATCH:
        return {"error": f"Max {MAX_ITEMS_PER_BATCH} items per batch", "status": 400}

    results = []
    for item_data in items:
        result = await upsert_item(
            user_id=user_id,
            store_name=item_data["storeName"],
            item_id=item_data["itemId"],
            item_name=item_data.get("itemName", ""),
            encrypted_payload=EncryptedPayload(**item_data["encryptedPayload"]),
            updated_at=item_data["updatedAt"],
        )
        results.append(
            {
                "itemId": item_data["itemId"],
                "storeName": item_data["storeName"],
                "success": "data" in result,
                "error": result.get("error"),
            }
        )

    return {"data": {"results": results}}


async def batch_pull(user_id: str, items: list[dict]):
    if len(items) > MAX_ITEMS_PER_BATCH:
        return {"error": f"Max {MAX_ITEMS_PER_BATCH} items per batch", "status": 400}

    results = []
    for req in items:
        item = await VaultItem.find_one(
            VaultItem.user_id == user_id,
            VaultItem.store_name == req["storeName"],
            VaultItem.item_id == req["itemId"],
        )
        if item:
            results.append(
                {
                    "storeName": item.store_name,
                    "itemId": item.item_id,
                    "itemName": item.item_name,
                    "encryptedPayload": item.encrypted_payload.model_dump()
                    if item.encrypted_payload
                    else None,
                    "payloadSize": item.payload_size,
                    "updatedAt": item.updated_at,
                }
            )
        else:
            results.append(
                {
                    "storeName": req["storeName"],
                    "itemId": req["itemId"],
                    "notFound": True,
                }
            )

    return {"data": {"results": results}}
