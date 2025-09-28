"""
Intent Recognition Models
Defines data structures for intent recognition and entity extraction
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class IntentType(str, Enum):
    """Intent types enumeration"""
    GREETING = "greeting"
    HOTEL_SEARCH = "hotel_search"
    LOCATION = "location"
    DATES = "dates"
    GUESTS = "guests"
    AMENITIES = "amenities"
    PRICE = "price"
    FILTER = "filter"
    BOOKING = "booking"
    CANCEL = "cancel"
    HELP = "help"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    """Entity types enumeration"""
    LOCATION = "location"
    DATE = "date"
    NUMBER = "number"
    AMENITY = "amenity"
    PRICE_RANGE = "price_range"
    HOTEL_NAME = "hotel_name"


class Entity(BaseModel):
    """Entity extracted from user message"""
    type: EntityType
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    start_pos: int = 0
    end_pos: int = 0


class Intent(BaseModel):
    """Intent recognition result"""
    type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    entities: List[Entity] = []
    raw_text: str = ""


class ChatResponse(BaseModel):
    """Chatbot response model"""
    message: str
    intent: Optional[Intent] = None
    entities: List[Entity] = []
    suggestions: List[str] = []
    hotel_data: Optional[Dict[str, Any]] = None
    booking_data: Optional[Dict[str, Any]] = None
    requires_input: bool = False
    next_step: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ConversationState(str, Enum):
    """Conversation state enumeration"""
    GREETING = "greeting"
    LOCATION_NEEDED = "location_needed"
    DATES_NEEDED = "dates_needed"
    GUESTS_NEEDED = "guests_needed"
    SHOWING_RESULTS = "showing_results"
    FILTERING = "filtering"
    BOOKING = "booking"
    COMPLETED = "completed"
