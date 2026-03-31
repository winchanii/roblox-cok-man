from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
from app.config import settings
from app.database import AsyncSession, get_db
from app.models import User
from sqlalchemy import select
import secrets

security = HTTPBearer()

def generate_access_key() -> str:
    """Сгенерировать ключ доступа"""
    return secrets.token_hex(32)

def create_jwt_token(user_id: int, discord_id: str) -> str:
    """Создать JWT токен"""
    expire = datetime.utcnow() + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "discord_id": discord_id,
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    """Проверить JWT токен"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Получить текущего пользователя из токена"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    async for db in get_db():
        result = await db.execute(
            select(User).where(User.id == payload["user_id"])
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
    
    raise HTTPException(status_code=500, detail="Database error")