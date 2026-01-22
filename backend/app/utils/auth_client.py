"""
认证客户端 - 本地验证JWT Token（快速）+ 认证服务调用（完整信息）
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


def verify_token_locally(token: str) -> Optional[dict]:
    """
    本地验证JWT Token（快速，不需要调用认证服务）
    
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
        
        # 返回简化的用户信息（从Token中提取）
        return {
            "id": user_id,
            "username": username,
            "is_active": True  # Token有效即认为用户激活
        }
    except JWTError:
        return None


async def get_current_user_from_auth_service(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    从Token获取当前用户（本地验证，快速）
    
    Args:
        credentials: HTTP认证凭据
        
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: 如果认证失败
    """
    token = credentials.credentials
    user_info = verify_token_locally(token)
    
    if user_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_info


async def get_current_active_user_from_auth_service(
    user_info: dict = Depends(get_current_user_from_auth_service)
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


async def get_optional_user_from_auth_service(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    获取可选的当前用户（不强制认证）
    
    Args:
        credentials: HTTP认证凭据
        
    Returns:
        用户信息字典或None
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    return verify_token_locally(token)

