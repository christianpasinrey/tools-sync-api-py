import hashlib
import os
import secrets
from datetime import datetime, timedelta

import bcrypt as _bcrypt
from jose import jwt

from src.config.settings import settings
from src.models.user import User
from src.models.vault_item import VaultItem
from src.models.deletion_log import DeletionLog


def _generate_vault_salt() -> list[int]:
    """Generate a 16-byte random salt as list of ints."""
    return list(os.urandom(16))


def _hash_password(password: str) -> str:
    salt = _bcrypt.gensalt(rounds=12)
    return _bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    return _bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _hash_token(token: str) -> str:
    # Pre-hash with SHA-256 to fit bcrypt's 72-byte limit (JWT tokens are longer)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest().encode("utf-8")
    salt = _bcrypt.gensalt(rounds=10)
    return _bcrypt.hashpw(digest, salt).decode("utf-8")


def _verify_token(token: str, hashed: str) -> bool:
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest().encode("utf-8")
    return _bcrypt.checkpw(digest, hashed.encode("utf-8"))


def _create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expires_minutes)
    return jwt.encode(
        {"userId": user_id, "exp": expire},
        settings.jwt_secret,
        algorithm="HS256",
    )


def _create_refresh_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_expires_days)
    return jwt.encode(
        {"userId": user_id, "exp": expire},
        settings.jwt_refresh_secret,
        algorithm="HS256",
    )


# --- Controller functions ---


async def register(email: str, password: str, vault_salt: list[int] | None = None):
    existing = await User.find_one(User.email == email)
    if existing:
        return {"error": "Email already registered", "status": 409}

    user = User(
        email=email,
        password_hash=_hash_password(password),
        vault_salt=vault_salt or _generate_vault_salt(),
    )
    await user.insert()

    access_token = _create_access_token(str(user.id))
    refresh_token = _create_refresh_token(str(user.id))

    user.refresh_token_hash = _hash_token(refresh_token)
    await user.save()

    return {
        "data": {
            "token": access_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "vaultSalt": user.vault_salt,
            },
        },
        "refresh_token": refresh_token,
    }


async def login(email: str, password: str):
    user = await User.find_one(User.email == email)
    if not user or not _verify_password(password, user.password_hash):
        return {"error": "Invalid credentials", "status": 401}

    access_token = _create_access_token(str(user.id))
    refresh_token = _create_refresh_token(str(user.id))

    user.refresh_token_hash = _hash_token(refresh_token)
    await user.save()

    return {
        "data": {
            "token": access_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "vaultSalt": user.vault_salt,
            },
        },
        "refresh_token": refresh_token,
    }


async def refresh(refresh_token_value: str):
    try:
        payload = jwt.decode(
            refresh_token_value, settings.jwt_refresh_secret, algorithms=["HS256"]
        )
    except Exception:
        return {"error": "Invalid refresh token", "status": 401}

    user_id = payload.get("userId")
    user = await User.get(user_id)
    if not user or not user.refresh_token_hash:
        return {"error": "Invalid refresh token", "status": 401}

    if not _verify_token(refresh_token_value, user.refresh_token_hash):
        return {"error": "Invalid refresh token", "status": 401}

    new_access_token = _create_access_token(str(user.id))
    new_refresh_token = _create_refresh_token(str(user.id))

    user.refresh_token_hash = _hash_token(new_refresh_token)
    await user.save()

    return {
        "data": {"token": new_access_token},
        "refresh_token": new_refresh_token,
    }


async def change_password(
    user_id: str, current_password: str, new_password: str, new_vault_salt: list[int]
):
    user = await User.get(user_id)
    if not user:
        return {"error": "User not found", "status": 404}

    if not _verify_password(current_password, user.password_hash):
        return {"error": "Current password is incorrect", "status": 401}

    user.password_hash = _hash_password(new_password)
    user.vault_salt = new_vault_salt
    user.refresh_token_hash = None
    await user.save()

    return {"data": {"message": "Password changed successfully"}}


async def logout(user_id: str):
    user = await User.get(user_id)
    if user:
        user.refresh_token_hash = None
        await user.save()
    return {"data": {"message": "Logged out successfully"}}


async def forgot_password(email: str):
    """Always returns success to prevent email enumeration."""
    user = await User.find_one(User.email == email)
    if not user:
        return {"data": {"message": "If the email exists, a reset link was sent"}}

    reset_token = secrets.token_hex(32)
    user.reset_token_hash = _hash_token(reset_token)
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
    await user.save()

    from src.utils.email import send_reset_email

    try:
        await send_reset_email(email, reset_token)
    except Exception as e:
        print(f"Failed to send reset email: {e}")

    return {"data": {"message": "If the email exists, a reset link was sent"}}


async def verify_reset_token(email: str, token: str):
    user = await User.find_one(User.email == email)
    if not user or not user.reset_token_hash or not user.reset_token_expiry:
        return {"error": "Invalid or expired reset token", "status": 400}

    if datetime.utcnow() > user.reset_token_expiry:
        return {"error": "Invalid or expired reset token", "status": 400}

    if not _verify_token(token, user.reset_token_hash):
        return {"error": "Invalid or expired reset token", "status": 400}

    return {"data": {"valid": True}}


async def reset_account(
    email: str, token: str, new_password: str, new_vault_salt: list[int]
):
    user = await User.find_one(User.email == email)
    if not user or not user.reset_token_hash or not user.reset_token_expiry:
        return {"error": "Invalid or expired reset token", "status": 400}

    if datetime.utcnow() > user.reset_token_expiry:
        return {"error": "Invalid or expired reset token", "status": 400}

    if not _verify_token(token, user.reset_token_hash):
        return {"error": "Invalid or expired reset token", "status": 400}

    # Delete all vault data
    await VaultItem.find(VaultItem.user_id == str(user.id)).delete()
    await DeletionLog.find(DeletionLog.user_id == str(user.id)).delete()

    # Update credentials
    user.password_hash = _hash_password(new_password)
    user.vault_salt = new_vault_salt
    user.reset_token_hash = None
    user.reset_token_expiry = None
    user.refresh_token_hash = None
    await user.save()

    access_token = _create_access_token(str(user.id))
    refresh_token = _create_refresh_token(str(user.id))

    user.refresh_token_hash = _hash_token(refresh_token)
    await user.save()

    return {
        "data": {
            "token": access_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "vaultSalt": user.vault_salt,
            },
        },
        "refresh_token": refresh_token,
    }
