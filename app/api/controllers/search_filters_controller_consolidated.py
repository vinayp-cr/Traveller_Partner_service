#!/usr/bin/env python3
"""
Consolidated Search Filters Controller
Single API endpoint for all hotel search filtering functionality with minimal payload
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.core.db import get_db
from app.core.logger import logger
from app.api.services.search_filters_controller_consolidated_service import ConsolidatedSearchService

router = APIRouter(prefix="/api/hotel/search", tags=["Consolidated Hotel Search"])


class ConsolidatedSearchRequest(BaseModel):
    """Consolidated search request with minimal payload"""
    
    # Search type (required - determines which search method to use)
    search_type: str = Field(..., description="Type of search: comprehensive, quick, amenities, rating, location, options, stats, sort_options")
    
    # Basic search parameters (optional)
    query: Optional[str] = Field(None, description="Search query (name, location, or amenity)")
    location: Optional[str] = Field(None, description="Location or neighborhood name")
    
    # Filter parameters (all optional)
    amenities: Optional[List[str]] = Field(None, description="List of amenity names")
    min_rating: Optional[float] = Field(None, ge=0, le=10, description="Minimum guest rating")
    star_ratings: Optional[List[int]] = Field(None, description="Star ratings to filter by")
    property_name: Optional[str] = Field(None, description="Property name search")
    neighborhoods: Optional[List[str]] = Field(None, description="Neighborhoods to filter by")
    property_types: Optional[List[str]] = Field(None, description="Property types")
    property_themes: Optional[List[str]] = Field(None, description="Property themes")
    nearby_attractions: Optional[List[str]] = Field(None, description="Nearby attractions")
    
    # Budget filter
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    
    # Sorting and pagination
    sort_by: Optional[str] = Field("recommended", description="Sort criteria")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Maximum number of results")
    
    model_config = {
        "extra": "ignore"
    }
    
    def model_dump_json(self, **kwargs) -> str:
        """Custom JSON serialization that excludes None values for minimal payloads"""
        # Use the minimal data method
        data = self.model_dump_minimal()
        
        # Convert to JSON
        import json
        return json.dumps(data, **kwargs)
    
    def model_dump_minimal(self) -> dict:
        """Get minimal model data excluding None values and defaults"""
        data = self.model_dump(exclude_none=True)
        
        # Always include search_type (required)
        result = {"search_type": data["search_type"]}
        
        # Add non-default fields
        for key, value in data.items():
            if key == "search_type":
                continue
            elif key == "sort_by" and value != "recommended":
                result[key] = value
            elif key == "limit" and value != 20:
                result[key] = value
            elif key not in ["sort_by", "limit"]:
                result[key] = value
        
        return result


class ConsolidatedSearchResponse(BaseModel):
    """Consolidated search response"""
    
    # Search results
    hotels: List[Dict[str, Any]] = Field(default_factory=list, description="Hotel search results")
    
    # Filter options (when search_type is 'options')
    filter_options: Optional[Dict[str, Any]] = Field(None, description="Available filter options")
    
    # Statistics (when search_type is 'stats')
    stats: Optional[Dict[str, Any]] = Field(None, description="Search statistics")
    
    # Sort options (when search_type is 'sort_options')
    sort_options: Optional[Dict[str, str]] = Field(None, description="Available sorting options")
    
    # Metadata
    total_results: int = Field(0, description="Total number of results")
    search_type: str = Field(..., description="Type of search performed")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters that were applied")


def get_consolidated_search_service() -> ConsolidatedSearchService:
    """Dependency injection for ConsolidatedSearchService"""
    return ConsolidatedSearchService()


@router.post("/consolidated", response_model=ConsolidatedSearchResponse, tags=["Consolidated Hotel Search"])
def consolidated_hotel_search(
    request: ConsolidatedSearchRequest,
    db: Session = Depends(get_db),
    service: ConsolidatedSearchService = Depends(get_consolidated_search_service)
):
    """
    Consolidated hotel search endpoint with minimal payload
    
    This single endpoint handles all search functionality:
    
    **Search Types:**
    - `comprehensive`: Full filtered search with all parameters
    - `quick`: Quick search by name, location, or amenity
    - `amenities`: Search by specific amenities
    - `rating`: Search by minimum rating
    - `location`: Search by location/neighborhood
    - `options`: Get available filter options
    - `stats`: Get search statistics
    - `sort_options`: Get available sorting options
    
    **Minimal Payload Examples:**
    
    Quick search:
    ```json
    {
        "query": "luxury hotel",
        "search_type": "quick",
        "limit": 10
    }
    ```
    
    Filter by amenities:
    ```json
    {
        "amenities": ["wifi", "pool", "gym"],
        "search_type": "amenities",
        "limit": 20
    }
    ```
    
    Filter by rating:
    ```json
    {
        "min_rating": 4.5,
        "search_type": "rating",
        "limit": 15
    }
    ```
    
    Comprehensive search:
    ```json
    {
        "location": "New York",
        "amenities": ["wifi", "pool"],
        "min_rating": 4.0,
        "star_ratings": [4, 5],
        "max_price": 300,
        "search_type": "comprehensive",
        "sort_by": "rating",
        "limit": 25
    }
    ```
    
    Get filter options:
    ```json
    {
        "search_type": "options"
    }
    ```
    """
    try:
        logger.info(f"Processing consolidated search request - Type: {request.search_type}")
        
        # Initialize response
        response = ConsolidatedSearchResponse(
            search_type=request.search_type,
            filters_applied={}
        )
        
        # Route to appropriate search method based on search_type
        if request.search_type == "options":
            return _handle_filter_options(db, service, response)
        elif request.search_type == "stats":
            return _handle_filter_stats(db, service, request, response)
        elif request.search_type == "sort_options":
            return _handle_sort_options(response)
        elif request.search_type == "quick":
            return _handle_quick_search(db, service, request, response)
        elif request.search_type == "amenities":
            return _handle_amenities_search(db, service, request, response)
        elif request.search_type == "rating":
            return _handle_rating_search(db, service, request, response)
        elif request.search_type == "location":
            return _handle_location_search(db, service, request, response)
        elif request.search_type == "comprehensive":
            return _handle_comprehensive_search(db, service, request, response)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid search_type: {request.search_type}")
            
    except Exception as e:
        logger.error(f"Error in consolidated search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def _handle_filter_options(db: Session, service: ConsolidatedSearchService, response: ConsolidatedSearchResponse) -> ConsolidatedSearchResponse:
    """Handle filter options request"""
    try:
        filter_options = service.get_filter_options(db)
        response.filter_options = filter_options
        response.total_results = len(filter_options.get("available_amenities", []))
        return response
    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get filter options: {str(e)}")


def _handle_filter_stats(db: Session, service: ConsolidatedSearchService, request: ConsolidatedSearchRequest, response: ConsolidatedSearchResponse) -> ConsolidatedSearchResponse:
    """Handle filter statistics request"""
    try:
        # Create filters dict if any filters are provided
        filters = {}
        if request.amenities:
            filters['amenities'] = request.amenities
        if request.min_rating is not None:
            filters['min_rating'] = request.min_rating
        if request.star_ratings:
            filters['star_ratings'] = request.star_ratings
        if request.property_name:
            filters['property_name'] = request.property_name
        if request.neighborhoods:
            filters['neighborhoods'] = request.neighborhoods
        if request.property_types:
            filters['property_types'] = request.property_types
        if request.property_themes:
            filters['property_themes'] = request.property_themes
        if request.nearby_attractions:
            filters['nearby_attractions'] = request.nearby_attractions
        if request.max_price is not None:
            filters['max_price'] = request.max_price
        
        stats = service.get_search_stats(db, filters if filters else None)
        response.stats = stats
        response.filters_applied = filters
        return response
    except Exception as e:
        logger.error(f"Error getting filter stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


def _handle_sort_options(db: Session, service: ConsolidatedSearchService, response: ConsolidatedSearchResponse) -> ConsolidatedSearchResponse:
    """Handle sort options request"""
    response.sort_options = service.get_sort_options()
    response.total_results = len(response.sort_options)
    return response


def _handle_quick_search(db: Session, service: ConsolidatedSearchService, request: ConsolidatedSearchRequest, response: ConsolidatedSearchResponse) -> ConsolidatedSearchResponse:
    """Handle quick search request"""
    if not request.query:
        raise HTTPException(status_code=400, detail="Query parameter is required for quick search")
    
    try:
        hotels = service.search_hotels_quick(db, request.query, request.limit or 10)
        response.hotels = hotels
        response.total_results = len(hotels)
        response.filters_applied = {"query": request.query}
        return response
    except Exception as e:
        logger.error(f"Error in quick search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick search failed: {str(e)}")


def _handle_amenities_search(db: Session, service: ConsolidatedSearchService, request: ConsolidatedSearchRequest, response: ConsolidatedSearchResponse) -> ConsolidatedSearchResponse:
    """Handle amenities search request"""
    if not request.amenities:
        raise HTTPException(status_code=400, detail="Amenities parameter is required for amenities search")
    
    try:
        hotels = service.search_hotels_by_amenities(db, request.amenities, request.limit or 10)
        response.hotels = hotels
        response.total_results = len(hotels)
        response.filters_applied = {"amenities": request.amenities}
        return response
    except Exception as e:
        logger.error(f"Error searching hotels by amenities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def _handle_rating_search(db: Session, service: ConsolidatedSearchService, request: ConsolidatedSearchRequest, response: ConsolidatedSearchResponse) -> ConsolidatedSearchResponse:
    """Handle rating search request"""
    if request.min_rating is None:
        raise HTTPException(status_code=400, detail="min_rating parameter is required for rating search")
    
    try:
        hotels = service.search_hotels_by_rating(db, request.min_rating, request.limit or 10)
        response.hotels = hotels
        response.total_results = len(hotels)
        response.filters_applied = {"min_rating": request.min_rating}
        return response
    except Exception as e:
        logger.error(f"Error searching hotels by rating: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def _handle_location_search(db: Session, service: ConsolidatedSearchService, request: ConsolidatedSearchRequest, response: ConsolidatedSearchResponse) -> ConsolidatedSearchResponse:
    """Handle location search request"""
    if not request.location:
        raise HTTPException(status_code=400, detail="Location parameter is required for location search")
    
    try:
        hotels = service.search_hotels_by_location(db, request.location, request.limit or 10)
        response.hotels = hotels
        response.total_results = len(hotels)
        response.filters_applied = {"location": request.location}
        return response
    except Exception as e:
        logger.error(f"Error searching hotels by location: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def _handle_comprehensive_search(db: Session, service: ConsolidatedSearchService, request: ConsolidatedSearchRequest, response: ConsolidatedSearchResponse) -> ConsolidatedSearchResponse:
    """Handle comprehensive search request"""
    try:
        # Create filters dict with only provided parameters
        filters = {}
        if request.sort_by:
            filters["sort_by"] = request.sort_by
        if request.amenities:
            filters["amenities"] = request.amenities
        if request.min_rating is not None:
            filters["min_rating"] = request.min_rating
        if request.star_ratings:
            filters["star_ratings"] = request.star_ratings
        if request.property_name:
            filters["property_name"] = request.property_name
        if request.neighborhoods:
            filters["neighborhoods"] = request.neighborhoods
        if request.property_types:
            filters["property_types"] = request.property_types
        if request.property_themes:
            filters["property_themes"] = request.property_themes
        if request.nearby_attractions:
            filters["nearby_attractions"] = request.nearby_attractions
        if request.max_price is not None:
            filters["max_price"] = request.max_price
        if request.location:
            filters["location"] = request.location
        
        # Perform search
        hotels = service.search_hotels_comprehensive(db, filters, request.limit or 20)
        response.hotels = hotels
        response.total_results = len(hotels)
        response.filters_applied = filters
        return response
    except Exception as e:
        logger.error(f"Error in comprehensive search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comprehensive search failed: {str(e)}")


# Additional convenience endpoints for backward compatibility
@router.get("/quick", response_model=ConsolidatedSearchResponse, tags=["Consolidated Hotel Search"])
def quick_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db),
    service: ConsolidatedSearchService = Depends(get_consolidated_search_service)
):
    """Quick search convenience endpoint"""
    request = ConsolidatedSearchRequest(
        query=query,
        search_type="quick",
        limit=limit
    )
    return consolidated_hotel_search(request, db, service)


@router.get("/amenities", response_model=ConsolidatedSearchResponse, tags=["Consolidated Hotel Search"])
def search_by_amenities(
    amenities: List[str] = Query(..., description="List of amenity names"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db),
    service: ConsolidatedSearchService = Depends(get_consolidated_search_service)
):
    """Search by amenities convenience endpoint"""
    request = ConsolidatedSearchRequest(
        amenities=amenities,
        search_type="amenities",
        limit=limit
    )
    return consolidated_hotel_search(request, db, service)


@router.get("/rating", response_model=ConsolidatedSearchResponse, tags=["Consolidated Hotel Search"])
def search_by_rating(
    min_rating: float = Query(..., ge=0, le=10, description="Minimum rating"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db),
    service: ConsolidatedSearchService = Depends(get_consolidated_search_service)
):
    """Search by rating convenience endpoint"""
    request = ConsolidatedSearchRequest(
        min_rating=min_rating,
        search_type="rating",
        limit=limit
    )
    return consolidated_hotel_search(request, db, service)


@router.get("/location", response_model=ConsolidatedSearchResponse, tags=["Consolidated Hotel Search"])
def search_by_location(
    location: str = Query(..., description="Location name"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db),
    service: ConsolidatedSearchService = Depends(get_consolidated_search_service)
):
    """Search by location convenience endpoint"""
    request = ConsolidatedSearchRequest(
        location=location,
        search_type="location",
        limit=limit
    )
    return consolidated_hotel_search(request, db, service)


@router.get("/options", response_model=ConsolidatedSearchResponse, tags=["Consolidated Hotel Search"])
def get_options(
    db: Session = Depends(get_db),
    service: ConsolidatedSearchService = Depends(get_consolidated_search_service)
):
    """Get filter options convenience endpoint"""
    request = ConsolidatedSearchRequest(search_type="options")
    return consolidated_hotel_search(request, db, service)


@router.get("/stats", response_model=ConsolidatedSearchResponse, tags=["Consolidated Hotel Search"])
def get_stats(
    amenities: Optional[List[str]] = Query(None, description="Filter by amenities"),
    min_rating: Optional[float] = Query(None, ge=0, le=10, description="Filter by minimum rating"),
    star_ratings: Optional[List[int]] = Query(None, description="Filter by star ratings"),
    db: Session = Depends(get_db),
    service: ConsolidatedSearchService = Depends(get_consolidated_search_service)
):
    """Get search statistics convenience endpoint"""
    request = ConsolidatedSearchRequest(
        amenities=amenities,
        min_rating=min_rating,
        star_ratings=star_ratings,
        search_type="stats"
    )
    return consolidated_hotel_search(request, db, service)
