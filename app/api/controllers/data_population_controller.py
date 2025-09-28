"""
Data Population Controller
Provides endpoints for populating hotel data for filtering functionality
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from app.core.db import get_db
from app.api.services.data_population_service import DataPopulationService
from app.api.services.hotel_service import HotelService

router = APIRouter()

# Pydantic models for requests
class CityPopulationRequest(BaseModel):
    city: str
    state: str = None
    country: str = "US"
    lat: float = None
    lng: float = None
    max_hotels: int = 50

class MultiCityPopulationRequest(BaseModel):
    cities: List[CityPopulationRequest]

# Dependency to get data population service
def get_data_population_service() -> DataPopulationService:
    hotel_service = HotelService()
    return DataPopulationService(hotel_service)

@router.post("/populate-city", tags=["Data Population"])
async def populate_city(
    request: CityPopulationRequest,
    db: Session = Depends(get_db),
    service: DataPopulationService = Depends(get_data_population_service)
):
    """
    Populate hotel data for a specific city
    
    This endpoint will:
    1. Search for hotels in the specified city
    2. Save hotel details, amenities, and images
    3. Return population statistics
    """
    try:
        result = await service.populate_hotels_for_city(
            db=db,
            city=request.city,
            state=request.state,
            country=request.country,
            lat=request.lat,
            lng=request.lng,
            max_hotels=request.max_hotels
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error populating city: {str(e)}")

@router.post("/populate-multiple-cities", tags=["Data Population"])
async def populate_multiple_cities(
    request: MultiCityPopulationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    service: DataPopulationService = Depends(get_data_population_service)
):
    """
    Populate hotel data for multiple cities
    
    This endpoint will process multiple cities and populate hotel data for each.
    For large datasets, consider running this as a background task.
    """
    try:
        # Convert to the format expected by the service
        cities_data = []
        for city in request.cities:
            cities_data.append({
                "city": city.city,
                "state": city.state,
                "country": city.country,
                "lat": city.lat,
                "lng": city.lng,
                "max_hotels": city.max_hotels
            })
        
        result = await service.populate_multiple_cities(db=db, cities=cities_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error populating cities: {str(e)}")

@router.get("/population-stats", tags=["Data Population"])
async def get_population_stats(
    db: Session = Depends(get_db),
    service: DataPopulationService = Depends(get_data_population_service)
):
    """
    Get current database population statistics
    
    Returns counts of hotels, rooms, amenities, images, and other useful statistics
    for monitoring data population progress.
    """
    try:
        result = await service.get_population_stats(db=db)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting population stats: {str(e)}")

@router.post("/populate-popular-cities", tags=["Data Population"])
async def populate_popular_cities(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    service: DataPopulationService = Depends(get_data_population_service)
):
    """
    Populate hotel data for popular US cities
    
    This is a convenience endpoint that populates data for major US cities
    commonly searched for hotel bookings.
    """
    try:
        # Popular US cities for hotel searches with coordinates
        popular_cities = [
            {"city": "New York", "state": "NY", "country": "US", "lat": 40.7128, "lng": -74.0060, "max_hotels": 100},
            {"city": "Los Angeles", "state": "CA", "country": "US", "lat": 34.0522, "lng": -118.2437, "max_hotels": 100},
            {"city": "Chicago", "state": "IL", "country": "US", "lat": 41.8781, "lng": -87.6298, "max_hotels": 80},
            {"city": "Miami", "state": "FL", "country": "US", "lat": 25.7617, "lng": -80.1918, "max_hotels": 80},
            {"city": "Las Vegas", "state": "NV", "country": "US", "lat": 36.1699, "lng": -115.1398, "max_hotels": 100},
            {"city": "San Francisco", "state": "CA", "country": "US", "lat": 37.7749, "lng": -122.4194, "max_hotels": 80},
            {"city": "Boston", "state": "MA", "country": "US", "lat": 42.3601, "lng": -71.0589, "max_hotels": 60},
            {"city": "Seattle", "state": "WA", "country": "US", "lat": 47.6062, "lng": -122.3321, "max_hotels": 60},
            {"city": "Orlando", "state": "FL", "country": "US", "lat": 28.5383, "lng": -81.3792, "max_hotels": 100},
            {"city": "Atlanta", "state": "GA", "country": "US", "lat": 33.7490, "lng": -84.3880, "max_hotels": 60}
        ]
        
        result = await service.populate_multiple_cities(db=db, cities=popular_cities)
        
        return {
            "message": "Popular cities population initiated",
            "cities_count": len(popular_cities),
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error populating popular cities: {str(e)}")
