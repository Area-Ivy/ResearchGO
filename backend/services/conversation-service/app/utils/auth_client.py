"""
认证客户端 - 验证JWT Token
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

load_dotenv()

# JWT配置（与认证服务保持一致）
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

# HTTP Bearer认证方案
security = HTTPBearer()


def verify_token(token: str) -> Optional[dict]:
    """
    验证JWT Token
    
    Args:
        token: JWT Token
        
    Returns:
        Token中的用户信息，如果验证失败返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        username: str = payload.get("sub")
        
        if user_id is None or username is None:
            return None
        
        return {
            "id": user_id,
            "username": username,
            "is_active": True
        }
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    获取当前用户
    
    Args:
        credentials: HTTP认证凭据
        
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: 如果认证失败
    """
    token = credentials.credentials
    user_info = verify_token(token)
    
    if user_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_info


async def get_current_active_user(
    user_info: dict = Depends(get_current_user)
) -> dict:
    """
    获取当前活跃用户
    
    Args:
        user_info: 用户信息
        
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: 如果用户未激活
    """
    if not user_info.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账号未激活"
        )
    return user_info

