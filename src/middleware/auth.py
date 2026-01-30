from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.config.settings import settings

security = HTTPBearer()


async def authenticate(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Verify JWT access token and return user_id."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id: str = payload.get("userId")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError as e:
        if "expired" in str(e).lower():
            raise HTTPException(
                status_code=401,
                detail={"message": "Token expired", "code": "TOKEN_EXPIRED"},
            )
        raise HTTPException(status_code=401, detail="Invalid token")
