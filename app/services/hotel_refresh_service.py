import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.api.services.hotel_service import HotelService
from app.api.repositories.hotel_repository import HotelRepository
from app.models.hotel_search_models import HotelSearchRequest
from app.models.hotel_entities import Hotel, HotelAmenity, HotelImage
from app.core.logger import logger
import traceback
from datetime import datetime, timedelta


class HotelRefreshService:
    """
    Service class for refreshing hotel data including hotels, amenities, and images.
    Handles batch processing and error recovery for scheduled hotel updates.
    """
    
    def __init__(self):
        self.hotel_service = HotelService()
        self.repository = HotelRepository()
        self.config = self._load_refresh_config()
    
    def _load_refresh_config(self) -> Dict[str, Any]:
        """Load refresh configuration from city demand config"""
        try:
            config_file = Path(__file__).parent.parent / "config" / "city_demand_config.json"
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load refresh configuration: {str(e)}")
            # Return default config
            return {
                'refresh_settings': {
                    'batch_size': 50,
                    'retry_attempts': 3,
                    'retry_delay_seconds': 60,
                    'enable_logging': True
                }
            }
    
    def _get_city_coordinates(self, city_name: str, state: str = None, country: str = None) -> tuple[float, float]:
        """Get coordinates for a city using autosuggest API"""
        try:
            # Create search text
            search_text = city_name
            if state:
                search_text += f", {state}"
            if country:
                search_text += f", {country}"
            
            # Use autosuggest to get location data
            from app.models.autosuggest_model import AutocompleteRequest
            import asyncio
            
            autosuggest_request = AutocompleteRequest(key=search_text)
            autosuggest_result = asyncio.run(self.hotel_service.get_hotel_autosuggestions_async(autosuggest_request))
            
            # Parse the response to get coordinates
            if autosuggest_result and 'data' in autosuggest_result:
                data = autosuggest_result['data']
                if len(data) > 0:
                    # Get the first suggestion (most relevant)
                    first_suggestion = data[0]
                    if 'location' in first_suggestion:
                        location = first_suggestion['location']
                        if 'lat' in location and 'long' in location:
                            return float(location['lat']), float(location['long'])
            
            # Fallback to known coordinates for major cities
            known_coordinates = {
                'New York': (40.7128, -74.0060),
                'Los Angeles': (34.0522, -118.2437),
                'Chicago': (41.8781, -87.6298),
                'Miami': (25.7617, -80.1918),
                'Las Vegas': (36.1699, -115.1398),
                'San Francisco': (37.7749, -122.4194),
                'Boston': (42.3601, -71.0589),
                'Washington': (38.9072, -77.0369),
                'Seattle': (47.6062, -122.3321),
                'Atlanta': (33.7490, -84.3880),
                'Dallas': (32.7767, -96.7970),
                'Houston': (29.7604, -95.3698),
                'Phoenix': (33.4484, -112.0740),
                'Denver': (39.7392, -104.9903),
                'Nashville': (36.1627, -86.7816),
                'Austin': (30.2672, -97.7431),
                'Portland': (45.5152, -122.6784),
                'San Diego': (32.7157, -117.1611),
                'Orlando': (28.5383, -81.3792),
                'Mexico City': (19.4326, -99.1332),
                'Cancun': (21.1619, -86.8515),
                'Guadalajara': (20.6597, -103.3496),
                'Monterrey': (25.6866, -100.3161),
                'Tijuana': (32.5149, -117.0382),
                'Puebla': (19.0414, -98.2063),
                'Merida': (20.9674, -89.5926),
                'Toluca': (19.2925, -99.6569),
                'León': (21.1228, -101.7065),
                'Juárez': (31.6904, -106.4225)
            }
            
            # Try to find coordinates by city name
            for city_key, coords in known_coordinates.items():
                if city_key.lower() in city_name.lower():
                    logger.info(f"Using known coordinates for {city_name}: {coords}")
                    return coords
            
            # Fallback to default coordinates if autosuggest fails
            logger.warning(f"Could not get coordinates for {city_name}, using default coordinates")
            return 0.0, 0.0
            
        except Exception as e:
            logger.error(f"Error getting coordinates for {city_name}: {str(e)}")
            return 0.0, 0.0

    def refresh_hotels_for_city(self, db: Session, city_name: str, state: str = None, country: str = None) -> Dict[str, Any]:
        """
        Refresh hotel data for a specific city.
        This is the main method called by the scheduler.
        """
        start_time = datetime.utcnow()
        refresh_stats = {
            'city_name': city_name,
            'state': state,
            'country': country,
            'start_time': start_time.isoformat(),
            'hotels_processed': 0,
            'hotels_updated': 0,
            'hotels_created': 0,
            'amenities_updated': 0,
            'images_updated': 0,
            'errors': [],
            'status': 'in_progress'
        }
        
        try:
            logger.info(f"Starting hotel refresh for {city_name}, {state}, {country}")
            
            # Get coordinates for the city
            lat, lng = self._get_city_coordinates(city_name, state, country)
            
            # Create search request for the city
            from app.models.hotel_search_models import Occupancy
            
            search_request = HotelSearchRequest(
                place_id=f"{city}, {state}, {country}" if state else f"{city}, {country}",
                lat=lat,
                lng=lng,
                checkin_date="2024-12-01",  # Use a future date for search
                checkout_date="2024-12-02",
                occupancy=[
                    Occupancy(
                        adults=2,
                        childs=0,
                        childages=[]
                    )
                ],
                country_of_residence="US",
                sort=[{"key": "price", "order": "asc"}]
            )
            
            # Search hotels via API
            api_result = self.hotel_service.search_hotels_api_only(search_request, db)
            hotels_data = api_result.get('hotels', [])
            
            if not hotels_data:
                logger.warning(f"No hotels found for {city_name}, {state}, {country}")
                refresh_stats['status'] = 'completed'
                refresh_stats['message'] = 'No hotels found'
                return refresh_stats
            
            # Process hotels in batches
            batch_size = self.config['refresh_settings']['batch_size']
            hotels_processed = 0
            
            for i in range(0, len(hotels_data), batch_size):
                batch = hotels_data[i:i + batch_size]
                batch_result = self._process_hotel_batch(db, batch, city_name)
                
                hotels_processed += batch_result['processed']
                refresh_stats['hotels_updated'] += batch_result['updated']
                refresh_stats['hotels_created'] += batch_result['created']
                refresh_stats['amenities_updated'] += batch_result['amenities_updated']
                refresh_stats['images_updated'] += batch_result['images_updated']
                refresh_stats['errors'].extend(batch_result['errors'])
                
                logger.info(f"Processed batch {i//batch_size + 1}: {batch_result['processed']} hotels")
            
            refresh_stats['hotels_processed'] = hotels_processed
            refresh_stats['status'] = 'completed'
            refresh_stats['end_time'] = datetime.utcnow().isoformat()
            refresh_stats['duration_seconds'] = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Completed hotel refresh for {city_name}: {hotels_processed} hotels processed in {refresh_stats['duration_seconds']:.2f} seconds")
            
        except Exception as e:
            error_msg = f"Error refreshing hotels for {city_name}: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            refresh_stats['status'] = 'error'
            refresh_stats['error_message'] = str(e)
            refresh_stats['end_time'] = datetime.utcnow().isoformat()
            refresh_stats['duration_seconds'] = (datetime.utcnow() - start_time).total_seconds()
            refresh_stats['errors'].append(error_msg)
        
        return refresh_stats
    
    def _process_hotel_batch(self, db: Session, hotels_data: List[Dict], city_name: str) -> Dict[str, Any]:
        """Process a batch of hotels"""
        batch_stats = {
            'processed': 0,
            'updated': 0,
            'created': 0,
            'amenities_updated': 0,
            'images_updated': 0,
            'errors': []
        }
        
        for hotel_data in hotels_data:
            try:
                result = self._process_single_hotel(db, hotel_data, city_name)
                batch_stats['processed'] += 1
                batch_stats['updated'] += result['updated']
                batch_stats['created'] += result['created']
                batch_stats['amenities_updated'] += result['amenities_updated']
                batch_stats['images_updated'] += result['images_updated']
                
            except Exception as e:
                error_msg = f"Error processing hotel {hotel_data.get('id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                batch_stats['errors'].append(error_msg)
                batch_stats['processed'] += 1  # Still count as processed
        
        return batch_stats
    
    def _process_single_hotel(self, db: Session, hotel_data: Dict, city_name: str) -> Dict[str, Any]:
        """Process a single hotel and update/create its data"""
        result = {
            'updated': 0,
            'created': 0,
            'amenities_updated': 0,
            'images_updated': 0
        }
        
        try:
            # Map API response to our hotel data structure
            address_info = hotel_data.get("address", {})
            rate_info = hotel_data.get("rate", {})
            reviews_info = hotel_data.get("reviews", [{}])[0] if hotel_data.get("reviews") else {}
            
            mapped_hotel_data = {
                "id": str(hotel_data.get("id")),
                "name": hotel_data.get("hotelName"),
                "description": hotel_data.get("description", ""),
                "address": address_info.get("line1", ""),
                "city": address_info.get("city", {}).get("name", ""),
                "state": address_info.get("state", {}).get("name", ""),
                "country": address_info.get("country", {}).get("name", ""),
                "postal_code": address_info.get("postalCode", ""),
                "latitude": float(hotel_data.get("lat", 0)) if hotel_data.get("lat") else 0,
                "longitude": float(hotel_data.get("lng", 0)) if hotel_data.get("lng") else 0,
                "star_rating": int(float(hotel_data.get("rating", 0))) if hotel_data.get("rating") else 0,
                "avg_rating": float(reviews_info.get("rating", 0)) if reviews_info.get("rating") else 0,
                "total_reviews": int(reviews_info.get("count", 0)) if reviews_info.get("count") else 0,
            }
            
            # Map facilities to amenities
            amenities = []
            for facility in hotel_data.get("facilities", []):
                amenity_name = facility.get("name", "")
                if amenity_name:
                    # Categorize amenities
                    amenity_type = self._categorize_amenity(amenity_name)
                    amenities.append({
                        "amenity_name": amenity_name,
                        "amenity_type": amenity_type
                    })
            
            # Map images
            images = []
            if hotel_data.get("image"):
                images.append({
                    "image": hotel_data.get("image"),
                    "caption": hotel_data.get("hotelName", ""),
                    "is_primary": True,
                    "sort_order": 0
                })
            
            # Check if hotel exists
            existing_hotel = db.query(Hotel).filter(Hotel.id == mapped_hotel_data['id']).first()
            
            if existing_hotel:
                # Update existing hotel
                for key, value in mapped_hotel_data.items():
                    if hasattr(existing_hotel, key) and value is not None and key != 'id':
                        setattr(existing_hotel, key, value)
                
                # Explicitly set updated_at timestamp
                existing_hotel.updated_at = datetime.utcnow()
                
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
                
                result['updated'] = 1
                result['amenities_updated'] = len(amenities)
                result['images_updated'] = len(images)
                
            else:
                # Create new hotel
                hotel = Hotel(**mapped_hotel_data)
                db.add(hotel)
                db.flush()  # Get the hotel ID
                
                # Add amenities
                for amenity_data in amenities:
                    amenity = HotelAmenity(hotel_id=hotel.id, **amenity_data)
                    db.add(amenity)
                
                # Add images
                for image_data in images:
                    image = HotelImage(hotel_id=hotel.id, **image_data)
                    db.add(image)
                
                db.commit()
                db.refresh(hotel)
                
                result['created'] = 1
                result['amenities_updated'] = len(amenities)
                result['images_updated'] = len(images)
            
        except Exception as e:
            logger.error(f"Error processing single hotel {hotel_data.get('id', 'unknown')}: {str(e)}")
            raise e
        
        return result
    
    def _categorize_amenity(self, amenity_name: str) -> str:
        """Categorize amenity based on its name"""
        amenity_lower = amenity_name.lower()
        
        if any(keyword in amenity_lower for keyword in ["wifi", "internet", "television", "tv", "cable", "satellite"]):
            return "technology"
        elif any(keyword in amenity_lower for keyword in ["pool", "spa", "fitness", "gym", "sauna", "jacuzzi"]):
            return "recreation"
        elif any(keyword in amenity_lower for keyword in ["restaurant", "bar", "cafe", "dining", "breakfast", "food"]):
            return "dining"
        elif any(keyword in amenity_lower for keyword in ["parking", "valet", "garage", "shuttle", "transport"]):
            return "transportation"
        elif any(keyword in amenity_lower for keyword in ["business", "meeting", "conference", "convention"]):
            return "business"
        elif any(keyword in amenity_lower for keyword in ["laundry", "dry", "cleaning", "housekeeping"]):
            return "services"
        elif any(keyword in amenity_lower for keyword in ["pet", "animal", "dog", "cat"]):
            return "pets"
        elif any(keyword in amenity_lower for keyword in ["accessibility", "wheelchair", "disabled", "ada"]):
            return "accessibility"
        else:
            return "general"
    
    def get_refresh_statistics(self, db: Session, hours_back: int = 24) -> Dict[str, Any]:
        """Get refresh statistics for the last N hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Get hotels updated in the last N hours
            recent_hotels = db.query(Hotel).filter(
                Hotel.updated_at >= cutoff_time
            ).count()
            
            # Get total hotels
            total_hotels = db.query(Hotel).count()
            
            # Get amenities count
            total_amenities = db.query(HotelAmenity).count()
            
            # Get images count
            total_images = db.query(HotelImage).count()
            
            return {
                'time_period_hours': hours_back,
                'hotels_updated_recently': recent_hotels,
                'total_hotels': total_hotels,
                'total_amenities': total_amenities,
                'total_images': total_images,
                'last_updated': cutoff_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting refresh statistics: {str(e)}")
            return {'error': str(e)}
    
    def cleanup_old_data(self, db: Session, days_to_keep: int = 30) -> Dict[str, Any]:
        """Clean up old hotel data that hasn't been updated recently"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Find hotels that haven't been updated recently
            old_hotels = db.query(Hotel).filter(
                Hotel.updated_at < cutoff_date
            ).all()
            
            cleanup_stats = {
                'hotels_found': len(old_hotels),
                'hotels_deleted': 0,
                'amenities_deleted': 0,
                'images_deleted': 0,
                'errors': []
            }
            
            for hotel in old_hotels:
                try:
                    # Delete associated amenities
                    amenities_deleted = db.query(HotelAmenity).filter(
                        HotelAmenity.hotel_id == hotel.id
                    ).delete()
                    
                    # Delete associated images
                    images_deleted = db.query(HotelImage).filter(
                        HotelImage.hotel_id == hotel.id
                    ).delete()
                    
                    # Delete the hotel
                    db.delete(hotel)
                    
                    cleanup_stats['hotels_deleted'] += 1
                    cleanup_stats['amenities_deleted'] += amenities_deleted
                    cleanup_stats['images_deleted'] += images_deleted
                    
                except Exception as e:
                    error_msg = f"Error deleting hotel {hotel.id}: {str(e)}"
                    logger.error(error_msg)
                    cleanup_stats['errors'].append(error_msg)
            
            db.commit()
            
            logger.info(f"Cleanup completed: {cleanup_stats['hotels_deleted']} hotels deleted")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return {'error': str(e)}
