from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.hotel_entities import Hotel, HotelAmenity, HotelImage, Booking, SearchHistory, Room, RoomAmenity, RoomImage
from app.core.logger import logger
import json
import hashlib
from datetime import datetime, timedelta
from typing import List


class HotelRepository:
    def __init__(self):
        self.logger = logger
    def save_hotel_details(self, db: Session, hotel_data: dict, amenities: list, images: list):
        # OPTIMIZED: Use bulk operations for better performance
        api_hotel_id = hotel_data.get('api_hotel_id')
        existing_hotel = db.query(Hotel).filter(Hotel.api_hotel_id == api_hotel_id).first()
        
        if existing_hotel:
            # Hotel already exists, update it with new data
            for key, value in hotel_data.items():
                if hasattr(existing_hotel, key) and value is not None and key != 'api_hotel_id':
                    setattr(existing_hotel, key, value)
            
            # OPTIMIZED: Bulk delete and insert for amenities and images
            db.query(HotelAmenity).filter(HotelAmenity.hotel_id == existing_hotel.id).delete()
            db.query(HotelImage).filter(HotelImage.hotel_id == existing_hotel.id).delete()
            
            # Bulk insert amenities
            if amenities:
                amenity_objects = [HotelAmenity(hotel_id=existing_hotel.id, **amenity_data) for amenity_data in amenities]
                db.bulk_save_objects(amenity_objects)
            
            # Bulk insert images
            if images:
                image_objects = [HotelImage(hotel_id=existing_hotel.id, **image_data) for image_data in images]
                db.bulk_save_objects(image_objects)
            
            db.commit()
            db.refresh(existing_hotel)
            return existing_hotel
        else:
            # Hotel doesn't exist, create new one
            try:
                hotel = Hotel(**hotel_data)
                db.add(hotel)
                db.flush()  # Get the hotel ID
                
                # OPTIMIZED: Bulk insert amenities and images
                if amenities:
                    amenity_objects = [HotelAmenity(hotel_id=hotel.id, **amenity_data) for amenity_data in amenities]
                    db.bulk_save_objects(amenity_objects)
                
                if images:
                    image_objects = [HotelImage(hotel_id=hotel.id, **image_data) for image_data in images]
                    db.bulk_save_objects(image_objects)
                
                db.commit()
                db.refresh(hotel)
                return hotel
                
            except IntegrityError as e:
                # Handle duplicate key errors
                db.rollback()
                
                # Check if it's a duplicate primary key error
                if "Duplicate entry" in str(e) and "PRIMARY" in str(e):
                    # Try to find the existing hotel by API hotel ID
                    existing_hotel = db.query(Hotel).filter(Hotel.api_hotel_id == hotel_data.get('api_hotel_id')).first()
                    if existing_hotel:
                        # Update the existing hotel instead
                        for key, value in hotel_data.items():
                            if hasattr(existing_hotel, key) and value is not None and key != 'api_hotel_id':
                                setattr(existing_hotel, key, value)
                        
                        # Update amenities
                        db.query(HotelAmenity).filter(HotelAmenity.hotel_id == existing_hotel.id).delete()
                        for amenity_data in amenities:
                            amenity = HotelAmenity(hotel_id=existing_hotel.id, **amenity_data)
                            db.add(amenity)
                        
                        # Update images
                        db.query(HotelImage).filter(HotelImage.hotel_id == existing_hotel.id).delete()
                        for image_data in images:
                            image = HotelImage(hotel_id=existing_hotel.id, **image_data)
                            db.add(image)
                        
                        db.commit()
                        db.refresh(existing_hotel)
                        return existing_hotel
                    else:
                        # If we can't find the existing hotel, re-raise the error
                        raise e
                else:
                    # Re-raise other integrity errors
                    raise e

    def save_room_details(self, db: Session, room_data: dict, amenities: list, images: list):
        """Save room details with amenities and images"""
        try:
            # Check if room already exists by room_id
            existing_room = db.query(Room).filter(Room.room_id == room_data.get('room_id')).first()
            if existing_room:
                self.logger.info(f"Room with ID {room_data.get('room_id')} already exists, updating...")
                # Update existing room
                for key, value in room_data.items():
                    if hasattr(existing_room, key):
                        setattr(existing_room, key, value)
                
                # Clear existing amenities and images
                db.query(RoomAmenity).filter(RoomAmenity.room_id == existing_room.id).delete()
                db.query(RoomImage).filter(RoomImage.room_id == existing_room.id).delete()
                
                # Add new amenities
                for amenity_data in amenities:
                    amenity = RoomAmenity(room_id=existing_room.id, **amenity_data)
                    db.add(amenity)
                
                # Add new images
                for image_data in images:
                    image = RoomImage(room_id=existing_room.id, **image_data)
                    db.add(image)
                
                db.commit()
                db.refresh(existing_room)
                return existing_room
            else:
                # Create new room
                room = Room(**room_data)
                db.add(room)
                db.flush()  # Get the room ID
                
                # Save amenities
                for amenity_data in amenities:
                    amenity = RoomAmenity(room_id=room.id, **amenity_data)
                    db.add(amenity)
                
                # Save images
                for image_data in images:
                    image = RoomImage(room_id=room.id, **image_data)
                    db.add(image)
                
                db.commit()
                db.refresh(room)
                return room
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error saving room details: {str(e)}")
            self.logger.error(f"Error type: {type(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise e

    def get_room_by_id(self, db: Session, room_id: int):
        """Get room by internal ID"""
        return db.query(Room).filter(Room.id == room_id).first()

    def get_room_by_api_id(self, db: Session, api_room_id: str):
        """Get room by API room ID"""
        return db.query(Room).filter(Room.room_id == api_room_id).first()

    def get_rooms_by_hotel_id(self, db: Session, hotel_id: int):
        """Get all rooms for a specific hotel by internal hotel ID"""
        return db.query(Room).filter(Room.hotel_id == hotel_id).all()
    
    def get_rooms_by_api_hotel_id(self, db: Session, api_hotel_id: str):
        """Get all rooms for a specific hotel by API hotel ID"""
        return db.query(Room).filter(Room.api_hotel_id == api_hotel_id).all()
    
    def get_room_with_details(self, db: Session, room_id: int):
        """Get room with amenities and images"""
        room = db.query(Room).filter(Room.id == room_id).first()
        if room:
            # Load amenities and images
            room.amenities = db.query(RoomAmenity).filter(RoomAmenity.room_id == room_id).all()
            room.images = db.query(RoomImage).filter(RoomImage.room_id == room_id).all()
        return room
    
    def get_rooms_with_details_by_hotel(self, db: Session, api_hotel_id: str):
        """Get all rooms with amenities and images for a specific hotel by API hotel ID"""
        rooms = db.query(Room).filter(Room.api_hotel_id == api_hotel_id).all()
        for room in rooms:
            room.amenities = db.query(RoomAmenity).filter(RoomAmenity.room_id == room.id).all()
            room.images = db.query(RoomImage).filter(RoomImage.room_id == room.id).all()
        return rooms

    def save_booking_details(self, db: Session, booking_request: dict, api_response: dict, hotel_id: str, session_id: str):
        # Extract data from the response
        response_data = api_response.get('data', {})
        
        # Extract billing information from booking request
        billing_contact = booking_request.get('billingContact', {})
        contact_info = billing_contact.get('contact', {})
        
        # Extract stay period
        stay_period = booking_request.get('stayPeriod', {})
        
        booking = Booking(
            hotel_id=hotel_id,
            session_id=session_id,
            booking_data=json.dumps(booking_request),
            response_data=json.dumps(api_response),
            booking_id=response_data.get('bookingId'),
            booking_ref_id=booking_request.get('bookingRefId'),
            recommendation_id=booking_request.get('recommendationId'),
            stay_start=stay_period.get('start'),
            stay_end=stay_period.get('end'),
            billing_first_name=billing_contact.get('firstName'),
            billing_last_name=billing_contact.get('lastName'),
            billing_title=billing_contact.get('title'),
            billing_type=billing_contact.get('type'),
            billing_email=contact_info.get('email'),
            billing_phone=contact_info.get('phone'),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    def get_hotel_by_id(self, db: Session, hotel_id: int):
        return db.query(Hotel).filter(Hotel.id == hotel_id).first()

    def get_booking_by_id(self, db: Session, booking_id: str):
        return db.query(Booking).filter(Booking.booking_id == booking_id).first()

    def get_all_hotels(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(Hotel).offset(skip).limit(limit).all()

    def get_all_bookings(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(Booking).offset(skip).limit(limit).all()
    
    def generate_search_hash(self, search_params: dict) -> str:
        """Generate a hash for search parameters to identify unique searches"""
        # Sort parameters to ensure consistent hashing
        sorted_params = json.dumps(search_params, sort_keys=True)
        return hashlib.sha256(sorted_params.encode()).hexdigest()
    
    def get_search_history(self, db: Session, search_hash: str) -> SearchHistory:
        """Get search history by hash"""
        return db.query(SearchHistory).filter(SearchHistory.search_hash == search_hash).first()
    
    def save_search_history(self, db: Session, search_params: dict, search_results: list, 
                          response_time: float, cache_duration_minutes: int = 30) -> SearchHistory:
        """Save search history with results"""
        search_hash = self.generate_search_hash(search_params)
        expires_at = datetime.utcnow() + timedelta(minutes=cache_duration_minutes)
        
        # Check if search already exists
        existing_search = self.get_search_history(db, search_hash)
        
        if existing_search:
            # Update existing search
            existing_search.search_results = search_results
            existing_search.hotels_count = len(search_results)
            existing_search.api_response_time = response_time
            existing_search.updated_at = datetime.utcnow()
            existing_search.expires_at = expires_at
            existing_search.is_fresh = True
            db.commit()
            db.refresh(existing_search)
            return existing_search
        else:
            # Create new search history
            search_history = SearchHistory(
                search_hash=search_hash,
                search_params=search_params,
                search_results=search_results,
                hotels_count=len(search_results),
                api_response_time=response_time,
                expires_at=expires_at,
                is_fresh=True
            )
            db.add(search_history)
            db.commit()
            db.refresh(search_history)
            return search_history
    
    def is_search_fresh(self, db: Session, search_hash: str) -> bool:
        """Check if search data is still fresh (not expired)"""
        search_history = self.get_search_history(db, search_hash)
        if not search_history:
            return False
        
        # Check if expired
        if datetime.utcnow() > search_history.expires_at:
            search_history.is_fresh = False
            db.commit()
            return False
        
        return search_history.is_fresh
    
    def get_fresh_search_results(self, db: Session, search_hash: str) -> list:
        """Get fresh search results if available"""
        search_history = self.get_search_history(db, search_hash)
        if search_history and self.is_search_fresh(db, search_hash):
            return search_history.search_results
        return []
    
    def cleanup_expired_searches(self, db: Session, max_entries: int = 1000):
        """Clean up expired search entries"""
        # Mark expired searches as not fresh
        expired_searches = db.query(SearchHistory).filter(
            SearchHistory.expires_at < datetime.utcnow()
        ).all()
        
        for search in expired_searches:
            search.is_fresh = False
        
        # Remove old entries if we exceed max_entries
        total_entries = db.query(SearchHistory).count()
        if total_entries > max_entries:
            # Delete oldest entries
            old_entries = db.query(SearchHistory).order_by(
                SearchHistory.created_at.asc()
            ).limit(total_entries - max_entries).all()
            
            for entry in old_entries:
                db.delete(entry)
        
        db.commit()
    
    def update_booking_cancellation(self, db: Session, booking_id: str, cancellation_data: dict) -> Booking:
        """
        Update booking with cancellation information
        
        Args:
            db: Database session
            booking_id: Booking ID to update
            cancellation_data: Dictionary containing cancellation details
            
        Returns:
            Updated booking object
        """
        try:
            # Find the booking
            booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
            
            if not booking:
                raise ValueError(f"Booking with ID {booking_id} not found")
            
            # Update booking with cancellation data
            booking.status = "cancelled"
            booking.cancellation_reason = cancellation_data.get("reason", "Customer request")
            booking.cancellation_penalty_amount = cancellation_data.get("penalty_amount")
            booking.cancellation_penalty_currency = cancellation_data.get("penalty_currency", "USD")
            booking.cancelled_at = datetime.utcnow()
            booking.cancelled_by = cancellation_data.get("cancelled_by", "system")
            booking.updated_at = datetime.utcnow().isoformat()
            
            # Update response data with cancellation details
            if cancellation_data.get("api_response"):
                booking.response_data = json.dumps(cancellation_data["api_response"])
            
            db.commit()
            db.refresh(booking)
            
            self.logger.info(f"Successfully updated booking {booking_id} with cancellation status")
            return booking
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating booking cancellation: {str(e)}")
            raise e
    
    def get_booking_by_id(self, db: Session, booking_id: str) -> Booking:
        """Get booking by booking ID"""
        return db.query(Booking).filter(Booking.booking_id == booking_id).first()
    
    def get_cancelled_bookings(self, db: Session, limit: int = 100) -> List[Booking]:
        """Get list of cancelled bookings"""
        return db.query(Booking).filter(Booking.status == "cancelled").order_by(Booking.cancelled_at.desc()).limit(limit).all()
    
    def get_booking_statistics(self, db: Session) -> dict:
        """Get booking statistics including cancellation rates"""
        try:
            total_bookings = db.query(Booking).count()
            active_bookings = db.query(Booking).filter(Booking.status == "active").count()
            cancelled_bookings = db.query(Booking).filter(Booking.status == "cancelled").count()
            completed_bookings = db.query(Booking).filter(Booking.status == "completed").count()
            
            return {
                "total_bookings": total_bookings,
                "active_bookings": active_bookings,
                "cancelled_bookings": cancelled_bookings,
                "completed_bookings": completed_bookings,
                "cancellation_rate": (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Error getting booking statistics: {str(e)}")
            return {}
