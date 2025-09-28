"""
Hotel Filter Controller
Provides endpoints for filtering hotels based on various criteria
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.db import get_db
from app.models.hotel_entities import Hotel, HotelAmenity, Room

router = APIRouter()

# Pydantic models for filter requests
class HotelFilterRequest(BaseModel):
    city: str = None
    state: str = None
    country: str = None
    star_rating: List[int] = None  # [3, 4, 5]
    amenities: List[str] = None  # ["wifi", "pool", "gym"]
    min_price: float = None
    max_price: float = None
    min_rating: float = None
    max_rating: float = None
    page: int = 1
    limit: int = 20

class HotelFilterResponse(BaseModel):
    hotels: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int
    total_pages: int

@router.post("/filter", response_model=HotelFilterResponse, tags=["Hotel Filtering"])
async def filter_hotels(
    request: HotelFilterRequest,
    db: Session = Depends(get_db)
):
    """
    Filter hotels based on various criteria
    
    Supports filtering by:
    - Location (city, state, country)
    - Star rating
    - Amenities
    - Price range (based on room rates)
    - Rating range
    - Pagination
    """
    try:
        # Start with base query
        query = db.query(Hotel)
        
        # Apply location filters
        if request.city:
            query = query.filter(Hotel.city.ilike(f"%{request.city}%"))
        if request.state:
            query = query.filter(Hotel.state.ilike(f"%{request.state}%"))
        if request.country:
            query = query.filter(Hotel.country.ilike(f"%{request.country}%"))
        
        # Apply star rating filter
        if request.star_rating:
            query = query.filter(Hotel.star_rating.in_(request.star_rating))
        
        # Apply rating range filter
        if request.min_rating is not None:
            query = query.filter(Hotel.avg_rating >= request.min_rating)
        if request.max_rating is not None:
            query = query.filter(Hotel.avg_rating <= request.max_rating)
        
        # Apply amenities filter
        if request.amenities:
            # Get hotel IDs that have all required amenities
            amenity_subquery = db.query(HotelAmenity.hotel_id).filter(
                HotelAmenity.amenity_name.in_(request.amenities)
            ).group_by(HotelAmenity.hotel_id).having(
                func.count(HotelAmenity.amenity_name) == len(request.amenities)
            ).subquery()
            
            query = query.filter(Hotel.id.in_(amenity_subquery))
        
        # Apply price range filter (based on room rates)
        if request.min_price is not None or request.max_price is not None:
            room_subquery = db.query(Room.hotel_id)
            
            if request.min_price is not None:
                room_subquery = room_subquery.filter(Room.base_rate >= request.min_price)
            if request.max_price is not None:
                room_subquery = room_subquery.filter(Room.base_rate <= request.max_price)
            
            query = query.filter(Hotel.id.in_(room_subquery))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (request.page - 1) * request.limit
        hotels = query.offset(offset).limit(request.limit).all()
        
        # Format response
        hotel_list = []
        for hotel in hotels:
            # Get hotel amenities
            amenities = [amenity.amenity_name for amenity in hotel.amenities]
            
            # Get room pricing info
            rooms = hotel.rooms
            min_price = None
            max_price = None
            if rooms:
                prices = [room.base_rate for room in rooms if room.base_rate is not None]
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
            
            hotel_data = {
                "id": hotel.id,
                "api_hotel_id": hotel.api_hotel_id,
                "name": hotel.name,
                "description": hotel.description,
                "address": hotel.address,
                "city": hotel.city,
                "state": hotel.state,
                "country": hotel.country,
                "postal_code": hotel.postal_code,
                "latitude": hotel.latitude,
                "longitude": hotel.longitude,
                "phone": hotel.phone,
                "email": hotel.email,
                "website": hotel.website,
                "star_rating": hotel.star_rating,
                "avg_rating": hotel.avg_rating,
                "total_reviews": hotel.total_reviews,
                "amenities": amenities,
                "min_price": min_price,
                "max_price": max_price,
                "rooms_count": len(rooms),
                "created_at": hotel.created_at.isoformat() if hotel.created_at else None,
                "updated_at": hotel.updated_at.isoformat() if hotel.updated_at else None
            }
            hotel_list.append(hotel_data)
        
        total_pages = (total_count + request.limit - 1) // request.limit
        
        return HotelFilterResponse(
            hotels=hotel_list,
            total_count=total_count,
            page=request.page,
            limit=request.limit,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering hotels: {str(e)}")

@router.get("/filter-options", tags=["Hotel Filtering"])
async def get_filter_options(db: Session = Depends(get_db)):
    """
    Get available filter options for the hotel search
    
    Returns lists of available:
    - Cities
    - Star ratings
    - Amenities
    - Price ranges
    - Rating ranges
    """
    try:
        # Get unique cities
        cities = db.query(Hotel.city, Hotel.state, Hotel.country).distinct().all()
        city_list = [{"city": c[0], "state": c[1], "country": c[2]} for c in cities if c[0]]
        
        # Get unique star ratings
        star_ratings = db.query(Hotel.star_rating).distinct().all()
        star_rating_list = sorted([s[0] for s in star_ratings if s[0] is not None])
        
        # Get unique amenities
        amenities = db.query(HotelAmenity.amenity_name).distinct().all()
        amenity_list = sorted([a[0] for a in amenities if a[0]])
        
        # Get price range
        price_stats = db.query(
            func.min(Room.base_rate).label('min_price'),
            func.max(Room.base_rate).label('max_price')
        ).filter(Room.base_rate.isnot(None)).first()
        
        min_price = price_stats.min_price if price_stats else 0
        max_price = price_stats.max_price if price_stats else 1000
        
        # Get rating range
        rating_stats = db.query(
            func.min(Hotel.avg_rating).label('min_rating'),
            func.max(Hotel.avg_rating).label('max_rating')
        ).filter(Hotel.avg_rating.isnot(None)).first()
        
        min_rating = rating_stats.min_rating if rating_stats else 0
        max_rating = rating_stats.max_rating if rating_stats else 5
        
        return {
            "cities": city_list,
            "star_ratings": star_rating_list,
            "amenities": amenity_list,
            "price_range": {
                "min": min_price,
                "max": max_price
            },
            "rating_range": {
                "min": min_rating,
                "max": max_rating
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting filter options: {str(e)}")

@router.get("/amenities", tags=["Hotel Filtering"])
async def get_amenities(
    amenity_type: str = Query(None, description="Filter by amenity type"),
    db: Session = Depends(get_db)
):
    """
    Get list of available amenities
    
    Args:
        amenity_type: Optional filter by amenity type (e.g., 'general', 'room', 'hotel')
    """
    try:
        query = db.query(HotelAmenity.amenity_name, HotelAmenity.amenity_type).distinct()
        
        if amenity_type:
            query = query.filter(HotelAmenity.amenity_type == amenity_type)
        
        amenities = query.all()
        
        amenity_list = [
            {
                "name": a[0],
                "type": a[1]
            }
            for a in amenities
        ]
        
        return {
            "amenities": amenity_list,
            "count": len(amenity_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting amenities: {str(e)}")

@router.get("/cities", tags=["Hotel Filtering"])
async def get_cities(
    country: str = Query(None, description="Filter by country"),
    state: str = Query(None, description="Filter by state"),
    db: Session = Depends(get_db)
):
    """
    Get list of available cities
    
    Args:
        country: Optional filter by country
        state: Optional filter by state
    """
    try:
        query = db.query(Hotel.city, Hotel.state, Hotel.country).distinct()
        
        if country:
            query = query.filter(Hotel.country.ilike(f"%{country}%"))
        if state:
            query = query.filter(Hotel.state.ilike(f"%{state}%"))
        
        cities = query.all()
        
        city_list = [
            {
                "city": c[0],
                "state": c[1],
                "country": c[2]
            }
            for c in cities if c[0]
        ]
        
        return {
            "cities": city_list,
            "count": len(city_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cities: {str(e)}")
