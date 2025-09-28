"""
Chat Repository
Database operations for chat data
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.ai.chatbot.models.chat_models import ChatSession, ChatMessage, BookingContext, ChatSessionStatus, MessageType
from app.core.db import get_db
from app.core.logger import logger
import uuid


class ChatRepository:
    """Repository for chat data operations"""
    
    def __init__(self):
        self.db = None
    
    def _get_db(self):
        """Get database session"""
        # Always get a fresh session to avoid connection issues
        return next(get_db())
    
    async def get_or_create_session(self, session_id: str, user_id: Optional[str] = None) -> ChatSession:
        """
        Get existing session or create new one
        
        Args:
            session_id: Session ID
            user_id: Optional user ID
            
        Returns:
            Chat session
        """
        try:
            db = self._get_db()
            try:
                # Try to get existing session
                session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id
                ).first()
                
                if session:
                    return session
                
                # Create new session
                session = ChatSession(
                    session_id=session_id,
                    user_id=user_id,
                    status=ChatSessionStatus.ACTIVE
                )
                
                db.add(session)
                db.commit()
                db.refresh(session)
                
                return session
                
            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting or creating session: {str(e)}")
            raise
    
    async def save_message(self, session_id: str, message_type: str, content: str, 
                          intent: Optional[str] = None, entities: Optional[List[Dict]] = None,
                          message_metadata: Optional[Dict[str, Any]] = None) -> ChatMessage:
        """
        Save chat message
        
        Args:
            session_id: Session ID
            message_type: Message type (user/bot)
            content: Message content
            intent: Optional intent
            entities: Optional entities
            message_metadata: Optional message metadata
            
        Returns:
            Saved message
        """
        try:
            db = self._get_db()
            try:
                message = ChatMessage(
                    session_id=session_id,
                    message_type=MessageType(message_type),
                    content=content,
                    intent=intent,
                    entities=entities,
                    message_metadata=message_metadata
                )
                
                db.add(message)
                db.commit()
                db.refresh(message)
                
                return message
                
            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            raise
    
    async def get_session_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """
        Get session messages
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages
            
        Returns:
            List of messages
        """
        try:
            db = self._get_db()
            try:
                messages = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).order_by(desc(ChatMessage.created_at)).limit(limit).all()
                
                return list(reversed(messages))  # Return in chronological order
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting session messages: {str(e)}")
            return []
    
    async def get_booking_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get booking context for session
        
        Args:
            session_id: Session ID
            
        Returns:
            Booking context or None
        """
        try:
            db = self._get_db()
            try:
                context = db.query(BookingContext).filter(
                    BookingContext.session_id == session_id
                ).first()
                
                if context:
                    return {
                        'search_criteria': context.search_criteria or {},
                        'selected_hotels': context.selected_hotels or [],
                        'current_step': context.current_step,
                        'booking_id': context.booking_id
                    }
                
                return None
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting booking context: {str(e)}")
            return None
    
    async def save_booking_context(self, session_id: str, context: Dict[str, Any]) -> BookingContext:
        """
        Save booking context
        
        Args:
            session_id: Session ID
            context: Context data
            
        Returns:
            Saved context
        """
        try:
            db = self._get_db()
            try:
                # Try to get existing context
                existing_context = db.query(BookingContext).filter(
                    BookingContext.session_id == session_id
                ).first()
                
                if existing_context:
                    # Update existing context
                    existing_context.search_criteria = context.get('search_criteria', {})
                    existing_context.selected_hotels = context.get('selected_hotels', [])
                    existing_context.current_step = context.get('current_step')
                    existing_context.booking_id = context.get('booking_id')
                    
                    db.commit()
                    db.refresh(existing_context)
                    
                    return existing_context
                else:
                    # Create new context
                    new_context = BookingContext(
                        session_id=session_id,
                        search_criteria=context.get('search_criteria', {}),
                        selected_hotels=context.get('selected_hotels', []),
                        current_step=context.get('current_step'),
                        booking_id=context.get('booking_id')
                    )
                    
                    db.add(new_context)
                    db.commit()
                    db.refresh(new_context)
                    
                    return new_context
                    
            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error saving booking context: {str(e)}")
            raise
    
    async def update_session_status(self, session_id: str, status: ChatSessionStatus) -> bool:
        """
        Update session status
        
        Args:
            session_id: Session ID
            status: New status
            
        Returns:
            Success status
        """
        try:
            db = self._get_db()
            try:
                session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id
                ).first()
                
                if session:
                    session.status = status
                    db.commit()
                    return True
                
                return False
                
            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error updating session status: {str(e)}")
            return False
    
    async def get_active_sessions(self, user_id: Optional[str] = None) -> List[ChatSession]:
        """
        Get active sessions
        
        Args:
            user_id: Optional user ID filter
            
        Returns:
            List of active sessions
        """
        try:
            db = self._get_db()
            try:
                query = db.query(ChatSession).filter(
                    ChatSession.status == ChatSessionStatus.ACTIVE
                )
                
                if user_id:
                    query = query.filter(ChatSession.user_id == user_id)
                
                return query.all()
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting active sessions: {str(e)}")
            return []
    
    async def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Clean up old completed sessions
        
        Args:
            days: Days to keep sessions
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            from datetime import datetime, timedelta
            
            db = self._get_db()
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Get old completed sessions
                old_sessions = db.query(ChatSession).filter(
                    ChatSession.status == ChatSessionStatus.COMPLETED,
                    ChatSession.updated_at < cutoff_date
                ).all()
                
                count = len(old_sessions)
                
                # Delete old sessions (cascade will handle messages and context)
                for session in old_sessions:
                    db.delete(session)
                
                db.commit()
                
                return count
                
            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {str(e)}")
            return 0
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get session statistics
        
        Args:
            session_id: Session ID
            
        Returns:
            Session statistics
        """
        try:
            db = self._get_db()
            try:
                session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id
                ).first()
                
                if not session:
                    return {}
                
                # Count messages
                message_count = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).count()
                
                # Count user messages
                user_message_count = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id,
                    ChatMessage.message_type == MessageType.USER
                ).count()
                
                # Count bot messages
                bot_message_count = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id,
                    ChatMessage.message_type == MessageType.BOT
                ).count()
                
                return {
                    'session_id': session_id,
                    'status': session.status,
                    'created_at': session.created_at,
                    'updated_at': session.updated_at,
                    'total_messages': message_count,
                    'user_messages': user_message_count,
                    'bot_messages': bot_message_count,
                    'duration_minutes': (session.updated_at - session.created_at).total_seconds() / 60
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting session stats: {str(e)}")
            return {}
