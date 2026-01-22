"""
认证客户端 - 本地JWT验证
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)
security = HTTPBearer()

# JWT配置 (与认证服务保持一致)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

# 调试日志
logger.info(f"Vector Search Service - SECRET_KEY loaded: {SECRET_KEY[:10]}..." if len(SECRET_KEY) > 10 else "SECRET_KEY not set!")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    从JWT Token中解析用户信息（本地验证）
    
    Returns:
        dict: 用户信息 {"id": int, "username": str, "is_active": bool, "is_superuser": bool}
    """
    token = credentials.credentials
    
    try:
        logger.debug(f"Verifying token: {token[:20]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        username: str = payload.get("sub")
        is_active: bool = payload.get("is_active", True)
        is_superuser: bool = payload.get("is_superuser", False)

        if user_id is None or username is None:
            logger.warning(f"Token missing user_id or username: {payload}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账号已被禁用"
            )

        logger.debug(f"Token verified for user: {username} (id={user_id})")
        return {
            "id": user_id,
            "username": username,
            "is_active": is_active,
            "is_superuser": is_superuser
        }
        
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        logger.error(f"Token: {token[:30]}..., SECRET_KEY: {SECRET_KEY[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
