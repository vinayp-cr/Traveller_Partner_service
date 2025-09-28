"""
Chat Controller
API endpoints for chat functionality
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.ai.chatbot.services.chat_service import ChatService
from app.ai.chatbot.models.intent_models import ChatResponse
from app.core.logger import logger
import uuid


# Request/Response Models
class ChatMessageRequest(BaseModel):
    """Chat message request model"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    user_id: Optional[str] = Field(None, description="User ID")


class ChatMessageResponse(BaseModel):
    """Chat message response model"""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Bot response message")
    session_id: str = Field(..., description="Chat session ID")
    intent: Optional[str] = Field(None, description="Recognized intent")
    entities: List[Dict[str, Any]] = Field(default=[], description="Extracted entities")
    suggestions: List[str] = Field(default=[], description="Suggested responses")
    hotel_data: Optional[Dict[str, Any]] = Field(None, description="Hotel search results")
    booking_data: Optional[Dict[str, Any]] = Field(None, description="Booking information")
    requires_input: bool = Field(default=True, description="Whether input is required")
    next_step: Optional[str] = Field(None, description="Next conversation step")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class ChatSessionResponse(BaseModel):
    """Chat session response model"""
    session_id: str = Field(..., description="Session ID")
    status: str = Field(..., description="Session status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    message_count: int = Field(..., description="Total message count")
    duration_minutes: float = Field(..., description="Session duration in minutes")


class ChatHistoryResponse(BaseModel):
    """Chat history response model"""
    session_id: str = Field(..., description="Session ID")
    messages: List[Dict[str, Any]] = Field(..., description="Chat messages")
    total_count: int = Field(..., description="Total message count")


# Initialize router
router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Initialize services
chat_service = ChatService()


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest):
    """
    Send a message to the chatbot
    
    Args:
        request: Chat message request
        
    Returns:
        Bot response
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process message
        response = await chat_service.process_message(
            session_id=session_id,
            user_message=request.message,
            user_id=request.user_id
        )
        
        # Convert response to API format
        return ChatMessageResponse(
            success=True,
            message=response.message,
            session_id=session_id,
            intent=response.intent.type if response.intent else None,
            entities=[entity.dict() for entity in response.entities],
            suggestions=response.suggestions,
            hotel_data=response.hotel_data,
            booking_data=response.booking_data,
            requires_input=response.requires_input,
            next_step=response.next_step,
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: str):
    """
    Get chat session information
    
    Args:
        session_id: Session ID
        
    Returns:
        Session information
    """
    try:
        # Get session stats
        stats = await chat_service.chat_repository.get_session_stats(session_id)
        
        if not stats:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        return ChatSessionResponse(
            session_id=session_id,
            status=stats.get('status', 'unknown'),
            created_at=stats.get('created_at', '').isoformat() if stats.get('created_at') else '',
            updated_at=stats.get('updated_at', '').isoformat() if stats.get('updated_at') else '',
            message_count=stats.get('total_messages', 0),
            duration_minutes=stats.get('duration_minutes', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting session: {str(e)}"
        )


@router.get("/session/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, limit: int = Query(50, ge=1, le=100)):
    """
    Get chat history for a session
    
    Args:
        session_id: Session ID
        limit: Maximum number of messages to return
        
    Returns:
        Chat history
    """
    try:
        # Get session messages
        messages = await chat_service.chat_repository.get_session_messages(session_id, limit)
        
        # Format messages for response
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'id': msg.id,
                'type': msg.message_type,
                'content': msg.content,
                'intent': msg.intent,
                'entities': msg.entities or [],
                'metadata': msg.message_metadata or {},
                'created_at': msg.created_at.isoformat()
            })
        
        return ChatHistoryResponse(
            session_id=session_id,
            messages=formatted_messages,
            total_count=len(formatted_messages)
        )
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting chat history: {str(e)}"
        )


@router.post("/session/{session_id}/reset")
async def reset_session(session_id: str):
    """
    Reset chat session (clear context)
    
    Args:
        session_id: Session ID
        
    Returns:
        Success status
    """
    try:
        # Clear booking context
        await chat_service.chat_repository.save_booking_context(session_id, {})
        
        return {
            "success": True,
            "message": "Session reset successfully",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error resetting session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting session: {str(e)}"
        )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_active_sessions(user_id: Optional[str] = Query(None, description="Filter by user ID")):
    """
    Get active chat sessions
    
    Args:
        user_id: Optional user ID filter
        
    Returns:
        List of active sessions
    """
    try:
        # Get active sessions
        sessions = await chat_service.chat_repository.get_active_sessions(user_id)
        
        # Format sessions for response
        formatted_sessions = []
        for session in sessions:
            stats = await chat_service.chat_repository.get_session_stats(session.session_id)
            formatted_sessions.append(ChatSessionResponse(
                session_id=session.session_id,
                status=session.status,
                created_at=session.created_at.isoformat(),
                updated_at=session.updated_at.isoformat(),
                message_count=stats.get('total_messages', 0),
                duration_minutes=stats.get('duration_minutes', 0)
            ))
        
        return formatted_sessions
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting active sessions: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete chat session
    
    Args:
        session_id: Session ID
        
    Returns:
        Success status
    """
    try:
        # Update session status to cancelled
        success = await chat_service.chat_repository.update_session_status(
            session_id, 
            "cancelled"
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        return {
            "success": True,
            "message": "Session deleted successfully",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting session: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    """
    Check chatbot health
    
    Returns:
        Health status
    """
    try:
        # Test basic functionality
        test_response = await chat_service.process_message(
            session_id="health_check",
            user_message="hello"
        )
        
        return {
            "status": "healthy",
            "service": "Chatbot API",
            "version": "1.0.0",
            "test_response": test_response.message
        }
        
    except Exception as e:
        logger.error(f"Chatbot health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "Chatbot API",
            "version": "1.0.0",
            "error": str(e)
        }
