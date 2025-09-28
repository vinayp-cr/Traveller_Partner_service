#!/usr/bin/env python3
"""
Search Filters Service
Business logic for hotel search filtering
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from app.models.search_filter_models import (
    HotelFilterRequest, HotelFilterResponse, HotelSearchResult, 
    FilterOptions, HotelFilters, Pagination
)
from app.api.repositories.search_filters_repository import SearchFiltersRepository
from app.api.services.hotel_service import HotelService
from app.core.logger import logger


class SearchFiltersService:
    """Service for hotel search filtering operations"""
    
    def __init__(self):
        self.repository = SearchFiltersRepository()
        self.hotel_service = HotelService()
        self.logger = logger
    
    def search_hotels_filtered(self, db: Session, request: HotelFilterRequest) -> HotelFilterResponse:
        """
        Search hotels with applied filters
        
        Args:
            db: Database session
            request: Filter request with search criteria and filters
            
        Returns:
            HotelFilterResponse with filtered results
        """
        try:
            self.logger.info(f"Processing filtered hotel search request - Location: {request.locationId}")
            
            # Set default pagination if not provided
            pagination = request.pagination or Pagination(page=1, limit=20)
            filters = request.filters or HotelFilters()
            
            # First, get basic search results from API (if needed for price data)
            api_results = None
            try:
                # Convert to HotelSearchRequest for API call
                from app.models.hotel_search_models import HotelSearchRequest
                api_request = HotelSearchRequest(
                    locationId=request.locationId,
                    checkInDate=request.checkInDate,
                    checkOutDate=request.checkOutDate,
                    occupancies=request.occupancies,
                    currency=request.currency
                )
                api_response = self.hotel_service.search_hotels_api_only(api_request, db)
                api_results = api_response.get("hotels", []) if isinstance(api_response, dict) else []
            except Exception as e:
                self.logger.warning(f"Could not fetch API results: {str(e)}")
                api_results = []
            
            # Get filtered hotels from database
            filtered_hotels, total_count = self.repository.search_hotels_with_filters(
                db, filters, pagination
            )
            
            # Convert to response format
            hotel_results = self._convert_hotels_to_results(db, filtered_hotels, api_results)
            
            # Get available filter options
            filter_options = self.repository.get_available_filter_options(db)
            
            # Calculate total pages
            total_pages = (total_count + pagination.limit - 1) // pagination.limit
            
            # Get filter statistics
            filter_stats = self.repository.get_filter_stats(db, filters)
            
            return HotelFilterResponse(
                status="success",
                message=f"Found {len(hotel_results)} hotels out of {total_count} total",
                data={
                    "hotels": hotel_results,
                    "totalCount": total_count,
                    "page": pagination.page,
                    "limit": pagination.limit,
                    "totalPages": total_pages,
                    "filters": filter_options,
                    "stats": filter_stats
                },
                hotels=hotel_results,
                totalCount=total_count,
                page=pagination.page,
                limit=pagination.limit,
                totalPages=total_pages,
                filters=filter_options
            )
            
        except Exception as e:
            self.logger.error(f"Error in search_hotels_filtered: {str(e)}")
            return HotelFilterResponse(
                status="error",
                message=f"Search failed: {str(e)}",
                data={},
                hotels=[],
                totalCount=0,
                page=1,
                limit=20,
                totalPages=0
            )
    
    def _convert_hotels_to_results(self, db: Session, hotels: List, api_results: List[Dict] = None) -> List[HotelSearchResult]:
        """
        Convert hotel entities to search result format
        
        Args:
            db: Database session
            hotels: List of hotel entities
            api_results: API results for price data
            
        Returns:
            List of HotelSearchResult objects
        """
        try:
            results = []
            api_hotels_map = {}
            
            # Create map of API results by hotel ID for price data
            if api_results:
                for api_hotel in api_results:
                    if isinstance(api_hotel, dict) and "id" in api_hotel:
                        api_hotels_map[str(api_hotel["id"])] = api_hotel
            
            for hotel in hotels:
                # Get hotel with amenities and images
                hotel_with_details = self.repository.get_hotel_with_details(db, hotel.id)
                
                # Get price from API results if available
                price = None
                currency = "USD"
                if str(hotel.id) in api_hotels_map:
                    api_hotel = api_hotels_map[str(hotel.id)]
                    # Extract price from API response (adjust field names as needed)
                    if "rate" in api_hotel and "price" in api_hotel["rate"]:
                        price = float(api_hotel["rate"]["price"])
                    elif "price" in api_hotel:
                        price = float(api_hotel["price"])
                    if "currency" in api_hotel:
                        currency = api_hotel["currency"]
                
                # Convert amenities
                amenities = []
                if hotel_with_details and hasattr(hotel_with_details, 'amenities'):
                    amenities = [
                        {
                            "id": amenity.id,
                            "name": amenity.amenity_name,
                            "type": amenity.amenity_type,
                            "icon": amenity.icon
                        }
                        for amenity in hotel_with_details.amenities
                    ]
                
                # Convert images
                images = []
                if hotel_with_details and hasattr(hotel_with_details, 'images'):
                    images = [
                        {
                            "id": image.id,
                            "url": image.image,
                            "caption": image.caption,
                            "is_primary": image.is_primary,
                            "sort_order": image.sort_order
                        }
                        for image in hotel_with_details.images
                    ]
                
                # Create search result
                result = HotelSearchResult(
                    id=hotel.id,
                    name=hotel.name,
                    description=hotel.description,
                    address=hotel.address,
                    city=hotel.city,
                    state=hotel.state,
                    country=hotel.country,
                    postal_code=hotel.postal_code,
                    latitude=float(hotel.latitude) if hotel.latitude else None,
                    longitude=float(hotel.longitude) if hotel.longitude else None,
                    phone=hotel.phone,
                    email=hotel.email,
                    website=hotel.website,
                    star_rating=hotel.star_rating,
                    avg_rating=float(hotel.avg_rating) if hotel.avg_rating else None,
                    total_reviews=hotel.total_reviews,
                    amenities=amenities,
                    images=images,
                    price=price,
                    currency=currency
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error converting hotels to results: {str(e)}")
            return []
    
    def get_filter_options(self, db: Session) -> FilterOptions:
        """
        Get available filter options
        
        Args:
            db: Database session
            
        Returns:
            FilterOptions with available choices
        """
        try:
            return self.repository.get_available_filter_options(db)
        except Exception as e:
            self.logger.error(f"Error getting filter options: {str(e)}")
            raise e
    
    def get_filter_stats(self, db: Session, filters: Optional[HotelFilters] = None) -> Dict[str, Any]:
        """
        Get filter statistics
        
        Args:
            db: Database session
            filters: Applied filters
            
        Returns:
            Dictionary with statistics
        """
        try:
            return self.repository.get_filter_stats(db, filters)
        except Exception as e:
            self.logger.error(f"Error getting filter stats: {str(e)}")
            raise e
    
    def search_hotels_by_amenities(self, db: Session, amenities: List[str], limit: int = 10) -> List[HotelSearchResult]:
        """
        Search hotels by specific amenities
        
        Args:
            db: Database session
            amenities: List of amenity names
            limit: Maximum number of results
            
        Returns:
            List of hotels with specified amenities
        """
        try:
            filters = HotelFilters(amenities=amenities)
            pagination = Pagination(page=1, limit=limit)
            
            hotels, _ = self.repository.search_hotels_with_filters(db, filters, pagination)
            return self._convert_hotels_to_results(db, hotels)
            
        except Exception as e:
            self.logger.error(f"Error searching hotels by amenities: {str(e)}")
            return []
    
    def search_hotels_by_rating(self, db: Session, min_rating: float, limit: int = 10) -> List[HotelSearchResult]:
        """
        Search hotels by minimum rating
        
        Args:
            db: Database session
            min_rating: Minimum rating threshold
            limit: Maximum number of results
            
        Returns:
            List of hotels above rating threshold
        """
        try:
            filters = HotelFilters(guestRating=min_rating)
            pagination = Pagination(page=1, limit=limit)
            
            hotels, _ = self.repository.search_hotels_with_filters(db, filters, pagination)
            return self._convert_hotels_to_results(db, hotels)
            
        except Exception as e:
            self.logger.error(f"Error searching hotels by rating: {str(e)}")
            return []
    
    def search_hotels_by_location(self, db: Session, location: str, limit: int = 10) -> List[HotelSearchResult]:
        """
        Search hotels by location/neighborhood
        
        Args:
            db: Database session
            location: Location/neighborhood name
            limit: Maximum number of results
            
        Returns:
            List of hotels in specified location
        """
        try:
            filters = HotelFilters(neighborhoods=[location])
            pagination = Pagination(page=1, limit=limit)
            
            hotels, _ = self.repository.search_hotels_with_filters(db, filters, pagination)
            return self._convert_hotels_to_results(db, hotels)
            
        except Exception as e:
            self.logger.error(f"Error searching hotels by location: {str(e)}")
            return []
