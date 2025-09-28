import os
import json
from pathlib import Path
from app.models.autosuggest_model import AutocompleteRequest
from app.utilities.http_client import post_request
from app.models.hotel_search_models import HotelSearchRequest, HotelSearchResponse, HotelDetailsResponse, AvailabilityRequest, AvailabilityResponse, PriceRequest, PriceResponse, BookHotelRequest, BookHotelResponse, CancelBookingRequest, CancelBookingResponse
from app.services.auth_service import AuthService
import requests
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
import httpx
from app.api.repositories.hotel_repository import HotelRepository
from app.models.hotel_entities import RoomAmenity, RoomImage, Hotel, HotelAmenity, HotelImage, Room
from app.utilities.message_loader import message_loader
from app.core.logger import logger
import traceback
import asyncio
from typing import List, Dict, Any
from datetime import datetime

# Load JSON configuration
def load_config():
    config_file = os.getenv("API_CONFIG_FILE", "api_config.json")
    config_path = Path(__file__).parent.parent.parent / "config" / config_file
    with open(config_path, "r") as f:
        return json.load(f)

config = load_config()

class HotelService:
    def __init__(self):
        self.repository = HotelRepository()

    async def search_and_save_hotels(self, db: Session, request: HotelSearchRequest):
        url = f"{config['api']['base_url']}{config['api']['endpoints']['hotel_search']}"
        # exclude optional fields
        payload = request.model_dump(exclude_none=True)

        headers = {
            "x-api-key": config["headers"]["default"]["x-api-key"],
            "accept-language": config["headers"]["default"]["accept-language"],
            "content-type": config["headers"]["default"]["content-type"]
        }
        response = requests.post(url, headers=headers, json=payload, timeout=config["timeouts"]["default"])
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"{message_loader.get_error_message('hotelier_service_error')}: {response.text}")
        response.raise_for_status()
        data = response.json()
        hotels_saved = []
        # Handle the actual response structure: data.data.hotels
        hotels_data = data.get("data", {}).get("hotels", [])
        for h in hotels_data:
            # Map the actual API response fields to our hotel data structure
            address_info = h.get("address", {})
            rate_info = h.get("rate", {})
            reviews_info = h.get("reviews", [{}])[0] if h.get("reviews") else {}
            
            # Extract amenities and images for database storage
            amenities = [{"amenity_name": facility.get("name", "")} for facility in h.get("facilities", [])]
            images = []
            if h.get("image"):
                images = [{"image": h.get("image"), "caption": h.get("hotelName", "")}]
            
            hotel_data = {
                "id": str(h.get("id")),  # Primary key - API hotel ID
                "api_hotel_id": str(h.get("id")),  # Store API hotel ID
                "name": h.get("hotelName"),
                "description": h.get("description", ""),  # Optional field - not provided in current API response
                "star_rating": int(h.get("rating", 0)) if h.get("rating") else None,
                "latitude": float(h.get("lat", 0)) if h.get("lat") else None,
                "longitude": float(h.get("lng", 0)) if h.get("lng") else None,
                "address": address_info.get("line1", ""),
                "city": address_info.get("city", {}).get("name", ""),
                "state": address_info.get("state", {}).get("name", "") if address_info.get("state") else "",
                "country": address_info.get("country", {}).get("name", ""),
                "postal_code": address_info.get("postalCode", ""),  # Optional field - not provided in current API response
                "phone": h.get("phone", ""),  # Optional field - not provided in current API response
                "email": h.get("email", ""),  # Optional field - not provided in current API response
                "website": h.get("website", ""),  # Optional field - not provided in current API response
                "avg_rating": float(reviews_info.get("rating", 0)) if reviews_info.get("rating") else None,
                "total_reviews": int(reviews_info.get("count", 0)) if reviews_info.get("count") else None
            }
            
            # Save hotel to database
            saved_hotel = self.repository.save_hotel_details(db, hotel_data, amenities, images)
            hotels_saved.append(saved_hotel)
        
        return hotels_saved

    async def search_and_save_hotels_async(self, db: Session, request: HotelSearchRequest):
        """
        Search for hotels and save hotel details to database asynchronously.
        
        Args:
            db: Database session
            request: HotelSearchRequest with search criteria
            
        Returns:
            List of saved hotel objects from database
        """
        try:
            logger.info(f"Calling Xeni API asynchronously for hotel search and save")
            
            url = f"{config['api']['base_url']}{config['api']['endpoints']['hotel_search']}"
            payload = request.model_dump(exclude_none=True)
            headers = {
                "x-api-key": config["headers"]["default"]["x-api-key"],
                "accept-language": config["headers"]["default"]["accept-language"],
                "content-type": config["headers"]["default"]["content-type"]
            }
            
            async with httpx.AsyncClient(timeout=config["timeouts"]["default"]) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    hotels_data = data.get("data", {}).get("hotels", [])
                    hotels_saved = []
                    
                    for h in hotels_data:
                        # Map the actual API response fields to our hotel data structure
                        address_info = h.get("address", {})
                        rate_info = h.get("rate", {})
                        reviews_info = h.get("reviews", [{}])[0] if h.get("reviews") else {}
                        
                        # Extract amenities and images for database storage
                        amenities = [{"amenity_name": facility.get("name", "")} for facility in h.get("facilities", [])]
                        images = []
                        if h.get("image"):
                            images = [{"image": h.get("image"), "caption": h.get("hotelName", "")}]
                        
                        hotel_data = {
                            "id": str(h.get("id")),  # Primary key - API hotel ID
                            "api_hotel_id": str(h.get("id")),  # Store API hotel ID
                            "name": h.get("hotelName"),
                            "description": h.get("description", ""),  # Optional field - not provided in current API response
                            "star_rating": int(h.get("rating", 0)) if h.get("rating") else None,
                            "latitude": float(h.get("lat", 0)) if h.get("lat") else None,
                            "longitude": float(h.get("lng", 0)) if h.get("lng") else None,
                            "address": address_info.get("line1", ""),
                            "city": address_info.get("city", {}).get("name", ""),
                            "state": address_info.get("state", {}).get("name", "") if address_info.get("state") else "",
                            "country": address_info.get("country", {}).get("name", ""),
                            "postal_code": address_info.get("postalCode", ""),  # Optional field - not provided in current API response
                            "phone": h.get("phone", ""),  # Optional field - not provided in current API response
                            "email": h.get("email", ""),  # Optional field - not provided in current API response
                            "website": h.get("website", ""),  # Optional field - not provided in current API response
                            "avg_rating": float(reviews_info.get("rating", 0)) if reviews_info.get("rating") else None,
                            "total_reviews": int(reviews_info.get("count", 0)) if reviews_info.get("count") else None
                        }
                        
                        # Save hotel to database
                        saved_hotel = self.repository.save_hotel_details(db, hotel_data, amenities, images)
                        hotels_saved.append(saved_hotel)
                        
                        # Save pricing data as a representative room if rate info is available
                        if rate_info and rate_info.get('baseRate'):
                            try:
                                from app.models.hotel_entities import Room
                                
                                # Check if representative room already exists
                                existing_room = db.query(Room).filter(
                                    Room.room_id == f"hotel_search_{h.get('id')}_representative"
                                ).first()
                                
                                if existing_room:
                                    # Update existing representative room with new pricing
                                    existing_room.currency = rate_info.get("currency", "USD")
                                    existing_room.base_rate = float(rate_info.get("baseRate", 0))
                                    existing_room.total_rate = float(rate_info.get("totalRate", rate_info.get("baseRate", 0)))
                                    existing_room.published_rate = float(rate_info.get("publishedRate", rate_info.get("baseRate", 0)))
                                    existing_room.per_night_rate = float(rate_info.get("perNightRate", rate_info.get("baseRate", 0)))
                                    existing_room.updated_at = datetime.utcnow()
                                    db.commit()
                                    logger.info(f"Updated representative room pricing for hotel {saved_hotel.name}: ${rate_info.get('baseRate')}")
                                else:
                                    # Create a new representative room with pricing data
                                    room_data = {
                                        "room_id": f"hotel_search_{h.get('id')}_representative",
                                        "group_id": "representative",
                                        "name": f"Representative Room - {h.get('hotelName', 'Hotel')}",
                                        "beds": [],
                                        "total_sleep": 2,  # Default assumption
                                        "room_area": None,
                                        "availability": "1",  # Assume available
                                        "room_rating": None,
                                        "hotel_id": saved_hotel.id,
                                        "api_hotel_id": str(h.get("id")),
                                        "currency": rate_info.get("currency", "USD"),
                                        "base_rate": float(rate_info.get("baseRate", 0)),
                                        "total_rate": float(rate_info.get("totalRate", rate_info.get("baseRate", 0))),
                                        "published_rate": float(rate_info.get("publishedRate", rate_info.get("baseRate", 0))),
                                        "per_night_rate": float(rate_info.get("perNightRate", rate_info.get("baseRate", 0))),
                                        "service_charges": 0,
                                        "taxes_and_fees": None,
                                        "additional_charges": None,
                                        "cancellation_policy": [{"text": "Standard cancellation policy"}],
                                        "booking_conditions": None
                                    }
                                    
                                    # Save the representative room
                                    representative_room = Room(**room_data)
                                    db.add(representative_room)
                                    db.commit()
                                    db.refresh(representative_room)
                                    
                                    logger.info(f"Saved representative room with pricing for hotel {saved_hotel.name}: ${rate_info.get('baseRate')}")
                                
                            except Exception as room_error:
                                logger.warning(f"Failed to save representative room for hotel {saved_hotel.name}: {str(room_error)}")
                                # Continue with hotel saving even if room saving fails
                    
                    logger.info(f"Successfully saved {len(hotels_saved)} hotels to database")
                    return hotels_saved
                    
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"Hotel search API error: {error_msg}")
                    raise HTTPException(status_code=response.status_code, detail=f"Hotel search API error: {error_msg}")
                    
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"Hotel search request error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Hotel search request error: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Hotel search unexpected error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Hotel search error: {error_msg}")

    async def save_rooms_from_api_data_async(self, db: Session, api_data: Dict[str, Any], hotel_id: str):
        """
        Save rooms to database from existing API data without making another API call.
        
        Args:
            db: Database session
            api_data: API response data containing rooms
            hotel_id: Hotel identifier
            
        Returns:
            List of saved room objects from database
        """
        try:
            logger.info(f"Saving rooms from API data to database for hotel: {hotel_id}")
            
            rooms_data = api_data.get("data", {}).get("roomLists", [])
            logger.info(f"Found {len(rooms_data)} rooms in API response")
            
            rooms_saved = []
            
            for room_data in rooms_data:
                logger.info(f"Processing room: {room_data.get('roomId', 'unknown')} - {room_data.get('name', 'unknown')}")
                
                # Map the API response fields to our room data structure
                # Find the hotel by API hotel ID to get the internal hotel ID
                hotel = db.query(Hotel).filter(Hotel.api_hotel_id == hotel_id).first()
                if not hotel:
                    logger.warning(f"Hotel with API ID {hotel_id} not found in database, saving room without hotel reference")
                    internal_hotel_id = None
                else:
                    internal_hotel_id = hotel.id
                
                
                # Extract pricing information from API response
                # Check if pricing is in the 'extra' array (new structure)
                price_info = {}
                rate_info = room_data.get("rate", {})
                pricing_info = room_data.get("pricing", {})
                charges_info = room_data.get("charges", {})
                
                # First check if price is directly in room_data
                if "price" in room_data:
                    price_info = room_data.get("price", {})
                # If not, check in the 'extra' array
                elif "extra" in room_data and isinstance(room_data.get("extra"), list) and len(room_data.get("extra", [])) > 0:
                    extra_data = room_data.get("extra")[0]  # Get first extra item
                    price_info = extra_data.get("price", {})
                    # Also extract other useful data from extra
                    if "cancellationPolicies" in extra_data:
                        room_data["cancellationPolicy"] = extra_data.get("cancellationPolicies", [])
                    if "policies" in extra_data:
                        room_data["bookingConditions"] = extra_data.get("policies", [])
                    if "boardBasis" in extra_data:
                        room_data["boardBasis"] = extra_data.get("boardBasis")
                    if "refundability" in extra_data:
                        room_data["refundability"] = extra_data.get("refundability")
                    # Extract rateId as room identifier
                    if "rateId" in extra_data and isinstance(extra_data.get("rateId"), list) and len(extra_data.get("rateId", [])) > 0:
                        rate_id = extra_data.get("rateId")[0]  # Get first rateId
                        room_data["rateId"] = rate_id
                        
                        # Look up rooms_id from rate_plans table
                        rooms_id = self.get_rooms_id_from_rate_id(db, rate_id)
                        if rooms_id:
                            room_data["rooms_id"] = rooms_id
                            logger.info(f"Found rooms_id {rooms_id} for rateId {rate_id}")
                        else:
                            logger.warning(f"Could not find rooms_id for rateId {rate_id}, using rateId as fallback")
                            room_data["rooms_id"] = rate_id
                
                # Log pricing data for debugging
                room_identifier = room_data.get('roomId') or room_data.get('groupId', 'unknown')
                logger.debug(f"Price info for room {room_identifier}: {price_info}")
                logger.debug(f"Rate info for room {room_identifier}: {rate_info}")
                logger.debug(f"Pricing info for room {room_identifier}: {pricing_info}")
                logger.debug(f"Extra data for room {room_identifier}: {room_data.get('extra', [])}")
                
                room_info = {
                    "room_id": room_data.get("rooms_id") or room_data.get("roomId") or room_data.get("rateId") or room_data.get("groupId"),  # Use rooms_id as primary identifier
                    "group_id": room_data.get("groupId"),
                    "name": room_data.get("name"),
                    "beds": room_data.get("beds", []),
                    "total_sleep": room_data.get("totalSleep"),
                    "room_area": room_data.get("roomArea"),
                    "availability": room_data.get("availability"),
                    "room_rating": room_data.get("roomRating"),
                    "hotel_id": internal_hotel_id,  # Internal hotel ID
                    "api_hotel_id": hotel_id,  # API hotel ID for reference
                    
                    # Pricing and Service Charge Fields - Updated to handle price object
                    "currency": price_info.get("currency") or rate_info.get("currency") or pricing_info.get("currency"),
                    "base_rate": price_info.get("baseRate") or rate_info.get("baseRate") or pricing_info.get("baseRate"),
                    "total_rate": price_info.get("total") or rate_info.get("totalRate") or pricing_info.get("totalRate"),
                    "published_rate": price_info.get("publishedRate") or rate_info.get("publishedRate") or pricing_info.get("publishedRate"),
                    "per_night_rate": price_info.get("perNightStay") or rate_info.get("perNightRate") or pricing_info.get("perNightRate"),
                    "service_charges": price_info.get("TaxAndExtras") if price_info.get("TaxAndExtras") is not None else (charges_info.get("serviceCharges") or room_data.get("serviceCharges")),
                    "taxes_and_fees": charges_info.get("taxesAndFees") or room_data.get("taxesAndFees"),
                    "additional_charges": charges_info.get("additionalCharges") or room_data.get("additionalCharges"),
                    "cancellation_policy": room_data.get("cancellationPolicy"),
                    "booking_conditions": room_data.get("bookingConditions")
                }
                
                # Log final pricing data being saved
                logger.debug(f"Final pricing data for room {room_data.get('roomId')}: base_rate={room_info.get('base_rate')}, total_rate={room_info.get('total_rate')}, published_rate={room_info.get('published_rate')}, per_night_rate={room_info.get('per_night_rate')}")
                
                # Debug: Log the entire room_info dictionary to see what's causing the issue
                logger.info(f"Room info dictionary for room {room_data.get('roomId')}: {room_info}")
                
                # Map room amenities
                amenities = []
                for amenity_name in room_data.get("roomAmenities", []):
                    amenity_type = "general"
                    if any(keyword in amenity_name.lower() for keyword in ["wifi", "internet", "television", "tv", "cable"]):
                        amenity_type = "technology"
                    elif any(keyword in amenity_name.lower() for keyword in ["bathroom", "shower", "toilet", "soap", "shampoo", "towels"]):
                        amenity_type = "bathroom"
                    elif any(keyword in amenity_name.lower() for keyword in ["kitchen", "refrigerator", "microwave", "coffee", "tea", "cookware"]):
                        amenity_type = "kitchen"
                    
                    amenity_data = {
                        "amenity_name": amenity_name,
                        "amenity_type": amenity_type
                    }
                    logger.debug(f"Amenity data for room {room_data.get('roomId')}: {amenity_data}")
                    amenities.append(amenity_data)
                
                # Map room images
                images = []
                for idx, image_group in enumerate(room_data.get("images", [])):
                    for link in image_group.get("links", []):
                        image_data = {
                            "image_url": link.get("url"),
                            "size": link.get("size", "XL"),  # Default to XL if not specified
                            "caption": image_group.get("caption", ""),
                            "is_primary": idx == 0,  # First image group is primary
                            "sort_order": idx
                        }
                        logger.debug(f"Image data for room {room_data.get('roomId')}: {image_data}")
                        images.append(image_data)
                
                # Save room to database (non-blocking)
                try:
                    logger.info(f"Saving room to database: {room_info.get('room_id')} - {room_info.get('name')}")
                    logger.info(f"Amenities list: {amenities}")
                    logger.info(f"Images list: {images}")
                    saved_room = await asyncio.to_thread(
                        self.repository.save_room_details, db, room_info, amenities, images
                    )
                    logger.info(f"Successfully saved room: {saved_room.id} - {saved_room.name}")
                    rooms_saved.append(saved_room)
                except Exception as save_error:
                    logger.error(f"Error saving room {room_info.get('room_id')}: {str(save_error)}")
                    continue
            
            logger.info(f"Successfully saved {len(rooms_saved)} rooms to database from API data")
            return rooms_saved
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Save rooms from API data error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Save rooms error: {error_msg}")

    def search_hotels_api_only(self, request: HotelSearchRequest, db: Session = None):
        """Search hotels via API with search history and freshness checking"""
        # Check if search caching is enabled
        cache_enabled = config.get("search_cache", {}).get("enabled", False)
        
        if cache_enabled and db:
            return self._search_hotels_with_cache(request, db)
        else:
            return self._search_hotels_direct(request)
    
    def _search_hotels_with_cache(self, request: HotelSearchRequest, db: Session):
        """Search hotels with caching and freshness checking"""
        import time
        
        # Prepare search parameters
        payload = request.model_dump(exclude_none=True)
        # Note: API doesn't accept page and limit parameters
        
        # Generate search hash
        search_hash = self.repository.generate_search_hash(payload)
        
        # Check if we have fresh cached results
        cached_results = self.repository.get_fresh_search_results(db, search_hash)
        if cached_results:
            logger.info(f"Cache hit for search hash: {search_hash[:8]}...")
            return {
                "hotels": cached_results
            }
        
        logger.info(f"Cache miss for search hash: {search_hash[:8]}... Making fresh API call")
        
        # Make fresh API call
        start_time = time.time()
        try:
            result = self._search_hotels_direct(request)
            response_time = time.time() - start_time
            
            # Save successful search history
            cache_duration = config.get("search_cache", {}).get("cache_duration_minutes", 30)
            self.repository.save_search_history(
                db, payload, result["hotels"], response_time, cache_duration
            )
            
            logger.info(f"Search completed successfully and saved to history")
            
        except Exception as e:
            response_time = time.time() - start_time
            
            # Save failed search history for tracking
            cache_duration = config.get("search_cache", {}).get("cache_duration_minutes", 30)
            self.repository.save_search_history(
                db, payload, [], response_time, cache_duration
            )
            
            logger.warning(f"Search failed but saved to history for tracking: {str(e)}")
            raise e
        
        # Cleanup old searches if needed
        max_entries = config.get("search_cache", {}).get("max_cache_entries", 1000)
        self.repository.cleanup_expired_searches(db, max_entries)
        
        return result
    
    def _search_hotels_direct(self, request: HotelSearchRequest):
        """Direct API call without caching"""
        url = f"{config['api']['base_url']}{config['api']['endpoints']['hotel_search']}"
        # exclude optional fields
        payload = request.model_dump(exclude_none=True)
        # Note: API doesn't accept page and limit parameters

        headers = {
            "x-api-key": config["headers"]["default"]["x-api-key"],
            "accept-language": config["headers"]["default"]["accept-language"],
            "content-type": config["headers"]["default"]["content-type"]
        }
        response = requests.post(url, headers=headers, json=payload, timeout=config["timeouts"]["default"])
        
        # Handle different response status codes
        if response.status_code == 200:
            data = response.json()
            hotels = data.get("data", {}).get("hotels", [])
            
            # Process hotels to include rate information
            processed_hotels = []
            for hotel in hotels:
                # Extract rate information
                rate_info = hotel.get("rate", {})
                if rate_info:
                    hotel["rate"] = {
                        "currency": rate_info.get("currency", "USD"),
                        "baseRate": rate_info.get("baseRate"),
                        "totalRate": rate_info.get("totalRate"),
                        "publishedRate": rate_info.get("publishedRate"),
                        "perNightRate": rate_info.get("perNightRate")
                    }
                processed_hotels.append(hotel)
            
            return {
                "hotels": processed_hotels
            }
        elif response.status_code == 404:
            # 404 with "No hotel search result found" is a valid response
            data = response.json()
            if data.get("message") == "No hotel search result found":
                return {
                    "hotels": []
                }
            else:
                raise HTTPException(status_code=response.status_code, detail=f"{message_loader.get_error_message('hotelier_service_error')}: {response.text}")
        else:
            # Other error status codes
            raise HTTPException(status_code=response.status_code, detail=f"{message_loader.get_error_message('hotelier_service_error')}: {response.text}")

    def book_hotel(self, db: Session, hotel_id: str, token: str, payload: BookHotelRequest):
        """Book a hotel and save the booking details to database"""
        url = f"{config['api']['base_url']}{config['api']['endpoints']['book_hotel'].format(hotel_id=hotel_id, session_id=token)}"
        
        headers = {
            "x-api-key": config["headers"]["default"]["x-api-key"],
            "accept-language": config["headers"]["default"]["accept-language"],
            "content-type": config["headers"]["default"]["content-type"]
        }
        
        try:
            # Call the Hotelier Service
            response = requests.post(url, json=payload.model_dump(), headers=headers, timeout=config["timeouts"]["booking"])
            
            # Handle different response status codes
            if response.status_code == 200:
                try:
                    api_response = response.json()
                except ValueError as json_error:
                    error_detail = f"{message_loader.get_error_message('hotelier_service_error')}: Invalid JSON response - {str(json_error)}"
                    raise HTTPException(status_code=500, detail=error_detail)
                
                # Try to save booking details to database if available
                try:
                    if db:
                        booking_record = self.repository.save_booking_details(
                            db=db,
                            booking_request=payload.model_dump(),
                            api_response=api_response,
                            hotel_id=hotel_id,
                            session_id=token
                        )
                        
                        return {
                            "message": message_loader.get_success_message("hotel_booking_completed"),
                            message_loader.get_info_message("booking_id"): booking_record.booking_id,
                            message_loader.get_info_message("booking_ref_id"): booking_record.booking_ref_id,
                            message_loader.get_info_message("booking_record"): booking_record,
                            message_loader.get_info_message("api_response"): api_response
                        }
                    else:
                        # Return without database saving
                        return {
                            "message": message_loader.get_success_message("hotel_booking_completed_no_db"),
                            message_loader.get_info_message("api_response"): api_response
                        }
                except Exception as db_error:
                    # If database fails, still return the API response
                    return {
                        "message": message_loader.get_success_message("hotel_booking_completed_db_failed"),
                        message_loader.get_info_message("api_response"): api_response,
                        message_loader.get_info_message("database_error"): str(db_error)
                    }
            else:
                # Handle non-200 status codes
                try:
                    error_response = response.json()
                    error_detail = f"{message_loader.get_error_message('hotelier_service_error')}: {error_response.get('message', response.text)}"
                except:
                    error_detail = f"{message_loader.get_error_message('hotelier_service_error')}: Status {response.status_code}, Response: {response.text}"
                
                # Return error information instead of raising HTTPException
                return {
                    "error": True,
                    "message": error_detail,
                    "status_code": response.status_code
                }
            
        except requests.exceptions.RequestException as e:
            error_detail = f"{message_loader.get_error_message('booking_api_error')}: {str(e)}"
            raise HTTPException(status_code=500, detail=error_detail)
        except Exception as e:
            error_detail = f"{message_loader.get_error_message('service_error')}: {str(e)}"
            logger.error(f"Hotel booking service error: {error_detail}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=error_detail)

    async def book_hotel_async(self, db: Session, hotel_id: str, token: str, payload: BookHotelRequest) -> Dict[str, Any]:
        """
        Book a hotel and save the booking details to database asynchronously.
        Optimized for better performance with parallel operations.
        
        Args:
            db: Database session
            hotel_id: Hotel identifier
            token: Booking session token
            payload: BookHotelRequest with booking details
            
        Returns:
            Dictionary with booking confirmation and details
        """
        try:
            logger.info(f"Processing async hotel booking for hotel: {hotel_id}")
            
            # Prepare API call data
            url = f"{config['api']['base_url']}{config['api']['endpoints']['book_hotel'].format(hotel_id=hotel_id, session_id=token)}"
            headers = {
                "x-api-key": config["headers"]["default"]["x-api-key"],
                "accept-language": config["headers"]["default"]["accept-language"],
                "content-type": config["headers"]["default"]["content-type"]
            }
            
            # Serialize payload once for efficiency
            booking_data = payload.model_dump()
            
            # Make async API call
            async with httpx.AsyncClient(timeout=config["timeouts"]["booking"]) as client:
                response = await client.post(url, json=booking_data, headers=headers)
                
                # Handle response
                if response.status_code == 200:
                    try:
                        api_response = response.json()
                    except ValueError as json_error:
                        error_detail = f"{message_loader.get_error_message('hotelier_service_error')}: Invalid JSON response - {str(json_error)}"
                        raise HTTPException(status_code=500, detail=error_detail)
                    
                    # Prepare response data
                    result = {
                        "message": message_loader.get_success_message("hotel_booking_completed"),
                        message_loader.get_info_message("api_response"): api_response
                    }
                    
                    # Save to database if available (non-blocking)
                    if db:
                        try:
                            # Use asyncio.to_thread for database operations to avoid blocking
                            booking_record = await asyncio.to_thread(
                                self.repository.save_booking_details,
                                db=db,
                                booking_request=booking_data,
                                api_response=api_response,
                                hotel_id=hotel_id,
                                session_id=token
                            )
                            
                            # Add booking details to response
                            result.update({
                                message_loader.get_info_message("booking_id"): booking_record.booking_id,
                                message_loader.get_info_message("booking_ref_id"): booking_record.booking_ref_id,
                                message_loader.get_info_message("booking_record"): booking_record
                            })
                            
                            logger.info(f"Booking successfully saved to database: {booking_record.booking_id}")
                            
                        except Exception as db_error:
                            # If database fails, still return the API response
                            logger.warning(f"Database save failed, but booking succeeded: {str(db_error)}")
                            result.update({
                                "message": message_loader.get_success_message("hotel_booking_completed_db_failed"),
                                message_loader.get_info_message("database_error"): str(db_error)
                            })
                    else:
                        result["message"] = message_loader.get_success_message("hotel_booking_completed_no_db")
                    
                    logger.info(f"Async hotel booking completed successfully for hotel: {hotel_id}")
                    return result
                    
                else:
                    # Handle error responses
                    try:
                        error_response = response.json()
                        error_detail = f"{message_loader.get_error_message('hotelier_service_error')}: {error_response.get('message', response.text)}"
                    except:
                        error_detail = f"{message_loader.get_error_message('hotelier_service_error')}: Status {response.status_code}, Response: {response.text}"
                    
                    return {
                        "error": True,
                        "message": error_detail,
                        "status_code": response.status_code
                    }
                    
        except httpx.RequestError as e:
            error_detail = f"{message_loader.get_error_message('booking_api_error')}: {str(e)}"
            logger.error(f"Async booking API error: {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)
        except Exception as e:
            error_detail = f"{message_loader.get_error_message('service_error')}: {str(e)}"
            logger.error(f"Async hotel booking service error: {error_detail}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=error_detail)

    async def get_hotel_autosuggestions_async(self, payload: AutocompleteRequest) -> Dict[str, Any]:
        """
        Get hotel autosuggestions from Xeni API asynchronously.
        
        Args:
            payload: AutocompleteRequest with search key
            
        Returns:
            Dictionary with autosuggest data from API including correlation ID
        """
        try:
            logger.info(f"Calling Xeni API asynchronously for autosuggest - Query: {payload.key}")
            
            # Get authentication token
            from app.services.auth_service import AuthService
            auth_service = AuthService()
            auth_token = await auth_service.get_valid_auth_token()
            
            if not auth_token:
                error_msg = "Failed to obtain authentication token"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail={
                    "desc": [{
                        "type": "auth_error",
                        "message": error_msg
                    }],
                    "error": error_msg,
                    "status": "failed"
                })
            
            headers = {
                "Authorization": auth_token,
                "accept-language": config["headers"]["default"]["accept-language"],
                "content-type": config["headers"]["default"]["content-type"]
            }
            
            # Build URL with query parameter
            base_url = f"{config['api']['base_url']}{config['api']['endpoints']['autosuggest']}"
            url = f"{base_url}?key={payload.key}"
            logger.info(f"URL: {url} is called")
            async with httpx.AsyncClient(timeout=config["timeouts"]["default"]) as client:
                # Use GET request instead of POST
                response = await client.get(url, headers=headers)
                
                # Extract correlation ID from response headers
                correlation_id = response.headers.get("X-Correlation-Id")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Add correlation ID to response
                    if correlation_id:
                        data["correlation_id"] = correlation_id
                    
                    logger.info(f"Autosuggest data received successfully - Correlation ID: {correlation_id}")
                    return data
                else:
                    # Handle different error response formats
                    try:
                        error_data = response.json()
                        # Add correlation ID to error response
                        if correlation_id:
                            error_data["correlation_id"] = correlation_id
                        
                        logger.error(f"Autosuggest API error {response.status_code}: {error_data}")
                        raise HTTPException(status_code=response.status_code, detail=error_data)
                    except ValueError:
                        # If response is not JSON, create a generic error
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                        logger.error(f"Autosuggest API error: {error_msg}")
                        
                        error_response = {
                            "desc": [{
                                "type": "http_error",
                                "message": error_msg
                            }],
                            "error": error_msg,
                            "status": "failed",
                            "correlation_id": correlation_id
                        }
                        raise HTTPException(status_code=response.status_code, detail=error_response)
                    
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"Autosuggest request error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Autosuggest request error: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Autosuggest unexpected error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Autosuggest error: {error_msg}")



    def get_rooms_id_from_rate_id(self, db: Session, rate_id: str) -> int:
        """Get rooms_id from rate_plans table using rateId"""
        try:
            # Query rate_plans table to get rooms_id for the given rateId
            result = db.execute(text("""
                SELECT rooms_id 
                FROM rate_plans 
                WHERE id = :rate_id 
                AND is_active = 1 
                AND deleted = 0
            """), {"rate_id": rate_id})
            
            row = result.fetchone()
            if row:
                return row[0]  # Return rooms_id
            else:
                logger.warning(f"No active rate plan found for rateId: {rate_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error looking up rooms_id for rateId {rate_id}: {str(e)}")
            return None


    async def get_hotel_details_from_api_async(self, hotel_id: str) -> Dict[str, Any]:
        """
        Get hotel details from Xeni API asynchronously.
        
        Args:
            hotel_id: Hotel ID to fetch details for
            
        Returns:
            Dictionary with hotel details from API
        """
        try:
            logger.info(f"Fetching hotel details from API for hotel: {hotel_id}")
            
            # Use the hotel search API to get hotel details
            # We'll search for the specific hotel by ID
            search_payload = {
                "hotelId": hotel_id,
                "checkInDate": "2025-12-30",  # Use future dates
                "checkOutDate": "2025-12-31",
                "occupancies": [{"numOfRoom": 1, "numOfAdults": 1, "numOfChildren": 0}]
            }
            
            url = f"{config['api']['base_url']}{config['api']['endpoints']['hotel_search']}"
            headers = {
                "x-api-key": config["headers"]["default"]["x-api-key"],
                "accept-language": config["headers"]["default"]["accept-language"],
                "content-type": config["headers"]["default"]["content-type"]
            }
            
            async with httpx.AsyncClient(timeout=config["timeouts"]["default"]) as client:
                response = await client.post(url, headers=headers, json=search_payload)
                
                if response.status_code == 200:
                    data = response.json()
                    hotels = data.get("data", {}).get("hotels", [])
                    
                    # Find the specific hotel by ID
                    for hotel in hotels:
                        if str(hotel.get("id")) == str(hotel_id):
                            logger.info(f"Found hotel details in API response for hotel: {hotel_id}")
                            return {
                                "id": hotel.get("id"),
                                "name": hotel.get("name"),
                                "description": hotel.get("description"),
                                "address": hotel.get("address"),
                                "city": hotel.get("city"),
                                "state": hotel.get("state"),
                                "country": hotel.get("country"),
                                "postal_code": hotel.get("postalCode"),
                                "latitude": hotel.get("latitude"),
                                "longitude": hotel.get("longitude"),
                                "star_rating": hotel.get("starRating"),
                                "avg_rating": hotel.get("avgRating"),
                                "total_reviews": hotel.get("totalReviews"),
                                "amenities": hotel.get("amenities", []),
                                "images": hotel.get("images", [])
                            }
                    
                    logger.warning(f"Hotel {hotel_id} not found in API search results")
                    return None
                else:
                    logger.error(f"API call failed with status {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching hotel details from API: {str(e)}")
            return None

    async def get_hotel_details_from_db_async(self, db: Session, hotel_id: str) -> Dict[str, Any]:
        """
        Get complete hotel details from database including amenities and images asynchronously.
        
        Args:
            db: Database session
            hotel_id: Hotel ID to search for (can be either database ID or API hotel ID)
            
        Returns:
            Dictionary with complete hotel details including amenities and images
        """
        try:
            logger.info(f"Fetching hotel details from database asynchronously for hotel ID: {hotel_id}")
            
            # Find hotel by API hotel ID or internal ID
            hotel = db.query(Hotel).filter(
                (Hotel.api_hotel_id == hotel_id) | (Hotel.id == hotel_id)
            ).first()
            
            if not hotel:
                logger.warning(f"Hotel not found in database for ID: {hotel_id}")
                return None
            
            # Get hotel amenities
            amenities = db.query(HotelAmenity).filter(HotelAmenity.hotel_id == hotel.id).all()
            
            # Get hotel images
            images = db.query(HotelImage).filter(HotelImage.hotel_id == hotel.id).all()
            
            # Build hotel details response
            hotel_details = {
                "id": hotel.api_hotel_id or hotel.id,  # Return API hotel ID if available, otherwise internal ID
                "internal_id": hotel.id,
                "api_hotel_id": hotel.api_hotel_id,
                "name": hotel.name,
                "description": hotel.description,
                "address": hotel.address,
                "city": hotel.city,
                "state": hotel.state,
                "country": hotel.country,
                "postal_code": hotel.postal_code,
                "latitude": float(hotel.latitude) if hotel.latitude else None,
                "longitude": float(hotel.longitude) if hotel.longitude else None,
                "phone": hotel.phone,
                "email": hotel.email,
                "website": hotel.website,
                "star_rating": hotel.star_rating,
                "avg_rating": float(hotel.avg_rating) if hotel.avg_rating else None,
                "total_reviews": hotel.total_reviews,
                "amenities": [
                    {
                        "id": amenity.id,
                        "name": amenity.amenity_name,
                        "type": amenity.amenity_type,
                        "icon": amenity.icon
                    }
                    for amenity in amenities
                ],
                "images": [
                    {
                        "id": image.id,
                        "url": image.image,
                        "caption": image.caption,
                        "is_primary": image.is_primary,
                        "sort_order": image.sort_order
                    }
                    for image in images
                ]
            }
            
            logger.info(f"Successfully fetched hotel details asynchronously for hotel: {hotel.name} (ID: {hotel.id})")
            return hotel_details
            
        except Exception as e:
            logger.error(f"Error fetching hotel details from database asynchronously: {str(e)}")
            raise e

 
    def get_price_recommendation(self, hotel_id: str, api_token: str, recommendation_id: str):
        url = f"{config['api']['base_url']}{config['api']['endpoints']['price_recommendation'].format(hotel_id=hotel_id, api_token=api_token, recommendation_id=recommendation_id)}"
        headers = {
            "x-api-key": config["headers"]["default"]["x-api-key"],
            "accept-language": config["headers"]["default"]["accept-language"],
            "content-type": config["headers"]["default"]["content-type"]
        }
        return requests.get(url, headers=headers, timeout=config["timeouts"]["default"])

    async def get_price_recommendation_async(self, hotel_id: str, api_token: str, recommendation_id: str) -> Dict[str, Any]:
        """
        Get hotel room price recommendation from Xeni API asynchronously.
        
        Args:
            hotel_id: Hotel identifier
            api_token: API token for authentication
            recommendation_id: Recommendation identifier
            
        Returns:
            Dictionary with price recommendation data from API
        """
        try:
            logger.info(f"Calling Xeni API asynchronously for price recommendation - Hotel: {hotel_id}, Recommendation: {recommendation_id}")
            
            url = f"{config['api']['base_url']}{config['api']['endpoints']['price_recommendation'].format(hotel_id=hotel_id, api_token=api_token, recommendation_id=recommendation_id)}"
            headers = {
                "x-api-key": config["headers"]["default"]["x-api-key"],
                "accept-language": config["headers"]["default"]["accept-language"],
                "content-type": config["headers"]["default"]["content-type"]
            }
            
            logger.info(f"Price recommendation URL: {url}")
            logger.info(f"Price recommendation headers: {headers}")
            logger.info(f"API Key being used: {config['headers']['default']['x-api-key']}")
            
            async with httpx.AsyncClient(timeout=config["timeouts"]["default"]) as client:
                response = await client.get(url, headers=headers)
                
                logger.info(f"Price recommendation response status: {response.status_code}")
                logger.info(f"Price recommendation response headers: {dict(response.headers)}")
                
                # Get response text for debugging
                response_text = response.text
                logger.info(f"Price recommendation response text: {response_text}")
                
                # Check if the API key is being sent correctly
                if response.status_code == 400 and "Invalid initialization vector" in response_text:
                    logger.error("API returned 'Invalid initialization vector' - this usually means the api_token parameter format is incorrect")
                    logger.error(f"API Key being used: {config['headers']['default']['x-api-key']}")
                    logger.error(f"API Token parameter: {api_token}")
                    logger.error(f"Hotel ID: {hotel_id}")
                    logger.error(f"Recommendation ID: {recommendation_id}")
                    logger.error(f"Headers sent: {headers}")
                    logger.error("This error typically means the api_token needs to be in a specific format (UUID, encrypted, or session token)")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"Price recommendation data received: {data}")
                        return data
                    except Exception as json_error:
                        logger.error(f"Failed to parse JSON response: {str(json_error)}")
                        raise HTTPException(status_code=500, detail=f"Invalid JSON response from API: {str(json_error)}")
                        
                elif response.status_code == 404:
                    try:
                        data = response.json()
                        if data.get("message") == "No price recommendation found":
                            logger.info("No price recommendation found, returning empty recommendations")
                            return {"data": {"recommendations": []}}
                        else:
                            error_msg = f"404 Error: {data.get('message', 'Not found')}"
                            logger.error(f"Price recommendation 404 error: {error_msg}")
                            raise HTTPException(status_code=response.status_code, detail=f"{message_loader.get_error_message('price_recommendation_error')}: {error_msg}")
                    except Exception as json_error:
                        error_msg = f"404 Error: {response_text}"
                        logger.error(f"Price recommendation 404 error (no JSON): {error_msg}")
                        raise HTTPException(status_code=response.status_code, detail=f"{message_loader.get_error_message('price_recommendation_error')}: {error_msg}")
                        
                elif response.status_code == 400 and "Invalid initialization vector" in response_text:
                    # Handle the specific "Invalid initialization vector" error
                    error_msg = f"API Token format error: The api_token parameter '{api_token}' is not in the correct format. This typically means the token needs to be a valid session token, UUID, or encrypted token from a previous API call."
                    logger.error(f"Price recommendation token format error: {error_msg}")
                    raise HTTPException(status_code=400, detail=f"{message_loader.get_error_message('price_recommendation_error')}: {error_msg}")
                        
                else:
                    # Handle other error status codes
                    try:
                        error_data = response.json()
                        error_msg = f"HTTP {response.status_code}: {error_data.get('message', response_text)}"
                    except:
                        error_msg = f"HTTP {response.status_code}: {response_text}"
                    
                    logger.error(f"Price recommendation API error: {error_msg}")
                    raise HTTPException(status_code=response.status_code, detail=f"{message_loader.get_error_message('price_recommendation_error')}: {error_msg}")
                    
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"Price recommendation request error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"{message_loader.get_error_message('price_recommendation_error')}: {error_msg}")
        except HTTPException:
            # Re-raise HTTP exceptions as they are already properly formatted
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Price recommendation unexpected error: {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"{message_loader.get_error_message('price_recommendation_error')}: {error_msg}")

    async def fetch_booking_details(self, booking_id: str, currency: str, session_id: str):
        try:
            async with httpx.AsyncClient(timeout=config["timeouts"]["booking"]) as client:
                headers = {
                    "x-api-key": config["headers"]["default"]["x-api-key"],
                    "accept-language": config["headers"]["default"]["accept-language"],
                    "content-type": config["headers"]["default"]["content-type"],
                    "x-session-id": session_id,
                }
                
                url = f"{config['api']['base_url']}{config['api']['endpoints']['booking_details']}"
                response = await client.get(
                    url,
                    params={"bookingId": booking_id, "currency": currency},
                    headers=headers,
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"{message_loader.get_error_message('hotelier_service_error')}: {response.text}",
                    )

                return response.json()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{message_loader.get_error_message('service_error')}: {str(e)}")

    async def fetch_cancellation_penalty(self, booking_id: str):
        try:
            async with httpx.AsyncClient(timeout=config["timeouts"]["booking"]) as client:
                headers = {
                    "x-api-key": config["headers"]["default"]["x-api-key"],
                }
                
                url = f"{config['api']['base_url']}{config['api']['endpoints']['booking_cancellation_fee']}"
                response = await client.get(
                    url,
                    params={"bookingId": booking_id},
                    headers=headers,
                )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"{message_loader.get_error_message('hotelier_service_error')}: {response.text}")
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{message_loader.get_error_message('service_error')}: {str(e)}")

    async def cancel_booking(self, booking_id: str, token: str, db: Session = None):
        try:
            logger.info(f"Calling Xeni API asynchronously for cancel booking - Booking: {booking_id}")
            
            async with httpx.AsyncClient(timeout=config["timeouts"]["booking"]) as client:
                headers = {
                    "x-api-key": config["headers"]["default"]["x-api-key"],
                }
                
                url = f"{config['api']['base_url']}{config['api']['endpoints']['cancel_booking']}"
                logger.info(f"Cancel booking URL: {url}")
                logger.info(f"Cancel booking headers: {headers}")
                logger.info(f"Cancel booking payload: {{'bookingId': '{booking_id}', 'token': '{token}'}}")
                
                response = await client.post(
                    url,
                    json={"bookingId": booking_id, "token": token},
                    headers=headers,
                )
                
                logger.info(f"Cancel booking response status: {response.status_code}")
                logger.info(f"Cancel booking response text: {response.text}")
                
                if response.status_code == 200:
                    api_response = response.json()
                    
                    # Update database if successful cancellation
                    if db:
                        try:
                            # Extract cancellation details from API response
                            cancellation_data = {
                                "reason": "Customer request",
                                "penalty_amount": None,
                                "penalty_currency": "USD",
                                "cancelled_by": "customer",
                                "api_response": api_response
                            }
                            
                            # Try to extract penalty information from API response
                            if "data" in api_response:
                                data = api_response["data"]
                                if "penalty" in data:
                                    penalty = data["penalty"]
                                    cancellation_data["penalty_amount"] = penalty.get("amount")
                                    cancellation_data["penalty_currency"] = penalty.get("currency", "USD")
                            
                            # Update booking in database
                            updated_booking = self.repository.update_booking_cancellation(
                                db, booking_id, cancellation_data
                            )
                            
                            logger.info(f"Successfully updated database for cancelled booking {booking_id}")
                            
                        except Exception as db_error:
                            logger.error(f"Failed to update database for cancelled booking {booking_id}: {str(db_error)}")
                            # Don't fail the entire operation if DB update fails
                    
                    return api_response
                else:
                    # Handle specific error responses from Xeni API
                    try:
                        error_data = response.json()
                        if error_data.get("error") and error_data.get("message"):
                            error_message = error_data["message"]
                            if isinstance(error_message, dict):
                                # Extract meaningful error details
                                code = error_message.get("Code", "Unknown")
                                message = error_message.get("Message", "Unknown error")
                                category = error_message.get("Category", "")
                                
                                # Create a user-friendly error message
                                if code == "4010" and "already cancelled" in message.lower():
                                    user_message = f"Booking cancellation failed: {message}"
                                else:
                                    user_message = f"Booking cancellation failed (Code {code}): {message}"
                                
                                logger.warning(f"Cancel booking API error - Code: {code}, Message: {message}")
                                raise HTTPException(status_code=400, detail=user_message)
                            else:
                                # Simple error message
                                raise HTTPException(status_code=response.status_code, detail=f"Booking cancellation failed: {error_message}")
                        else:
                            # Generic error response
                            raise HTTPException(status_code=response.status_code, detail=f"Booking cancellation failed: {response.text}")
                    except ValueError:
                        # Not JSON response
                        raise HTTPException(status_code=response.status_code, detail=f"Booking cancellation failed: {response.text}")
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"Cancel booking request error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"{message_loader.get_error_message('service_error')}: {error_msg}")
        except HTTPException:
            # Re-raise HTTP exceptions as they are already properly formatted
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Cancel booking unexpected error: {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"{message_loader.get_error_message('service_error')}: {error_msg}")
    def get_hotel_details_from_db(self, db: Session, hotel_id: str):
        """
        Get complete hotel details from database including amenities and images.
        
        Args:
            db: Database session
            hotel_id: Hotel ID to search for (can be either database ID or API hotel ID)
            
        Returns:
            Dictionary with complete hotel details including amenities and images
        """
        try:
            logger.info(f"Fetching hotel details from database for hotel ID: {hotel_id}")
            
            # Find hotel by API hotel ID or internal ID
            hotel = db.query(Hotel).filter(
                (Hotel.api_hotel_id == hotel_id) | (Hotel.id == hotel_id)
            ).first()
            
            if not hotel:
                logger.warning(f"Hotel not found in database for ID: {hotel_id}")
                return None
            
            # Get hotel amenities
            amenities = db.query(HotelAmenity).filter(HotelAmenity.hotel_id == hotel.id).all()
            
            # Get hotel images
            images = db.query(HotelImage).filter(HotelImage.hotel_id == hotel.id).all()
            
            # Build hotel details response
            hotel_details = {
                "id": hotel.api_hotel_id or hotel.id,  # Return API hotel ID if available, otherwise internal ID
                "internal_id": hotel.id,
                "api_hotel_id": hotel.api_hotel_id,
                "name": hotel.name,
                "description": hotel.description,
                "address": hotel.address,
                "city": hotel.city,
                "state": hotel.state,
                "country": hotel.country,
                "postal_code": hotel.postal_code,
                "latitude": float(hotel.latitude) if hotel.latitude else None,
                "longitude": float(hotel.longitude) if hotel.longitude else None,
                "phone": hotel.phone,
                "email": hotel.email,
                "website": hotel.website,
                "star_rating": hotel.star_rating,
                "avg_rating": float(hotel.avg_rating) if hotel.avg_rating else None,
                "total_reviews": hotel.total_reviews,
                "amenities": [
                    {
                        "id": amenity.id,
                        "name": amenity.amenity_name,
                        "type": amenity.amenity_type,
                        "icon": amenity.icon
                    }
                    for amenity in amenities
                ],
                "images": [
                    {
                        "id": image.id,
                        "url": image.image,
                        "caption": image.caption,
                        "is_primary": image.is_primary,
                        "sort_order": image.sort_order
                    }
                    for image in images
                ]
            }
            
            logger.info(f"Successfully fetched hotel details for hotel: {hotel.name} (ID: {hotel.id})")
            return hotel_details
            
        except Exception as e:
            logger.error(f"Error fetching hotel details from database: {str(e)}")
            raise e

    async def search_hotels_from_db(self, db: Session, request: HotelSearchRequest) -> List[Dict[str, Any]]:
        """
        Search for hotels in the database based on latitude, longitude coordinates and other criteria.
        OPTIMIZED VERSION with proper joins and indexes.
        
        Args:
            db: Database session
            request: HotelSearchRequest with search criteria (lat, lng, dates, occupancy)
            
        Returns:
            List of hotel dictionaries from database
        """
        try:
            logger.info(f"Searching hotels in database for coordinates: lat={request.lat}, lng={request.lng}")
            
            # Get search radius (default to 50km if not specified)
            radius_km = request.radius if request.radius else 50
            
            # Calculate bounding box for coordinate search
            # Rough approximation: 1 degree latitude ≈ 111 km
            lat_delta = radius_km / 111.0
            lng_delta = radius_km / (111.0 * abs(request.lat) * 0.0174532925)  # Adjust for longitude
            
            # OPTIMIZED: Use single query with joins to avoid N+1 problem
            from sqlalchemy.orm import joinedload
            
            hotels_query = db.query(Hotel).options(
                joinedload(Hotel.amenities),
                joinedload(Hotel.images),
                joinedload(Hotel.rooms)
            ).filter(
                Hotel.latitude.between(request.lat - lat_delta, request.lat + lat_delta),
                Hotel.longitude.between(request.lng - lng_delta, request.lng + lng_delta)
            ).order_by(
                Hotel.api_hotel_id.isnot(None).desc(), 
                Hotel.api_hotel_id.desc()
            ).limit(100)
            
            hotels = hotels_query.all()
            
            # If no hotels found in radius, try a broader search
            if not hotels:
                logger.info("No hotels found in radius, trying broader search")
                # Expand search radius by 2x
                lat_delta *= 2
                lng_delta *= 2
                hotels_query = db.query(Hotel).options(
                    joinedload(Hotel.amenities),
                    joinedload(Hotel.images),
                    joinedload(Hotel.rooms)
                ).filter(
                    Hotel.latitude.between(request.lat - lat_delta, request.lat + lat_delta),
                    Hotel.longitude.between(request.lng - lng_delta, request.lng + lng_delta)
                ).order_by(
                    Hotel.api_hotel_id.isnot(None).desc(), 
                    Hotel.api_hotel_id.desc()
                ).limit(50)
                
                hotels = hotels_query.all()
            
            # If still no hotels, try a very broad search
            if not hotels:
                logger.info("No hotels found in expanded radius, trying very broad search")
                hotels = db.query(Hotel).filter(
                    Hotel.latitude.isnot(None),
                    Hotel.longitude.isnot(None)
                ).order_by(Hotel.api_hotel_id.isnot(None).desc(), Hotel.api_hotel_id.desc()).limit(20).all()
            
            # Convert hotels to response format
            hotel_results = []
            for hotel in hotels:
                # Calculate distance from search point (optional, for sorting)
                if hotel.latitude and hotel.longitude:
                    distance = self._calculate_distance(
                        request.lat, request.lng, 
                        float(hotel.latitude), float(hotel.longitude)
                    )
                else:
                    distance = None
                
                # OPTIMIZED: Use pre-loaded relationships instead of separate queries
                amenities = hotel.amenities if hasattr(hotel, 'amenities') else []
                images = hotel.images if hasattr(hotel, 'images') else []
                
                # Get pricing information from hotel_rooms table
                # First try to find representative room created during hotel search
                representative_room = db.query(Room).filter(
                    Room.room_id == f"hotel_search_{hotel.api_hotel_id}_representative"
                ).first()
                
                rate_info = None
                
                if representative_room and representative_room.base_rate is not None and representative_room.base_rate > 0:
                    # Use representative room pricing data
                    rate_info = {
                        "currency": representative_room.currency or "USD",
                        "baseRate": round(representative_room.base_rate, 2),
                        "totalRate": round(representative_room.total_rate, 2) if representative_room.total_rate else round(representative_room.base_rate, 2),
                        "publishedRate": round(representative_room.published_rate, 2) if representative_room.published_rate else round(representative_room.base_rate * 1.2, 2),
                        "perNightRate": round(representative_room.per_night_rate, 2) if representative_room.per_night_rate else round(representative_room.base_rate, 2)
                    }
                else:
                    # Fallback: look for any rooms linked to this hotel
                    rooms = db.query(Room).filter(Room.hotel_id == hotel.id).all()
                    
                    if rooms:
                        # Find the room with the most recent pricing data (or first available)
                        valid_rooms = [room for room in rooms if room.base_rate is not None and room.base_rate > 0]
                        if valid_rooms:
                            # Use the first valid room's pricing as representative pricing for the hotel
                            room = valid_rooms[0]
                            rate_info = {
                                "currency": room.currency or "USD",
                                "baseRate": round(room.base_rate, 2),
                                "totalRate": round(room.total_rate, 2) if room.total_rate else round(room.base_rate, 2),
                                "publishedRate": round(room.published_rate, 2) if room.published_rate else round(room.base_rate * 1.2, 2),
                                "perNightRate": round(room.per_night_rate, 2) if room.per_night_rate else round(room.base_rate, 2)
                            }
                
                hotel_data = {
                    "id": hotel.api_hotel_id or hotel.id,  # Return API hotel ID if available, otherwise internal ID
                    "internal_id": hotel.id,
                    "api_hotel_id": hotel.api_hotel_id,
                    "hotelName": hotel.name,
                    "description": hotel.description,
                    "address": {
                        "line1": hotel.address,
                        "city": {"name": hotel.city},
                        "state": {"name": hotel.state},
                        "country": {"name": hotel.country},
                        "postalCode": hotel.postal_code
                    },
                    "lat": float(hotel.latitude) if hotel.latitude else 0,
                    "lng": float(hotel.longitude) if hotel.longitude else 0,
                    "rating": hotel.star_rating,
                    "reviews": [{
                        "rating": float(hotel.avg_rating) if hotel.avg_rating else 0,
                        "count": hotel.total_reviews
                    }],
                    "facilities": [{"name": amenity.amenity_name} for amenity in amenities],
                    "image": images[0].image if images else None,
                    "distance": round(distance, 2) if distance else None,
                    "rate": rate_info  # Add pricing information
                }
                hotel_results.append(hotel_data)
            
            # Sort by distance if available (handle None values properly)
            hotel_results.sort(key=lambda x: x.get('distance') if x.get('distance') is not None else float('inf'))
            
            logger.info(f"Found {len(hotel_results)} hotels in database")
            return hotel_results
            
        except Exception as e:
            logger.error(f"Error searching hotels from database: {str(e)}")
            return []

    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.
        
        Args:
            lat1, lng1: First coordinate
            lat2, lng2: Second coordinate
            
        Returns:
            Distance in kilometers
        """
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r

    async def search_hotels_from_api_async(self, request: HotelSearchRequest) -> Dict[str, Any]:
        """
        Search hotels from Xeni API asynchronously.
        
        Args:
            request: HotelSearchRequest with search criteria
            
        Returns:
            Dictionary with hotels data from API
        """
        try:
            logger.info(f"Calling Xeni API asynchronously for location: {request.locationId}")
            
            url = f"{config['api']['base_url']}{config['api']['endpoints']['hotel_search']}"
            payload = request.model_dump(exclude_none=True)
            
            headers = {
                "x-api-key": config["headers"]["default"]["x-api-key"],
                "accept-language": config["headers"]["default"]["accept-language"],
                "content-type": config["headers"]["default"]["content-type"]
            }
            
            async with httpx.AsyncClient(timeout=config["timeouts"]["default"]) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    hotels = data.get("data", {}).get("hotels", [])
                    
                    # Process hotels to include rate information
                    processed_hotels = []
                    for hotel in hotels:
                        # Extract rate information
                        rate_info = hotel.get("rate", {})
                        if rate_info:
                            hotel["rate"] = {
                                "currency": rate_info.get("currency", "USD"),
                                "baseRate": rate_info.get("baseRate"),
                                "totalRate": rate_info.get("totalRate"),
                                "publishedRate": rate_info.get("publishedRate"),
                                "perNightRate": rate_info.get("perNightRate")
                            }
                        processed_hotels.append(hotel)
                    
                    return {
                        "hotels": processed_hotels
                    }
                elif response.status_code == 404:
                    data = response.json()
                    if data.get("message") == "No hotel search result found":
                        return {"hotels": []}
                    else:
                        raise HTTPException(status_code=response.status_code, detail=f"{message_loader.get_error_message('hotelier_service_error')}: {response.text}")
                else:
                    raise HTTPException(status_code=response.status_code, detail=f"{message_loader.get_error_message('hotelier_service_error')}: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error calling Xeni API asynchronously: {str(e)}")
            raise HTTPException(status_code=500, detail=f"API call failed: {str(e)}")

    async def save_hotels_to_db_async(self, db: Session, hotels_data: List[Dict[str, Any]]) -> List[Hotel]:
        """
        Save hotels data to database asynchronously.
        
        Args:
            db: Database session
            hotels_data: List of hotel data from API
            
        Returns:
            List of saved hotel objects
        """
        try:
            logger.info(f"Saving {len(hotels_data)} hotels to database asynchronously")
            
            hotels_saved = []
            
            for h in hotels_data:
                # Map the API response fields to our hotel data structure
                address_info = h.get("address", {})
                reviews_info = h.get("reviews", [{}])[0] if h.get("reviews") else {}
                
                hotel_data = {
                    "id": str(h.get("id")),  # Primary key - API hotel ID
                    "api_hotel_id": str(h.get("id")),  # Store API hotel ID
                    "name": h.get("hotelName"),
                    "description": h.get("description", ""),
                    "address": address_info.get("line1", ""),
                    "city": address_info.get("city", {}).get("name", ""),
                    "state": address_info.get("state", {}).get("name", ""),
                    "country": address_info.get("country", {}).get("name", ""),
                    "postal_code": address_info.get("postalCode", ""),
                    "latitude": float(h.get("lat", 0)) if h.get("lat") else 0,
                    "longitude": float(h.get("lng", 0)) if h.get("lng") else 0,
                    "star_rating": int(float(h.get("rating", 0))) if h.get("rating") else 0,
                    "avg_rating": float(reviews_info.get("rating", 0)) if reviews_info.get("rating") else 0,
                    "total_reviews": int(reviews_info.get("count", 0)) if reviews_info.get("count") else 0,
                }

                # Map facilities to amenities
                amenities = [{"amenity_name": facility.get("name", "")} for facility in h.get("facilities", [])]
                
                # Map image
                images = []
                if h.get("image"):
                    images = [{"image": h.get("image"), "caption": h.get("hotelName", "")}]

                # Save hotel details (this is synchronous but we're in an async context)
                saved_hotel = self.repository.save_hotel_details(db, hotel_data, amenities, images)
                hotels_saved.append(saved_hotel)
            
            logger.info(f"Successfully saved {len(hotels_saved)} hotels to database")
            return hotels_saved
            
        except Exception as e:
            logger.error(f"Error saving hotels to database asynchronously: {str(e)}")
            raise e

    async def search_hotels(self, request, x_correlation_id: str) -> Dict[str, Any]:
        """
        Search hotels using the Xeni API with query parameters.
        
        Args:
            request: HotelSearchRequest with search criteria
            x_correlation_id: Correlation ID from autosuggest response (required)
            
        Returns:
            Dict containing the API response
        """
        try:
            # Validate correlation ID is provided
            if not x_correlation_id:
                raise HTTPException(
                    status_code=400, 
                    detail="x-correlation-id header is required for hotel search"
                )
            
            # Get HMAC authentication signature
            auth_service = AuthService()
            auth_signature = await auth_service.get_valid_auth_token()
            
            if not auth_signature:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to obtain authentication signature for hotel search"
                )
            
            # Build URL with query parameters
            base_url = f"{config['api']['base_url']}{config['api']['endpoints']['hotel_search']}"
            query_params = {
                "currency": "USD",
                "page": 1,
                "limit": 50,
                "amenities": "true"
            }
            
            # Add query parameters to URL
            import urllib.parse
            query_string = urllib.parse.urlencode(query_params)
            url = f"{base_url}?{query_string}"
            
            # Prepare headers with HMAC authentication (inherit auth from parent)
            headers = {
                "Authorization": auth_signature,
                "accept-language": config["headers"]["default"]["accept-language"],
                "content-type": config["headers"]["default"]["content-type"],
                "x-correlation-id": x_correlation_id
            }
            
            # Prepare request payload
            payload = request.model_dump(exclude_none=True)
            
            logger.info(f"Making hotel search API call to: {url}")
            logger.info(f"Request payload: {payload}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Make async HTTP request
            async with httpx.AsyncClient(timeout=config["timeouts"]["default"]) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                # Use the correlation ID from the request (not from response)
                correlation_id = x_correlation_id
                
                if response.status_code == 200:
                    data = response.json()
                    data["correlation_id"] = correlation_id
                    logger.info(f"Hotel search API call successful. Found {data.get('data', {}).get('total', 0)} hotels")
                    return data
                else:
                    # Handle error response with proper structure
                    try:
                        error_data = response.json()
                        error_data["correlation_id"] = correlation_id
                        logger.error(f"Hotel search API call failed with status {response.status_code}: {error_data}")
                        
                        # Convert the error response to match our error model format
                        if "desc" not in error_data:
                            # Convert simple error format to our expected format
                            error_response = {
                                "desc": [{
                                    "type": "api_error",
                                    "message": error_data.get("message", "API error occurred"),
                                    "fields": []
                                }],
                                "error": error_data.get("message", "API error occurred"),
                                "status": "failed",
                                "correlation_id": correlation_id
                            }
                            return error_response
                        else:
                            return error_data
                    except:
                        # If JSON parsing fails, return a generic error
                        error_data = {
                            "desc": [{
                                "type": "api_error",
                                "message": response.text,
                                "fields": []
                            }],
                            "error": response.text,
                            "status": "failed",
                            "correlation_id": correlation_id
                        }
                        logger.error(f"Hotel search API call failed with status {response.status_code}: {error_data}")
                        return error_data
                    
        except httpx.TimeoutException:
            logger.error("Hotel search API call timed out")
            raise HTTPException(status_code=408, detail="Hotel search API request timed out")
        except httpx.RequestError as e:
            logger.error(f"Hotel search API request error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Hotel search API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in hotel search: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def get_hotel_details(self, property_id: str, x_correlation_id: str) -> Dict[str, Any]:
        """
        Get hotel details using the Xeni API.
        
        Args:
            property_id: Property ID for the hotel
            x_correlation_id: Correlation ID from autosuggest response (required)
            
        Returns:
            Dict containing the API response
        """
        try:
            logger.info(f"Starting hotel details request - Property ID: {property_id}, Correlation ID: {x_correlation_id}")
            
            # Validate correlation ID is provided
            if not x_correlation_id:
                raise HTTPException(
                    status_code=400, 
                    detail="x-correlation-id header is required for hotel details"
                )
            
            # Get HMAC authentication signature
            logger.info("Getting authentication signature...")
            auth_service = AuthService()
            auth_signature = await auth_service.get_valid_auth_token()
            
            if not auth_signature:
                logger.error("Failed to get authentication signature")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to obtain authentication signature for hotel details"
                )
            
            logger.info("Authentication signature obtained successfully")
            
            # Build URL with property ID - simple concatenation
            base_url = config['api']['endpoints']['get_hotel_Details']
            url = f"{base_url}{property_id}"
            
            logger.info(f"Constructed URL: {url}")
            logger.info(f"Base URL: {base_url}")
            logger.info(f"Property ID: {property_id}")
            
            # Prepare headers with HMAC authentication (inherit auth from parent)
            headers = {
                "Authorization": auth_signature,
                "accept-language": config["headers"]["default"]["accept-language"],
                "content-type": config["headers"]["default"]["content-type"],
                "x-correlation-id": x_correlation_id
            }
            
            logger.info(f"Making hotel details API call to: {url}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Make async HTTP request
            async with httpx.AsyncClient(timeout=config["timeouts"]["default"]) as client:
                response = await client.get(url, headers=headers)
                
                # Use the correlation ID from the request (not from response)
                correlation_id = x_correlation_id
                
                if response.status_code == 200:
                    data = response.json()
                    data["correlation_id"] = correlation_id
                    logger.info(f"Hotel details API call successful for property: {property_id}")
                    return data
                else:
                    # Handle error response with proper structure
                    try:
                        error_data = response.json()
                        error_data["correlation_id"] = correlation_id
                        logger.error(f"Hotel details API call failed with status {response.status_code}: {error_data}")
                        
                        # Convert the error response to match our error model format
                        if "desc" not in error_data:
                            # Convert simple error format to our expected format
                            error_response = {
                                "desc": [{
                                    "type": "api_error",
                                    "message": error_data.get("message", "API error occurred"),
                                    "fields": []
                                }],
                                "error": error_data.get("message", "API error occurred"),
                                "status": "failed",
                                "correlation_id": correlation_id
                            }
                            return error_response
                        else:
                            return error_data
                    except:
                        # If JSON parsing fails, return a generic error
                        error_data = {
                            "desc": [{
                                "type": "api_error",
                                "message": response.text,
                                "fields": []
                            }],
                            "error": response.text,
                            "status": "failed",
                            "correlation_id": correlation_id
                        }
                        logger.error(f"Hotel details API call failed with status {response.status_code}: {error_data}")
                        return error_data
                    
        except httpx.TimeoutException:
            logger.error("Hotel details API call timed out")
            raise HTTPException(status_code=408, detail="Hotel details API request timed out")
        except httpx.RequestError as e:
            logger.error(f"Hotel details API request error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Hotel details API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in hotel details: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def check_hotel_availability(self, request: AvailabilityRequest, x_correlation_id: str) -> Dict[str, Any]:
        """
        Check hotel availability using the Xeni API.
        
        Args:
            request: AvailabilityRequest with availability criteria
            x_correlation_id: Correlation ID from autosuggest response (required)
            
        Returns:
            Dict containing the API response
        """
        try:
            logger.info(f"Starting hotel availability request - Property ID: {request.property_id}, Check-in: {request.checkin_date}, Check-out: {request.checkout_date}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Validate correlation ID is provided
            if not x_correlation_id:
                raise HTTPException(
                    status_code=400, 
                    detail="x-correlation-id header is required for hotel availability"
                )
            
            # Get HMAC authentication signature
            logger.info("Getting authentication signature...")
            auth_service = AuthService()
            auth_signature = await auth_service.get_valid_auth_token()
            
            if not auth_signature:
                logger.error("Failed to get authentication signature")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to obtain authentication signature for hotel availability"
                )
            
            logger.info("Authentication signature obtained successfully")
            
            # Build URL - simple concatenation
            base_url = config['api']['endpoints']['hotel_availability']
            url = base_url
            
            logger.info(f"Constructed URL: {url}")
            logger.info(f"Base URL: {base_url}")
            
            # Prepare headers with HMAC authentication (inherit auth from parent)
            headers = {
                "Authorization": auth_signature,
                "accept-language": config["headers"]["default"]["accept-language"],
                "content-type": config["headers"]["default"]["content-type"],
                "x-correlation-id": x_correlation_id
            }
            
            # Prepare request payload
            payload = request.model_dump(exclude_none=True)
            
            logger.info(f"Making hotel availability API call to: {url}")
            logger.info(f"Request payload: {payload}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Make async HTTP request
            async with httpx.AsyncClient(timeout=config["timeouts"]["default"]) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                # Use the correlation ID from the request (not from response)
                correlation_id = x_correlation_id
                
                if response.status_code == 200:
                    data = response.json()
                    data["correlation_id"] = correlation_id
                    logger.info(f"Hotel availability API call successful for property: {request.property_id}")
                    return data
                else:
                    # Handle error response with proper structure
                    try:
                        error_data = response.json()
                        error_data["correlation_id"] = correlation_id
                        logger.error(f"Hotel availability API call failed with status {response.status_code}: {error_data}")
                        
                        # Convert the error response to match our error model format
                        if "desc" not in error_data:
                            # Convert simple error format to our expected format
                            error_response = {
                                "desc": [{
                                    "type": "api_error",
                                    "message": error_data.get("message", "API error occurred"),
                                    "fields": []
                                }],
                                "error": error_data.get("message", "API error occurred"),
                                "status": "failed",
                                "correlation_id": correlation_id
                            }
                            return error_response
                        else:
                            return error_data
                    except:
                        # If JSON parsing fails, return a generic error
                        error_data = {
                            "desc": [{
                                "type": "api_error",
                                "message": response.text,
                                "fields": []
                            }],
                            "error": response.text,
                            "status": "failed",
                            "correlation_id": correlation_id
                        }
                        logger.error(f"Hotel availability API call failed with status {response.status_code}: {error_data}")
                        return error_data
                    
        except httpx.TimeoutException:
            logger.error("Hotel availability API call timed out")
            raise HTTPException(status_code=408, detail="Hotel availability API request timed out")
        except httpx.RequestError as e:
            logger.error(f"Hotel availability API request error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Hotel availability API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in hotel availability: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def get_hotel_price(self, availability_token: str, currency: str = "USD", x_correlation_id: str = None) -> Dict[str, Any]:
        """
        Get hotel pricing using the Xeni API.
        
        Args:
            availability_token: Availability token from availability response
            currency: Currency code (default: USD)
            x_correlation_id: Correlation ID from autosuggest response (optional)
            
        Returns:
            Dict containing the API response
        """
        try:
            logger.info(f"Starting hotel pricing request - Availability Token: {availability_token}, Currency: {currency}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Get HMAC authentication signature
            logger.info("Getting authentication signature...")
            auth_service = AuthService()
            auth_signature = await auth_service.get_valid_auth_token()
            
            if not auth_signature:
                logger.error("Failed to get authentication signature")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to obtain authentication signature for hotel pricing"
                )
            
            logger.info("Authentication signature obtained successfully")
            
            # Build URL with query parameters
            base_url = config['api']['endpoints']['hotel_price']
            query_params = {
                "availability_token": availability_token,
                "currency": currency
            }
            
            # Add query parameters to URL
            import urllib.parse
            query_string = urllib.parse.urlencode(query_params)
            url = f"{base_url}?{query_string}"
            
            logger.info(f"Constructed URL: {url}")
            logger.info(f"Base URL: {base_url}")
            logger.info(f"Query params: {query_params}")
            
            # Prepare headers with HMAC authentication (inherit auth from parent)
            headers = {
                "Authorization": auth_signature,
                "accept-language": config["headers"]["default"]["accept-language"],
                "content-type": config["headers"]["default"]["content-type"]
            }
            
            # Add correlation ID if provided
            if x_correlation_id:
                headers["x-correlation-id"] = x_correlation_id
            
            logger.info(f"Making hotel pricing API call to: {url}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Make async HTTP request
            async with httpx.AsyncClient(timeout=config["timeouts"]["default"]) as client:
                response = await client.get(url, headers=headers)
                
                # Use the correlation ID from the request (not from response)
                correlation_id = x_correlation_id
                
                if response.status_code == 200:
                    data = response.json()
                    data["correlation_id"] = correlation_id
                    logger.info(f"Hotel pricing API call successful for availability token: {availability_token}")
                    return data
                else:
                    # Handle error response with proper structure
                    try:
                        error_data = response.json()
                        error_data["correlation_id"] = correlation_id
                        logger.error(f"Hotel pricing API call failed with status {response.status_code}: {error_data}")
                        
                        # Convert the error response to match our error model format
                        if "desc" not in error_data:
                            # Convert simple error format to our expected format
                            error_response = {
                                "desc": [{
                                    "type": "api_error",
                                    "message": error_data.get("message", "API error occurred"),
                                    "fields": []
                                }],
                                "error": error_data.get("message", "API error occurred"),
                                "status": "failed",
                                "correlation_id": correlation_id
                            }
                            return error_response
                        else:
                            return error_data
                    except:
                        # If JSON parsing fails, return a generic error
                        error_data = {
                            "desc": [{
                                "type": "api_error",
                                "message": response.text,
                                "fields": []
                            }],
                            "error": response.text,
                            "status": "failed",
                            "correlation_id": correlation_id
                        }
                        logger.error(f"Hotel pricing API call failed with status {response.status_code}: {error_data}")
                        return error_data
                    
        except httpx.TimeoutException:
            logger.error("Hotel pricing API call timed out")
            raise HTTPException(status_code=408, detail="Hotel pricing API request timed out")
        except httpx.RequestError as e:
            logger.error(f"Hotel pricing API request error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Hotel pricing API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in hotel pricing: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def book_hotel(self, request: BookHotelRequest, pricing_token: str, x_correlation_id: str = None, db: Session = None) -> Dict[str, Any]:
        """
        Book hotel using the Xeni API and save to database.
        
        Args:
            request: BookHotelRequest with booking details
            pricing_token: Pricing token from pricing response
            x_correlation_id: Correlation ID from autosuggest response (optional)
            db: Database session (optional)
            
        Returns:
            Dict containing the API response and database booking details
        """
        try:
            logger.info(f"Starting hotel booking request - Booking ID: {request.booking_id}, Pricing Token: {pricing_token}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Get HMAC authentication signature
            logger.info("Getting authentication signature...")
            auth_service = AuthService()
            auth_signature = await auth_service.get_valid_auth_token()
            
            if not auth_signature:
                logger.error("Failed to get authentication signature")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to obtain authentication signature for hotel booking"
                )
            
            logger.info("Authentication signature obtained successfully")
            
            # Build URL with query parameters
            base_url = config['api']['endpoints']['hotel_booking']
            query_params = {
                "pricing_token": pricing_token
            }
            
            # Add query parameters to URL
            import urllib.parse
            query_string = urllib.parse.urlencode(query_params)
            url = f"{base_url}?{query_string}"
            
            logger.info(f"Constructed URL: {url}")
            logger.info(f"Base URL: {base_url}")
            logger.info(f"Query params: {query_params}")
            
            # Prepare headers with HMAC authentication (inherit auth from parent)
            headers = {
                "Authorization": auth_signature,
                "accept-language": config["headers"]["default"]["accept-language"],
                "content-type": config["headers"]["default"]["content-type"]
            }
            
            # Add correlation ID if provided
            if x_correlation_id:
                headers["x-correlation-id"] = x_correlation_id
            
            # Prepare request payload
            payload = request.model_dump(exclude_none=True)
            
            logger.info(f"Making hotel booking API call to: {url}")
            logger.info(f"Request payload: {payload}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Make async HTTP request
            async with httpx.AsyncClient(timeout=config["timeouts"]["booking"]) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                # Use the correlation ID from the request (not from response)
                correlation_id = x_correlation_id
                
                if response.status_code == 200:
                    data = response.json()
                    data["correlation_id"] = correlation_id
                    logger.info(f"Hotel booking API call successful for booking ID: {request.booking_id}")
                    
                    # Save booking to database if database session is provided
                    if db and data.get("status") == "success":
                        try:
                            booking_details = await self.save_booking_to_database(db, data, request, pricing_token)
                            data["database_booking"] = booking_details
                            logger.info(f"Booking {request.booking_id} saved to database successfully")
                            
                            # Process payment through Terrapay (completely non-blocking - never fails the booking)
                            await self._process_payment_safely(db, data, request, pricing_token)
                            
                        except Exception as e:
                            logger.error(f"Error saving booking to database: {str(e)}")
                            # Don't fail the booking if database save fails
                            data["database_save_error"] = str(e)
                    
                    return data
                else:
                    # Handle error response with proper structure
                    try:
                        error_data = response.json()
                        error_data["correlation_id"] = correlation_id
                        logger.error(f"Hotel booking API call failed with status {response.status_code}: {error_data}")
                        
                        # Convert the error response to match our error model format
                        if "desc" not in error_data:
                            # Convert simple error format to our expected format
                            error_response = {
                                "desc": [{
                                    "type": "api_error",
                                    "message": error_data.get("message", "API error occurred"),
                                    "fields": []
                                }],
                                "error": error_data.get("message", "API error occurred"),
                                "status": "failed",
                                "correlation_id": correlation_id
                            }
                            return error_response
                        else:
                            return error_data
                    except:
                        # If JSON parsing fails, return a generic error
                        error_data = {
                            "desc": [{
                                "type": "api_error",
                                "message": response.text,
                                "fields": []
                            }],
                            "error": response.text,
                            "status": "failed",
                            "correlation_id": correlation_id
                        }
                        logger.error(f"Hotel booking API call failed with status {response.status_code}: {error_data}")
                        return error_data
                    
        except httpx.TimeoutException:
            logger.error("Hotel booking API call timed out")
            raise HTTPException(status_code=408, detail="Hotel booking API request timed out")
        except httpx.RequestError as e:
            logger.error(f"Hotel booking API request error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Hotel booking API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in hotel booking: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def cancel_booking(self, booking_id: str, request: CancelBookingRequest, x_correlation_id: str = None) -> Dict[str, Any]:
        """
        Cancel hotel booking using the Xeni API.
        
        Args:
            booking_id: Booking ID to cancel
            request: CancelBookingRequest with booking status
            x_correlation_id: Correlation ID from autosuggest response (optional)
            
        Returns:
            Dict containing the API response
        """
        try:
            logger.info(f"Starting hotel booking cancellation request - Booking ID: {booking_id}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Get HMAC authentication signature
            logger.info("Getting authentication signature...")
            auth_service = AuthService()
            auth_signature = await auth_service.get_valid_auth_token()
            
            if not auth_signature:
                logger.error("Failed to get authentication signature")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to obtain authentication signature for hotel booking cancellation"
                )
            
            logger.info("Authentication signature obtained successfully")
            
            # Build URL with booking ID in path using the correct endpoint format
            base_url = config['api']['endpoints']['hotel_cancel_booking']
            url = f"{base_url}/{booking_id}"
            
            logger.info(f"Constructed URL: {url}")
            logger.info(f"Base URL: {base_url}")
            logger.info(f"Booking ID: {booking_id}")
            
            # Prepare headers with HMAC authentication (inherit auth from parent)
            headers = {
                "Authorization": auth_signature,
                "accept-language": config["headers"]["default"]["accept-language"],
                "content-type": config["headers"]["default"]["content-type"]
            }
            
            # Add correlation ID if provided
            if x_correlation_id:
                headers["x-correlation-id"] = x_correlation_id
            
            # Prepare request payload
            payload = request.model_dump(exclude_none=True)
            
            logger.info(f"Making hotel booking cancellation API call to: {url}")
            logger.info(f"Request payload: {payload}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Make async HTTP request (PATCH method for cancellation)
            async with httpx.AsyncClient(timeout=config["timeouts"]["booking"]) as client:
                response = await client.patch(url, headers=headers, json=payload)
                
                # Use the correlation ID from the request (not from response)
                correlation_id = x_correlation_id
                
                if response.status_code == 200:
                    data = response.json()
                    data["correlation_id"] = correlation_id
                    logger.info(f"Hotel booking cancellation API call successful for booking ID: {booking_id}")
                    return data
                else:
                    # Handle error response with proper structure
                    try:
                        error_data = response.json()
                        error_data["correlation_id"] = correlation_id
                        logger.error(f"Hotel booking cancellation API call failed with status {response.status_code}: {error_data}")
                        
                        # Convert the error response to match our error model format
                        if "desc" not in error_data:
                            # Convert simple error format to our expected format
                            error_response = {
                                "desc": [{
                                    "type": "api_error",
                                    "message": error_data.get("message", "API error occurred"),
                                    "fields": []
                                }],
                                "error": error_data.get("message", "API error occurred"),
                                "status": "failed",
                                "correlation_id": correlation_id
                            }
                            return error_response
                        else:
                            return error_data
                    except:
                        # If JSON parsing fails, return a generic error
                        error_data = {
                            "desc": [{
                                "type": "api_error",
                                "message": response.text,
                                "fields": []
                            }],
                            "error": response.text,
                            "status": "failed",
                            "correlation_id": correlation_id
                        }
                        logger.error(f"Hotel booking cancellation API call failed with status {response.status_code}: {error_data}")
                        return error_data
                    
        except httpx.TimeoutException:
            logger.error("Hotel booking cancellation API call timed out")
            raise HTTPException(status_code=408, detail="Hotel booking cancellation API request timed out")
        except httpx.RequestError as e:
            logger.error(f"Hotel booking cancellation API request error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Hotel booking cancellation API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in hotel booking cancellation: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def search_hotels_and_save(self, request: HotelSearchRequest, x_correlation_id: str, db: Session) -> Dict[str, Any]:
        """
        Search hotels using the Xeni API and save results to database.
        
        Args:
            request: HotelSearchRequest with search criteria
            x_correlation_id: Correlation ID from autosuggest response
            db: Database session
            
        Returns:
            Dict containing the API response
        """
        try:
            logger.info(f"Starting hotel search and save for place: {request.place_id}")
            
            # First, call the regular search API
            search_result = await self.search_hotels(request, x_correlation_id)
            
            # If search was successful, save the results to database
            if search_result.get("status") == "success":
                await self.save_hotel_search_results_v3(db, search_result)
                logger.info("Hotel search results saved to database successfully")
            
            return search_result
            
        except Exception as e:
            logger.error(f"Error in hotel search and save: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def get_hotel_price_and_save(self, availability_token: str, currency: str = "USD", x_correlation_id: str = None, db: Session = None) -> Dict[str, Any]:
        """
        Get hotel pricing using the Xeni API and save room details to database.
        
        Args:
            availability_token: Availability token from availability response
            currency: Currency code (default: USD)
            x_correlation_id: Correlation ID from autosuggest response (optional)
            db: Database session
            
        Returns:
            Dict containing the API response
        """
        try:
            logger.info(f"Starting hotel price and save for token: {availability_token}")
            
            # First, call the regular price API
            price_result = await self.get_hotel_price(availability_token, currency, x_correlation_id)
            
            # If price was successful, save the results to database
            if price_result.get("status") == "success" and db:
                await self.save_hotel_price_results_v2(db, price_result)
                logger.info("Hotel price results saved to database successfully")
            
            return price_result
            
        except Exception as e:
            logger.error(f"Error in hotel price and save: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def save_hotel_search_results(self, db: Session, search_response: Dict[str, Any]) -> List[Any]:
        """
        Save hotel search results to database.
        
        Args:
            db: Database session
            search_response: Search API response
            
        Returns:
            List of saved hotel records
        """
        try:
            from app.models.hotel_entities import Hotel, HotelAmenity, HotelImage
            
            saved_hotels = []
            hotels_data = search_response.get("data", {}).get("hotels", [])
            
            for hotel_data in hotels_data:
                # Check if hotel already exists
                existing_hotel = db.query(Hotel).filter(
                    Hotel.api_hotel_id == hotel_data["property_id"]
                ).first()
                
                if existing_hotel:
                    logger.info(f"Hotel {hotel_data['property_id']} already exists, skipping")
                    saved_hotels.append(existing_hotel)
                    continue
                
                # Create new hotel record
                hotel = Hotel(
                    api_hotel_id=hotel_data["property_id"],
                    name=hotel_data["name"],
                    latitude=hotel_data["location"]["lat"],
                    longitude=hotel_data["location"]["long"],
                    phone=hotel_data["contact"]["phone"],
                    address=hotel_data["contact"]["address"]["line_1"],
                    city=hotel_data["contact"]["address"]["city"],
                    state=hotel_data["contact"]["address"]["state"],
                    country=hotel_data["contact"]["address"]["country"],
                    postal_code=hotel_data["contact"]["address"]["postal_code"],
                    star_rating=hotel_data["ratings"]["star_rating"],
                    avg_rating=hotel_data["ratings"]["user_rating"],
                    chain=hotel_data.get("chain", "Unknown")
                )
                
                db.add(hotel)
                db.flush()  # Get the hotel ID
                
                # Save hotel amenities
                for amenity_name in hotel_data.get("amenities", []):
                    amenity = HotelAmenity(
                        hotel_id=hotel.id,
                        amenity_name=amenity_name,
                        amenity_type="general"  # Default type
                    )
                    db.add(amenity)
                
                # Save hotel images
                image_data = hotel_data.get("image", {})
                if image_data:
                    # Thumbnail image
                    if image_data.get("thumbnail"):
                        image = HotelImage(
                            hotel_id=hotel.id,
                            image=image_data["thumbnail"],
                            is_primary=True,
                            sort_order=1
                        )
                        db.add(image)
                    
                    # Large image
                    if image_data.get("large"):
                        image = HotelImage(
                            hotel_id=hotel.id,
                            image=image_data["large"],
                            is_primary=False,
                            sort_order=2
                        )
                        db.add(image)
                    
                    # Extra large image
                    if image_data.get("extra_large"):
                        image = HotelImage(
                            hotel_id=hotel.id,
                            image=image_data["extra_large"],
                            is_primary=False,
                            sort_order=3
                        )
                        db.add(image)
                
                saved_hotels.append(hotel)
            
            db.commit()
            logger.info(f"Saved {len(saved_hotels)} hotels to database")
            return saved_hotels
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving hotel search results: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e

    async def save_hotel_price_results(self, db: Session, price_response: Dict[str, Any]) -> List[Any]:
        """
        Save hotel price results to database.
        
        Args:
            db: Database session
            price_response: Price API response
            
        Returns:
            List of saved room records
        """
        try:
            from app.models.hotel_entities import Hotel, Room, RoomAmenity, RoomImage
            
            saved_rooms = []
            price_data = price_response.get("data", {})
            property_id = price_data.get("property_id")
            
            # Find the hotel by api_hotel_id
            hotel = db.query(Hotel).filter(Hotel.api_hotel_id == property_id).first()
            if not hotel:
                logger.error(f"Hotel not found for property_id: {property_id}")
                raise ValueError(f"Hotel not found for property_id: {property_id}")
            
            rooms_data = price_data.get("rooms", [])
            
            for room_data in rooms_data:
                # Check if room already exists
                existing_room = db.query(Room).filter(
                    Room.room_id == room_data["id"]
                ).first()
                
                if existing_room:
                    logger.info(f"Room {room_data['id']} already exists, updating")
                    # Update existing room with new pricing
                    existing_room.base_rate = price_data.get("base_rate")
                    existing_room.total_rate = price_data.get("total_price")
                    existing_room.published_rate = price_data.get("retail_price")
                    existing_room.taxes_and_fees = price_data.get("tax_and_fees")
                    existing_room.currency = price_data.get("currency")
                    existing_room.availability = price_data.get("status")
                    existing_room.cancellation_policy = price_data.get("cancellation_policy")
                    existing_room.booking_conditions = {
                        "refundable": price_data.get("refundable"),
                        "board_basis": price_data.get("board_basis"),
                        "all_guest_info_required": room_data.get("all_guest_info_required"),
                        "special_request_supported": room_data.get("special_request_supported")
                    }
                    saved_rooms.append(existing_room)
                    continue
                
                # Create new room record
                room = Room(
                    room_id=room_data["id"],
                    hotel_id=hotel.id,
                    api_hotel_id=property_id,
                    name=room_data["name"],
                    total_sleep=room_data.get("number_of_adults", 1),
                    beds=[{"type": "bed", "description": room_data.get("bed", "")}],  # Store bed info as JSON
                    availability=price_data.get("status"),
                    currency=price_data.get("currency"),
                    base_rate=price_data.get("base_rate"),
                    total_rate=price_data.get("total_price"),
                    published_rate=price_data.get("retail_price"),
                    taxes_and_fees=price_data.get("tax_and_fees"),
                    cancellation_policy=price_data.get("cancellation_policy"),
                    booking_conditions={
                        "refundable": price_data.get("refundable"),
                        "board_basis": price_data.get("board_basis"),
                        "all_guest_info_required": room_data.get("all_guest_info_required"),
                        "special_request_supported": room_data.get("special_request_supported")
                    }
                )
                
                db.add(room)
                db.flush()  # Get the room ID
                
                # Save room amenities
                for amenity_name in room_data.get("amenities", []):
                    amenity = RoomAmenity(
                        room_id=room.id,
                        amenity_name=amenity_name,
                        amenity_type="general"  # Default type
                    )
                    db.add(amenity)
                
                # Save room images
                images_data = room_data.get("images", {})
                sort_order = 1
                for size in ["thumbnail", "small", "large", "extra_large"]:
                    if images_data.get(size):
                        for image_url in images_data[size]:
                            image = RoomImage(
                                room_id=room.id,
                                image_url=image_url,
                                size=size,
                                is_primary=(size == "thumbnail"),
                                sort_order=sort_order
                            )
                            db.add(image)
                            sort_order += 1
                
                saved_rooms.append(room)
            
            db.commit()
            logger.info(f"Saved {len(saved_rooms)} rooms to database")
            return saved_rooms
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving hotel price results: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e

    async def save_hotel_price_results_v2(self, db: Session, price_response: Dict[str, Any]) -> List[Any]:
        """
        Save hotel price results to database (v2 - with duplicate prevention).
        
        Args:
            db: Database session
            price_response: Price API response
            
        Returns:
            List of saved room records
        """
        try:
            from app.models.hotel_entities import Hotel, Room, RoomAmenity, RoomImage
            
            saved_rooms = []
            price_data = price_response.get("data", {})
            property_id = price_data.get("property_id")
            
            # Find the hotel by api_hotel_id
            hotel = db.query(Hotel).filter(Hotel.api_hotel_id == property_id).first()
            if not hotel:
                logger.error(f"Hotel not found for property_id: {property_id}")
                raise ValueError(f"Hotel not found for property_id: {property_id}")
            
            rooms_data = price_data.get("rooms", [])
            
            for room_data in rooms_data:
                # Check if room already exists
                existing_room = db.query(Room).filter(
                    Room.room_id == room_data["id"]
                ).first()
                
                if existing_room:
                    logger.info(f"Room {room_data['id']} already exists, updating")
                    # Update existing room with new pricing
                    existing_room.base_rate = price_data.get("base_rate")
                    existing_room.total_rate = price_data.get("total_price")
                    existing_room.published_rate = price_data.get("retail_price")
                    existing_room.taxes_and_fees = price_data.get("tax_and_fees")
                    existing_room.currency = price_data.get("currency")
                    existing_room.availability = price_data.get("status")
                    existing_room.cancellation_policy = price_data.get("cancellation_policy")
                    existing_room.booking_conditions = {
                        "refundable": price_data.get("refundable"),
                        "board_basis": price_data.get("board_basis"),
                        "all_guest_info_required": room_data.get("all_guest_info_required"),
                        "special_request_supported": room_data.get("special_request_supported")
                    }
                    saved_rooms.append(existing_room)
                    continue
                
                # Create new room record
                room = Room(
                    room_id=room_data["id"],
                    hotel_id=hotel.id,
                    api_hotel_id=property_id,
                    name=room_data["name"],
                    total_sleep=room_data.get("number_of_adults", 1),
                    beds=[{"type": "bed", "description": room_data.get("bed", "")}],  # Store bed info as JSON
                    availability=price_data.get("status"),
                    currency=price_data.get("currency"),
                    base_rate=price_data.get("base_rate"),
                    total_rate=price_data.get("total_price"),
                    published_rate=price_data.get("retail_price"),
                    taxes_and_fees=price_data.get("tax_and_fees"),
                    cancellation_policy=price_data.get("cancellation_policy"),
                    booking_conditions={
                        "refundable": price_data.get("refundable"),
                        "board_basis": price_data.get("board_basis"),
                        "all_guest_info_required": room_data.get("all_guest_info_required"),
                        "special_request_supported": room_data.get("special_request_supported")
                    }
                )
                
                db.add(room)
                db.flush()  # Get the room ID
                
                # Save room amenities (check for duplicates)
                for amenity_name in room_data.get("amenities", []):
                    # Check if amenity already exists
                    existing_amenity = db.query(RoomAmenity).filter(
                        RoomAmenity.room_id == room.id,
                        RoomAmenity.amenity_name == amenity_name
                    ).first()
                    
                    if not existing_amenity:
                        amenity = RoomAmenity(
                            room_id=room.id,
                            amenity_name=amenity_name,
                            amenity_type="general"  # Default type
                        )
                        db.add(amenity)
                
                # Save room images (check for duplicates)
                images_data = room_data.get("images", {})
                sort_order = 1
                for size in ["thumbnail", "small", "large", "extra_large"]:
                    if images_data.get(size):
                        for image_url in images_data[size]:
                            # Check if image already exists
                            existing_image = db.query(RoomImage).filter(
                                RoomImage.room_id == room.id,
                                RoomImage.image_url == image_url
                            ).first()
                            
                            if not existing_image:
                                image = RoomImage(
                                    room_id=room.id,
                                    image_url=image_url,
                                    size=size,
                                    is_primary=(size == "thumbnail"),
                                    sort_order=sort_order
                                )
                                db.add(image)
                            sort_order += 1
                
                saved_rooms.append(room)
            
            db.commit()
            logger.info(f"Saved {len(saved_rooms)} rooms to database")
            return saved_rooms
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving hotel price results v2: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e

    async def _process_payment_safely(self, db: Session, booking_data: Dict[str, Any], request: BookHotelRequest, pricing_token: str) -> None:
        """
        Safely process payment through Terrapay without ever failing the booking.
        This method is completely non-blocking and will never raise exceptions.
        """
        try:
            # Check if Terrapay integration is enabled
            terrapay_enabled = config.get('terrapay', {}).get('enabled', True)
            if not terrapay_enabled:
                logger.info("Terrapay integration is disabled, skipping payment processing")
                return
            
            # Process payment in a separate try-catch to ensure it never affects the booking
            payment_result = await self.process_booking_payment(db, booking_data, request, pricing_token)
            booking_data["payment_processing"] = payment_result
            logger.info(f"Payment processing completed successfully for booking {request.booking_id}")
            
        except Exception as payment_error:
            # Log the error but never fail the booking
            logger.error(f"Payment processing failed for booking {request.booking_id}: {str(payment_error)}")
            logger.error(f"Payment error traceback: {traceback.format_exc()}")
            
            # Add error info to response without failing the booking
            booking_data["payment_error"] = {
                "error": str(payment_error),
                "timestamp": datetime.utcnow().isoformat(),
                "booking_id": request.booking_id
            }
            
            logger.info(f"Booking {request.booking_id} completed successfully despite payment processing failure")

    async def process_booking_payment(
        self, 
        db: Session, 
        booking_response: Dict[str, Any], 
        booking_request: BookHotelRequest, 
        pricing_token: str
    ) -> Dict[str, Any]:
        """
        Process payment for successful booking through TerraPay with retry logic.
        """
        try:
            from app.services.terrapay_service import TerraPayService
            from app.models.terrapay_models import PaymentRequest
            from app.models.payment_entities import PaymentTransaction
            from app.models.hotel_entities import Room
            
            # Find room and calculate payment amount
            room = db.query(Room).filter(Room.booking_conditions.contains({"pricing_token": pricing_token})).first()
            if not room:
                raise ValueError(f"Room not found for pricing token: {pricing_token}")
            
            # Calculate payment amount with charges
            base_amount = room.total_rate
            service_charge = base_amount * 0.10  # 10% service charge
            additional_charge = base_amount * 0.05  # 5% additional charge
            total_amount = base_amount + service_charge + additional_charge
            
            # Create payment request
            payment_request = PaymentRequest(
                booking_id=booking_response["data"]["booking_id"],
                amount=total_amount,
                currency="USD",  # Will be configurable
                customer_email=booking_request.email,
                agent_card_profile_id="4",  # Will be configurable
                booking_reference=booking_response["data"]["booking_id"],
                additional_restrictions={
                    "singleCardUse": True,
                    "maxDailyAmount": total_amount
                }
            )
            
            # Create payment transaction record
            from datetime import datetime
            payment_transaction = PaymentTransaction(
                payment_id=f"PAY_{payment_request.booking_id}_{int(datetime.utcnow().timestamp())}",
                booking_id=payment_request.booking_id,
                amount=base_amount,
                service_charge=service_charge,
                additional_charge=additional_charge,
                total_amount=total_amount,
                currency=payment_request.currency,
                customer_email=payment_request.customer_email,
                status="PENDING"
            )
            
            db.add(payment_transaction)
            db.commit()
            
            # Process payment through TerraPay with retry logic
            terrapay_service = TerraPayService()
            payment_result = await terrapay_service.process_booking_payment_with_retry(
                payment_request, 
                payment_transaction, 
                db
            )
            
            return payment_result
        
        except Exception as e:
            logger.error(f"Error processing booking payment: {str(e)}")
            raise e

    async def save_booking_to_database(
        self, 
        db: Session, 
        api_response: Dict[str, Any], 
        request: BookHotelRequest, 
        pricing_token: str
    ) -> Dict[str, Any]:
        """
        Save booking details to database with proper relationships.
        
        Args:
            db: Database session
            api_response: Xeni API booking response
            request: Original booking request
            pricing_token: Pricing token used
            
        Returns:
            Saved booking record
        """
        try:
            from app.models.hotel_entities import Booking, Hotel, Room
            import time
            
            # Extract booking data from API response
            booking_data = api_response.get("data", {})
            booking_id = booking_data.get("booking_id")
            booking_status = booking_data.get("booking_status")
            
            # Find hotel by pricing token (look in rooms table)
            room = db.query(Room).filter(Room.booking_conditions.contains({"pricing_token": pricing_token})).first()
            if not room:
                # Fallback: try to find by any room with this pricing token
                room = db.query(Room).filter(Room.booking_conditions.contains({"token": pricing_token})).first()
            
            hotel = None
            if room:
                hotel = room.hotel
            else:
                # If no room found, try to find hotel by other means
                # This is a fallback - in practice, pricing token should be linked to room
                logger.warning(f"Could not find room for pricing token: {pricing_token}")
            
            # Create booking record
            booking = Booking(
                booking_ref_id=f"BK_{booking_id}_{int(time.time())}",  # Internal reference
                booking_id=booking_id,
                hotel_id=hotel.id if hotel else None,
                room_id=room.id if room else None,
                pricing_token=pricing_token,
                booking_status=booking_status,
                guest_details=[guest.model_dump() for guest in request.rooms],
                contact_email=request.email,
                contact_phone=request.phone.model_dump(),
                api_response=api_response,
                correlation_id=api_response.get("correlation_id"),
                # Legacy fields for backward compatibility
                billing_email=request.email,
                booking_data=str(api_response),  # Store as string for legacy compatibility
                response_data=str(api_response)
            )
            
            db.add(booking)
            db.commit()
            db.refresh(booking)
            
            logger.info(f"Booking {booking_id} saved to database with ID: {booking.id}")
            
            # Return booking details with relationships
            booking_details = {
                "id": booking.id,
                "booking_ref_id": booking.booking_ref_id,
                "booking_id": booking.booking_id,
                "booking_status": booking.booking_status,
                "hotel_id": booking.hotel_id,
                "room_id": booking.room_id,
                "created_at": booking.created_at.isoformat() if booking.created_at else None
            }
            
            return booking_details
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving booking to database: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e

    async def save_hotel_search_results_v2(self, db: Session, search_response: Dict[str, Any]) -> List[Any]:
        """
        Save hotel search results to database (v2 - compatible with existing Hotel model).
        
        Args:
            db: Database session
            search_response: Search API response
            
        Returns:
            List of saved hotel records
        """
        try:
            from app.models.hotel_entities import Hotel, HotelAmenity, HotelImage
            
            saved_hotels = []
            hotels_data = search_response.get("data", {}).get("hotels", [])
            
            for hotel_data in hotels_data:
                # Check if hotel already exists
                existing_hotel = db.query(Hotel).filter(
                    Hotel.api_hotel_id == hotel_data["property_id"]
                ).first()
                
                if existing_hotel:
                    logger.info(f"Hotel {hotel_data['property_id']} already exists, skipping")
                    saved_hotels.append(existing_hotel)
                    continue
                
                # Create new hotel record (only with fields that exist in Hotel model)
                hotel = Hotel(
                    api_hotel_id=hotel_data["property_id"],
                    name=hotel_data["name"],
                    latitude=hotel_data["location"]["lat"],
                    longitude=hotel_data["location"]["long"],
                    phone=hotel_data["contact"]["phone"],
                    address=hotel_data["contact"]["address"]["line_1"],
                    city=hotel_data["contact"]["address"]["city"],
                    state=hotel_data["contact"]["address"]["state"],
                    country=hotel_data["contact"]["address"]["country"],
                    postal_code=hotel_data["contact"]["address"]["postal_code"],
                    star_rating=hotel_data["ratings"]["star_rating"],
                    avg_rating=hotel_data["ratings"]["user_rating"]
                    # Note: chain field removed as it doesn't exist in Hotel model
                )
                
                db.add(hotel)
                db.flush()  # Get the hotel ID
                
                # Save hotel amenities
                for amenity_name in hotel_data.get("amenities", []):
                    amenity = HotelAmenity(
                        hotel_id=hotel.id,
                        amenity_name=amenity_name,
                        amenity_type="general"  # Default type
                    )
                    db.add(amenity)
                
                # Save hotel images
                image_data = hotel_data.get("image", {})
                if image_data:
                    # Thumbnail image
                    if image_data.get("thumbnail"):
                        image = HotelImage(
                            hotel_id=hotel.id,
                            image=image_data["thumbnail"],
                            is_primary=True,
                            sort_order=1
                        )
                        db.add(image)
                    
                    # Large image
                    if image_data.get("large"):
                        image = HotelImage(
                            hotel_id=hotel.id,
                            image=image_data["large"],
                            is_primary=False,
                            sort_order=2
                        )
                        db.add(image)
                    
                    # Extra large image
                    if image_data.get("extra_large"):
                        image = HotelImage(
                            hotel_id=hotel.id,
                            image=image_data["extra_large"],
                            is_primary=False,
                            sort_order=3
                        )
                        db.add(image)
                
                saved_hotels.append(hotel)
            
            db.commit()
            logger.info(f"Saved {len(saved_hotels)} hotels to database")
            return saved_hotels
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving hotel search results v2: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e

    async def save_hotel_search_results_v3(self, db: Session, search_response: Dict[str, Any]) -> List[Any]:
        """
        Save hotel search results to database (v3 - with duplicate prevention).
        
        Args:
            db: Database session
            search_response: Search API response
            
        Returns:
            List of saved hotel records
        """
        try:
            from app.models.hotel_entities import Hotel, HotelAmenity, HotelImage
            
            saved_hotels = []
            hotels_data = search_response.get("data", {}).get("hotels", [])
            
            for hotel_data in hotels_data:
                # Check if hotel already exists
                existing_hotel = db.query(Hotel).filter(
                    Hotel.api_hotel_id == hotel_data["property_id"]
                ).first()
                
                if existing_hotel:
                    logger.info(f"Hotel {hotel_data['property_id']} already exists, skipping")
                    saved_hotels.append(existing_hotel)
                    continue
                
                # Create new hotel record (only with fields that exist in Hotel model)
                hotel = Hotel(
                    api_hotel_id=hotel_data["property_id"],
                    name=hotel_data["name"],
                    latitude=hotel_data["location"]["lat"],
                    longitude=hotel_data["location"]["long"],
                    phone=hotel_data["contact"]["phone"],
                    address=hotel_data["contact"]["address"]["line_1"],
                    city=hotel_data["contact"]["address"]["city"],
                    state=hotel_data["contact"]["address"]["state"],
                    country=hotel_data["contact"]["address"]["country"],
                    postal_code=hotel_data["contact"]["address"]["postal_code"],
                    star_rating=hotel_data["ratings"]["star_rating"],
                    avg_rating=hotel_data["ratings"]["user_rating"]
                )
                
                db.add(hotel)
                db.flush()  # Get the hotel ID
                
                # Save hotel amenities (check for duplicates)
                for amenity_name in hotel_data.get("amenities", []):
                    # Check if amenity already exists
                    existing_amenity = db.query(HotelAmenity).filter(
                        HotelAmenity.hotel_id == hotel.id,
                        HotelAmenity.amenity_name == amenity_name
                    ).first()
                    
                    if not existing_amenity:
                        amenity = HotelAmenity(
                            hotel_id=hotel.id,
                            amenity_name=amenity_name,
                            amenity_type="general"  # Default type
                        )
                        db.add(amenity)
                
                # Save hotel images (check for duplicates)
                image_data = hotel_data.get("image", {})
                if image_data:
                    # Thumbnail image
                    if image_data.get("thumbnail"):
                        existing_image = db.query(HotelImage).filter(
                            HotelImage.hotel_id == hotel.id,
                            HotelImage.image == image_data["thumbnail"]
                        ).first()
                        
                        if not existing_image:
                            image = HotelImage(
                                hotel_id=hotel.id,
                                image=image_data["thumbnail"],
                                is_primary=True,
                                sort_order=1
                            )
                            db.add(image)
                    
                    # Large image
                    if image_data.get("large"):
                        existing_image = db.query(HotelImage).filter(
                            HotelImage.hotel_id == hotel.id,
                            HotelImage.image == image_data["large"]
                        ).first()
                        
                        if not existing_image:
                            image = HotelImage(
                                hotel_id=hotel.id,
                                image=image_data["large"],
                                is_primary=False,
                                sort_order=2
                            )
                            db.add(image)
                    
                    # Extra large image
                    if image_data.get("extra_large"):
                        existing_image = db.query(HotelImage).filter(
                            HotelImage.hotel_id == hotel.id,
                            HotelImage.image == image_data["extra_large"]
                        ).first()
                        
                        if not existing_image:
                            image = HotelImage(
                                hotel_id=hotel.id,
                                image=image_data["extra_large"],
                                is_primary=False,
                                sort_order=3
                            )
                            db.add(image)
                
                saved_hotels.append(hotel)
            
            db.commit()
            logger.info(f"Saved {len(saved_hotels)} hotels to database")
            return saved_hotels
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving hotel search results v3: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e