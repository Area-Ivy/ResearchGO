"""
对话会话相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse
)
# 使用认证服务客户端
from app.utils.auth_client import get_current_active_user_from_auth_service

router = APIRouter(prefix="/api/conversations", tags=["对话管理"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: dict = Depends(get_current_active_user_from_auth_service),
    db: Session = Depends(get_db)
):
    """
    创建新的对话会话
    
    Args:
        conversation_data: 对话会话数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        ConversationResponse: 创建的对话会话信息
    """
    conversation = Conversation(
        user_id=current_user["id"],
        title=conversation_data.title
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.get("", response_model=ConversationListResponse)
async def get_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_active_user_from_auth_service),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的对话会话列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数限制
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        ConversationListResponse: 对话会话列表
    """
    # 查询总数
    total = db.query(Conversation).filter(
        Conversation.user_id == current_user["id"],
        Conversation.is_deleted == False
    ).count()
    
    # 查询对话列表（按更新时间倒序）
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user["id"],
        Conversation.is_deleted == False
    ).order_by(desc(Conversation.updated_at)).offset(skip).limit(limit).all()
    
    # 为每个对话添加消息数量
    conversations_with_count = []
    for conv in conversations:
        message_count = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).count()
        
        conv_dict = {
            "id": conv.id,
            "user_id": conv.user_id,
            "title": conv.title,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "message_count": message_count
        }
        conversations_with_count.append(ConversationResponse(**conv_dict))
    
    return ConversationListResponse(
        total=total,
        conversations=conversations_with_count
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    current_user: dict = Depends(get_current_active_user_from_auth_service),
    db: Session = Depends(get_db)
):
    """
    获取对话会话详情（包含所有消息）
    
    Args:
        conversation_id: 对话会话ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        ConversationDetailResponse: 对话会话详情
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user["id"],
        Conversation.is_deleted == False
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话会话不存在"
        )
    
    # 获取所有消息
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()
    
    return ConversationDetailResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[MessageResponse.from_orm(msg) for msg in messages]
    )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    current_user: dict = Depends(get_current_active_user_from_auth_service),
    db: Session = Depends(get_db)
):
    """
    更新对话会话
    
    Args:
        conversation_id: 对话会话ID
        conversation_update: 更新数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        ConversationResponse: 更新后的对话会话信息
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user["id"],
        Conversation.is_deleted == False
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话会话不存在"
        )
    
    if conversation_update.title:
        conversation.title = conversation_update.title
    
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    current_user: dict = Depends(get_current_active_user_from_auth_service),
    db: Session = Depends(get_db)
):
    """
    删除对话会话（软删除）
    
    Args:
        conversation_id: 对话会话ID
        current_user: 当前用户
        db: 数据库会话
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user["id"],
        Conversation.is_deleted == False
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话会话不存在"
        )
    
    # 软删除
    conversation.is_deleted = True
    db.commit()
    
    return None


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: int,
    message_data: MessageCreate,
    current_user: dict = Depends(get_current_active_user_from_auth_service),
    db: Session = Depends(get_db)
):
    """
    向对话会话添加消息
    
    Args:
        conversation_id: 对话会话ID
        message_data: 消息数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        MessageResponse: 创建的消息信息
    """
    # 验证对话会话是否存在且属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user["id"],
        Conversation.is_deleted == False
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话会话不存在"
        )
    
    # 创建消息
    message = Message(
        conversation_id=conversation_id,
        role=message_data.role,
        content=message_data.content
    )
    
    db.add(message)
    
    # 更新对话会话的更新时间
    conversation.updated_at = func.now()
    
    db.commit()
    db.refresh(message)
    
    return message


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    current_user: dict = Depends(get_current_active_user_from_auth_service),
    db: Session = Depends(get_db)
):
    """
    获取对话会话的所有消息
    
    Args:
        conversation_id: 对话会话ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        List[MessageResponse]: 消息列表
    """
    # 验证对话会话是否存在且属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user["id"],
        Conversation.is_deleted == False
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话会话不存在"
        )
    
    # 获取消息列表
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()
    
    return messages

