"""
Chatbot Data Models
Defines data structures for chat sessions, messages, and booking context
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.db import Base
import enum


class ChatSessionStatus(str, enum.Enum):
    """Chat session status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MessageType(str, enum.Enum):
    """Message type enumeration"""
    USER = "user"
    BOT = "bot"


class ChatSession(Base):
    """Chat session model"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(String(255), nullable=True, index=True)
    status = Column(Enum(ChatSessionStatus), default=ChatSessionStatus.ACTIVE, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    booking_context = relationship("BookingContext", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    message_type = Column(Enum(MessageType), nullable=False, index=True)
    content = Column(Text, nullable=False)
    intent = Column(String(100), nullable=True)
    entities = Column(JSON, nullable=True)
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class BookingContext(Base):
    """Booking context model for storing conversation state"""
    __tablename__ = "booking_context"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    search_criteria = Column(JSON, nullable=True)
    selected_hotels = Column(JSON, nullable=True)
    current_step = Column(String(100), nullable=True)
    booking_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="booking_context")
