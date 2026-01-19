from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from app.models.chat import ChatRequest, ChatResponse, ChatMessage
from app.services.openai_service import OpenAIService
import json
import logging

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)




@router.post("/message")
async def chat_message(request: ChatRequest):
    """
    Handle chat message and return streaming or complete response
    
    Args:
        request: ChatRequest containing message and conversation history
        
    Returns:
        StreamingResponse with SSE events or complete JSON response
    """
    try:
        # Initialize OpenAI service
        openai_service = OpenAIService()
        
        # Build messages list
        messages = []
        
        # Add system message
        system_message = ChatMessage(
            role="system",
            content="You are a helpful AI research assistant. You help users understand research papers, explain complex concepts, and provide accurate information about computer science and AI topics. Format your responses using Markdown for better readability."
        )
        messages.append(system_message)
        
        # Add conversation history
        if request.conversation_history:
            messages.extend(request.conversation_history)
        
        # Add current user message
        user_message = ChatMessage(role="user", content=request.message)
        messages.append(user_message)
        
        # Stream response
        if request.stream:
            async def event_generator():
                try:
                    async for chunk in openai_service.chat_completion_stream(
                        messages=messages,
                        model=request.model,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens
                    ):
                        # Send chunk as SSE event
                        yield {
                            "event": "message",
                            "data": json.dumps({"content": chunk})
                        }
                    
                    # Send completion event
                    yield {
                        "event": "done",
                        "data": json.dumps({"status": "complete"})
                    }
                    
                except Exception as e:
                    logger.error(f"Error in stream: {str(e)}")
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": str(e)})
                    }
            
            return EventSourceResponse(event_generator())
        
        # Non-streaming response
        else:
            response_text = await openai_service.chat_completion(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            return ChatResponse(
                message=response_text,
                role="assistant",
                finish_reason="stop"
            )
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "chat-api"
    }

