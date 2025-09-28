from app.core.db import Base
from sqlalchemy import Column, Integer, String, Float, JSON, Text, DateTime
from sqlalchemy.orm import relationship 
from sqlalchemy import ForeignKey, Boolean
from datetime import datetime

class Hotel(Base):
    __tablename__ = "hotels"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Internal hotel ID
    api_hotel_id = Column(String(255), unique=True, index=True, nullable=True)  # Xeni API hotel ID
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String(20), nullable=True)  # Optional field
    email = Column(String(100), nullable=True)  # Optional field
    website = Column(String(255), nullable=True)  # Optional field
    star_rating = Column(Integer, default=3)
    avg_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    amenities = relationship("HotelAmenity", back_populates="hotel", cascade="all, delete-orphan")
    images = relationship("HotelImage", back_populates="hotel", cascade="all, delete-orphan")
    rooms = relationship("Room", back_populates="hotel", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="hotel", cascade="all, delete-orphan")
    


class HotelAmenity(Base):
    __tablename__ = "hotel_amenities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"))
    amenity_name = Column(String(100), nullable=False)
    amenity_type = Column(String(50), default="general")
    icon = Column(String(50), nullable=True)

    hotel = relationship("Hotel", back_populates="amenities")


class HotelImage(Base):
    __tablename__ = "hotel_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"))
    image = Column(String(500), nullable=False)
    caption = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    hotel = relationship("Hotel", back_populates="images")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_ref_id = Column(String(255), unique=True, index=True)
    booking_id = Column(String(255), unique=True, index=True)  # Xeni API booking ID
    recommendation_id = Column(String(255))
    
    # Foreign key relationships to hotels and rooms tables
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=True)  # Link to hotels table
    room_id = Column(Integer, ForeignKey("hotel_rooms.id"), nullable=True)  # Link to rooms table
    
    # Booking details
    pricing_token = Column(String(255), nullable=True)  # Token used for booking
    booking_status = Column(String(50), default="PENDING")  # CONFIRMED, PENDING, CANCELLED
    total_amount = Column(Float, nullable=True)  # Total booking amount
    currency = Column(String(10), default="USD")  # Booking currency
    
    # Stay details
    stay_start = Column(String(50))
    stay_end = Column(String(50))
    checkin_date = Column(String(50), nullable=True)
    checkout_date = Column(String(50), nullable=True)
    nights = Column(Integer, nullable=True)
    
    # Guest information (stored as JSON for flexibility)
    guest_details = Column(JSON, nullable=True)  # Store room guests as JSON
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(JSON, nullable=True)  # Store phone as JSON
    
    # Billing information (legacy fields for backward compatibility)
    billing_first_name = Column(String(100))
    billing_last_name = Column(String(100))
    billing_title = Column(String(20))
    billing_type = Column(String(20))
    billing_email = Column(String(255))
    billing_phone = Column(String(50))
    
    # API response data
    booking_data = Column(Text)  # Legacy field
    response_data = Column(Text)  # Legacy field
    api_response = Column(JSON, nullable=True)  # Store full API response as JSON
    correlation_id = Column(String(255), nullable=True)
    session_id = Column(String(255))
    
    # Booking status and cancellation tracking
    status = Column(String(20), default="active", index=True)  # active, cancelled, completed
    cancellation_reason = Column(String(255), nullable=True)
    cancellation_penalty_amount = Column(Float, nullable=True)
    cancellation_penalty_currency = Column(String(10), nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(String(100), nullable=True)  # user or system
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hotel = relationship("Hotel", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")


class Room(Base):
    __tablename__ = "hotel_rooms"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_id = Column(String(255), unique=True, index=True, nullable=False)  # API room ID
    group_id = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    beds = Column(JSON, nullable=True)  # Store beds array as JSON
    total_sleep = Column(Integer, nullable=True)
    room_area = Column(String(50), nullable=True)
    availability = Column(String(50), nullable=True)
    room_rating = Column(String(100), nullable=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=True)  # Foreign key to hotels table
    api_hotel_id = Column(String(255), nullable=True)  # API hotel ID for reference
    
    # Pricing and Service Charge Fields
    currency = Column(String(10), nullable=True)  # Currency code (USD, EUR, etc.)
    base_rate = Column(Float, nullable=True)  # Base room rate
    total_rate = Column(Float, nullable=True)  # Total rate including all charges
    published_rate = Column(Float, nullable=True)  # Published/display rate
    per_night_rate = Column(Float, nullable=True)  # Rate per night
    service_charges = Column(JSON, nullable=True)  # Service charges breakdown
    taxes_and_fees = Column(JSON, nullable=True)  # Taxes and fees breakdown
    additional_charges = Column(JSON, nullable=True)  # Additional charges
    cancellation_policy = Column(JSON, nullable=True)  # Cancellation policy as JSON
    booking_conditions = Column(JSON, nullable=True)  # Booking conditions and restrictions
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    hotel = relationship("Hotel", back_populates="rooms")
    amenities = relationship("RoomAmenity", back_populates="room", cascade="all, delete-orphan")
    images = relationship("RoomImage", back_populates="room", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="room", cascade="all, delete-orphan")


class RoomAmenity(Base):
    __tablename__ = "room_amenities"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("hotel_rooms.id", ondelete="CASCADE"))
    amenity_name = Column(String(255), nullable=False)
    amenity_type = Column(String(50), default="general")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    room = relationship("Room", back_populates="amenities")


class RoomImage(Base):
    __tablename__ = "room_images"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("hotel_rooms.id", ondelete="CASCADE"))
    image_url = Column(String(500), nullable=False)
    size = Column(String(20), nullable=True)  # XL, XXL, XS, etc.
    caption = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    room = relationship("Room", back_populates="images")


class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    search_hash = Column(String(64), unique=True, index=True)  # Hash of search parameters
    search_params = Column(JSON, nullable=False)  # Original search parameters
    search_results = Column(JSON, nullable=False)  # Cached search results
    hotels_count = Column(Integer, default=0)
    api_response_time = Column(Float)  # API response time in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)  # When the search data expires
    is_fresh = Column(Boolean, default=True)  # Whether the data is still fresh