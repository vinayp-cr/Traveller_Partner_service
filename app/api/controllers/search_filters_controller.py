#!/usr/bin/env python3
"""
Search Filters Controller
API endpoints for hotel search filtering
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.db import get_db
from app.core.logger import logger
from app.models.search_filter_models import (
    HotelFilterRequest, HotelFilterResponse, FilterOptions, 
    HotelSearchResult, HotelFilters
)
from app.api.services.search_filters_service import SearchFiltersService

router = APIRouter(prefix="/api/hotel/filters", tags=["Hotel Search Filters"])


def get_search_filters_service() -> SearchFiltersService:
    """Dependency injection for SearchFiltersService"""
    return SearchFiltersService()


@router.post("/search", response_model=HotelFilterResponse, tags=["Hotel Search Filters"])
def search_hotels_filtered(
    request: HotelFilterRequest,
    db: Session = Depends(get_db),
    service: SearchFiltersService = Depends(get_search_filters_service)
):
    """
    Search hotels with advanced filtering options
    
    This endpoint allows filtering hotels by:
    - Star rating
    - Guest rating
    - Amenities
    - Neighborhoods
    - Property name
    - Budget range
    - Property types and themes
    - Nearby attractions
    
    Supports sorting by:
    - Recommended (default)
    - Price (low to high / high to low)
    - Rating
    - Star rating
    - Name (A-Z / Z-A)
    """
    try:
        logger.info(f"Processing filtered hotel search request - Location: {request.locationId}")
        return service.search_hotels_filtered(db, request)
    except Exception as e:
        logger.error(f"Error in search_hotels_filtered endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/options", response_model=FilterOptions, tags=["Hotel Search Filters"])
def get_filter_options(
    db: Session = Depends(get_db),
    service: SearchFiltersService = Depends(get_search_filters_service)
):
    """
    Get available filter options for the UI
    
    Returns all available:
    - Amenities with counts
    - Neighborhoods with counts
    - Star ratings
    - Property types and themes
    - Price ranges
    """
    try:
        logger.info("Fetching available filter options")
        return service.get_filter_options(db)
    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get filter options: {str(e)}")


@router.get("/amenities", response_model=List[HotelSearchResult], tags=["Hotel Search Filters"])
def search_hotels_by_amenities(
    amenities: List[str] = Query(..., description="List of amenity names"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db),
    service: SearchFiltersService = Depends(get_search_filters_service)
):
    """
    Search hotels by specific amenities
    
    Returns hotels that have ALL specified amenities
    """
    try:
        logger.info(f"Searching hotels by amenities: {amenities}")
        return service.search_hotels_by_amenities(db, amenities, limit)
    except Exception as e:
        logger.error(f"Error searching hotels by amenities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/rating", response_model=List[HotelSearchResult], tags=["Hotel Search Filters"])
def search_hotels_by_rating(
    min_rating: float = Query(..., ge=0, le=10, description="Minimum rating threshold"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db),
    service: SearchFiltersService = Depends(get_search_filters_service)
):
    """
    Search hotels by minimum guest rating
    
    Returns hotels with rating >= min_rating
    """
    try:
        logger.info(f"Searching hotels by minimum rating: {min_rating}")
        return service.search_hotels_by_rating(db, min_rating, limit)
    except Exception as e:
        logger.error(f"Error searching hotels by rating: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/location", response_model=List[HotelSearchResult], tags=["Hotel Search Filters"])
def search_hotels_by_location(
    location: str = Query(..., description="Location or neighborhood name"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db),
    service: SearchFiltersService = Depends(get_search_filters_service)
):
    """
    Search hotels by location/neighborhood
    
    Returns hotels in the specified location
    """
    try:
        logger.info(f"Searching hotels by location: {location}")
        return service.search_hotels_by_location(db, location, limit)
    except Exception as e:
        logger.error(f"Error searching hotels by location: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats", tags=["Hotel Search Filters"])
def get_filter_stats(
    filters: Optional[HotelFilters] = None,
    db: Session = Depends(get_db),
    service: SearchFiltersService = Depends(get_search_filters_service)
):
    """
    Get statistics for filtered results
    
    Returns:
    - Total hotels in database
    - Filtered hotels count
    - Available amenities count
    - Available neighborhoods count
    - Average rating
    - Average price (if available)
    """
    try:
        logger.info("Fetching filter statistics")
        return service.get_filter_stats(db, filters)
    except Exception as e:
        logger.error(f"Error getting filter stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/sort-options", tags=["Hotel Search Filters"])
def get_sort_options():
    """
    Get available sorting options
    
    Returns all available sorting criteria
    """
    return {
        "sort_options": {
            "recommended": "Recommended (default)",
            "price_low_to_high": "Price: Low to High",
            "price_high_to_low": "Price: High to Low",
            "rating": "Guest Rating (High to Low)",
            "star_rating": "Star Rating (High to Low)",
            "name_asc": "Name: A to Z",
            "name_desc": "Name: Z to A"
        }
    }


@router.get("/quick-search", response_model=List[HotelSearchResult], tags=["Hotel Search Filters"])
def quick_search_hotels(
    query: str = Query(..., description="Search query (name, location, or amenity)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db),
    service: SearchFiltersService = Depends(get_search_filters_service)
):
    """
    Quick search hotels by name, location, or amenity
    
    Searches across hotel names, locations, and amenities
    """
    try:
        logger.info(f"Quick search for: {query}")
        
        # Create filters for quick search
        filters = HotelFilters(propertyName=query)
        pagination = {"page": 1, "limit": limit}
        
        # Search by name first
        name_results = service.search_hotels_filtered(db, HotelFilterRequest(
            locationId="",  # Not needed for quick search
            checkInDate="2025-01-01",  # Dummy date
            checkOutDate="2025-01-02",  # Dummy date
            occupancies=[],  # Not needed for quick search
            filters=filters,
            pagination=pagination
        ))
        
        # If no results by name, try by location
        if not name_results.hotels:
            filters = HotelFilters(neighborhoods=[query])
            location_results = service.search_hotels_filtered(db, HotelFilterRequest(
                locationId="",
                checkInDate="2025-01-01",
                checkOutDate="2025-01-02",
                occupancies=[],
                filters=filters,
                pagination=pagination
            ))
            return location_results.hotels
        
        return name_results.hotels
        
    except Exception as e:
        logger.error(f"Error in quick search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick search failed: {str(e)}")
