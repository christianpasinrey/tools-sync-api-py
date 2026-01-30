from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel

from src.controllers import vault_controller
from src.middleware.auth import authenticate
from src.middleware.rate_limiter import limiter, BATCH_LIMIT
from src.models.vault_item import EncryptedPayload

router = APIRouter(prefix="/vault", tags=["vault"])


# --- Request schemas ---


class UpsertItemBody(BaseModel):
    itemName: str
    encryptedPayload: EncryptedPayload
    updatedAt: int


class DeleteItemBody(BaseModel):
    deletedAt: int


class BatchPushBody(BaseModel):
    items: list[dict]


class BatchPullBody(BaseModel):
    items: list[dict]


# --- Endpoints ---


@router.get("/sync-status")
async def sync_status(
    since: int = Query(default=0),
    user_id: str = Depends(authenticate),
):
    result = await vault_controller.sync_status(user_id, since)
    return result["data"]


@router.get("/{store_name}")
async def list_items(
    store_name: str,
    response: Response,
    user_id: str = Depends(authenticate),
):
    result = await vault_controller.list_items(user_id, store_name)
    if "error" in result:
        response.status_code = result["status"]
        return {"message": result["error"]}
    return result["data"]


@router.get("/{store_name}/{item_id}")
async def get_item(
    store_name: str,
    item_id: str,
    response: Response,
    user_id: str = Depends(authenticate),
):
    result = await vault_controller.get_item(user_id, store_name, item_id)
    if "error" in result:
        response.status_code = result["status"]
        return {"message": result["error"]}
    return result["data"]


@router.put("/{store_name}/{item_id}")
async def upsert_item(
    store_name: str,
    item_id: str,
    body: UpsertItemBody,
    response: Response,
    user_id: str = Depends(authenticate),
):
    result = await vault_controller.upsert_item(
        user_id=user_id,
        store_name=store_name,
        item_id=item_id,
        item_name=body.itemName,
        encrypted_payload=body.encryptedPayload,
        updated_at=body.updatedAt,
    )
    if "error" in result:
        response.status_code = result["status"]
        resp = {"message": result["error"]}
        if "extra" in result:
            resp.update(result["extra"])
        return resp
    return result["data"]


@router.delete("/{store_name}/{item_id}")
async def delete_item(
    store_name: str,
    item_id: str,
    body: DeleteItemBody,
    response: Response,
    user_id: str = Depends(authenticate),
):
    result = await vault_controller.delete_item(
        user_id, store_name, item_id, body.deletedAt
    )
    if "error" in result:
        response.status_code = result["status"]
        return {"message": result["error"]}
    return result["data"]


@router.post("/batch-push")
@limiter.limit(BATCH_LIMIT)
async def batch_push(
    body: BatchPushBody,
    request: Request,
    response: Response,
    user_id: str = Depends(authenticate),
):
    result = await vault_controller.batch_push(user_id, body.items)
    if "error" in result:
        response.status_code = result["status"]
        return {"message": result["error"]}
    return result["data"]


@router.post("/batch-pull")
@limiter.limit(BATCH_LIMIT)
async def batch_pull(
    body: BatchPullBody,
    request: Request,
    response: Response,
    user_id: str = Depends(authenticate),
):
    result = await vault_controller.batch_pull(user_id, body.items)
    if "error" in result:
        response.status_code = result["status"]
        return {"message": result["error"]}
    return result["data"]
