"""
Data Population Service for Hotel Filtering
Provides methods to populate database with comprehensive hotel data
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.api.services.hotel_service import HotelService
from app.models.hotel_search_models import HotelSearchRequest
from app.core.config import settings

logger = logging.getLogger(__name__)

class DataPopulationService:
    """Service for populating hotel data for filtering functionality"""
    
    def __init__(self, hotel_service: HotelService):
        self.hotel_service = hotel_service
    
    async def populate_hotels_for_city(
        self, 
        db: Session, 
        city: str, 
        state: str = None, 
        country: str = "US",
        lat: float = None,
        lng: float = None,
        max_hotels: int = 50
    ) -> Dict[str, Any]:
        """
        Populate hotels for a specific city with comprehensive data
        
        Args:
            db: Database session
            city: City name
            state: State name (optional)
            country: Country code (default: US)
            lat: Latitude (optional)
            lng: Longitude (optional)
            max_hotels: Maximum number of hotels to fetch
        
        Returns:
            Dict with population results
        """
        try:
            logger.info(f"Starting hotel population for {city}, {state}, {country}")
            
            # Create search request with required fields
            from app.models.hotel_search_models import Occupancy, SortCriteria
            
            # Use future dates for API calls
            from datetime import datetime, timedelta
            future_date = datetime.now() + timedelta(days=30)
            checkin_date = future_date.strftime("%Y-%m-%d")
            checkout_date = (future_date + timedelta(days=2)).strftime("%Y-%m-%d")
            
            search_request = HotelSearchRequest(
                place_id=f"{city},{state},{country}" if state else f"{city},{country}",
                lat=lat or 40.7128,  # Default to NYC coordinates if not provided
                lng=lng or -74.0060,
                checkin_date=checkin_date,  # Future check-in date
                checkout_date=checkout_date,  # Future check-out date
                occupancy=[Occupancy(adults=2, childs=0, childages=[])],
                country_of_residence="US",
                sort=[SortCriteria(key="price", order="asc")],
                radius=50
            )
            
            # Generate correlation ID
            correlation_id = f"populate_{city}_{country}_{asyncio.get_event_loop().time()}"
            
            # Search and save hotels
            search_result = await self.hotel_service.search_hotels_and_save(
                search_request, 
                correlation_id, 
                db
            )
            
            if search_result.get("status") != "success":
                logger.error(f"Failed to search hotels for {city}: {search_result}")
                return {
                    "status": "error",
                    "message": f"Failed to search hotels for {city}",
                    "details": search_result
                }
            
            hotels_data = search_result.get("data", {}).get("hotels", [])
            logger.info(f"Found {len(hotels_data)} hotels for {city}")
            
            # For each hotel, get pricing data to populate rooms
            populated_rooms = 0
            for hotel in hotels_data:
                try:
                    # Get availability token (you'll need to implement this)
                    # For now, we'll skip room population as it requires availability API
                    logger.info(f"Hotel {hotel['property_id']} saved, rooms will be populated separately")
                except Exception as e:
                    logger.error(f"Error processing hotel {hotel['property_id']}: {str(e)}")
                    continue
            
            return {
                "status": "success",
                "message": f"Successfully populated {len(hotels_data)} hotels for {city}",
                "hotels_count": len(hotels_data),
                "rooms_count": populated_rooms
            }
            
        except Exception as e:
            logger.error(f"Error populating hotels for {city}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error populating hotels for {city}: {str(e)}"
            }
    
    async def populate_multiple_cities(
        self, 
        db: Session, 
        cities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Populate hotels for multiple cities
        
        Args:
            db: Database session
            cities: List of city dictionaries with keys: city, state, country, lat, lng, max_hotels
        
        Returns:
            Dict with population results for all cities
        """
        results = {}
        total_hotels = 0
        
        for city_data in cities:
            city_name = city_data.get("city")
            logger.info(f"Processing city: {city_name}")
            
            result = await self.populate_hotels_for_city(
                db=db,
                city=city_data.get("city"),
                state=city_data.get("state"),
                country=city_data.get("country", "US"),
                lat=city_data.get("lat"),
                lng=city_data.get("lng"),
                max_hotels=city_data.get("max_hotels", 50)
            )
            
            results[city_name] = result
            if result.get("status") == "success":
                total_hotels += result.get("hotels_count", 0)
        
        return {
            "status": "completed",
            "message": f"Processed {len(cities)} cities",
            "total_hotels": total_hotels,
            "city_results": results
        }
    
    async def get_population_stats(self, db: Session) -> Dict[str, Any]:
        """
        Get current database population statistics
        
        Args:
            db: Database session
            
        Returns:
            Dict with population statistics
        """
        try:
            from app.models.hotel_entities import Hotel, HotelAmenity, HotelImage, Room, RoomAmenity, RoomImage
            
            # Count hotels
            hotels_count = db.query(Hotel).count()
            
            # Count amenities
            hotel_amenities_count = db.query(HotelAmenity).count()
            room_amenities_count = db.query(RoomAmenity).count()
            
            # Count images
            hotel_images_count = db.query(HotelImage).count()
            room_images_count = db.query(RoomImage).count()
            
            # Count rooms
            rooms_count = db.query(Room).count()
            
            # Get unique amenity types
            amenity_types = db.query(HotelAmenity.amenity_type).distinct().all()
            amenity_types = [t[0] for t in amenity_types]
            
            # Get star rating distribution
            star_ratings = db.query(Hotel.star_rating).all()
            star_distribution = {}
            for rating in star_ratings:
                star = rating[0]
                star_distribution[star] = star_distribution.get(star, 0) + 1
            
            return {
                "status": "success",
                "statistics": {
                    "hotels": hotels_count,
                    "rooms": rooms_count,
                    "hotel_amenities": hotel_amenities_count,
                    "room_amenities": room_amenities_count,
                    "hotel_images": hotel_images_count,
                    "room_images": room_images_count,
                    "amenity_types": amenity_types,
                    "star_rating_distribution": star_distribution
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting population stats: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting population stats: {str(e)}"
            }
