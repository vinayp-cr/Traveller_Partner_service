from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.logger import logger
from app.api.repositories.hotel_repository import HotelRepository
from app.models.hotel_entities import Hotel, HotelAmenity, HotelImage
from sqlalchemy import func, distinct, and_
from typing import List, Dict, Any, Optional
import traceback

router = APIRouter(prefix="/api/filters")

class FilterDataController:
    """Controller for providing filter data from database"""
    
    def __init__(self):
        self.repository = HotelRepository()
    
    async def get_all_filters(self, db: Session) -> Dict[str, Any]:
        """
        Get all available filter data from database
        
        Args:
            db: Database session
            
        Returns:
            Dictionary containing all filter options
        """
        try:
            logger.info("Fetching all filter data from database")
            
            # Get all filter data in parallel
            amenities = await self._get_amenities_filter(db)
            star_ratings = await self._get_star_ratings_filter(db)
            neighborhoods = await self._get_neighborhoods_filter(db)
            rate_ranges = await self._get_rate_ranges_filter(db)
            countries = await self._get_countries_filter(db)
            cities = await self._get_cities_filter(db)
            
            # Get popular amenities (top 20)
            popular_amenities = amenities[:20] if len(amenities) > 20 else amenities
            
            # Get popular neighborhoods (top 20)
            popular_neighborhoods = neighborhoods[:20] if len(neighborhoods) > 20 else neighborhoods
            
            filter_data = {
                "amenities": {
                    "all": amenities,
                    "popular": popular_amenities,
                    "total": len(amenities)
                },
                "star_ratings": {
                    "all": star_ratings,
                    "total": len(star_ratings)
                },
                "neighborhoods": {
                    "all": neighborhoods,
                    "popular": popular_neighborhoods,
                    "total": len(neighborhoods)
                },
                "rate_ranges": {
                    "all": rate_ranges,
                    "total": len(rate_ranges)
                },
                "countries": {
                    "all": countries,
                    "total": len(countries)
                },
                "cities": {
                    "all": cities,
                    "total": len(cities)
                },
                "summary": {
                    "total_hotels": await self._get_total_hotels_count(db),
                    "total_amenities": len(amenities),
                    "total_locations": len(neighborhoods),
                    "total_countries": len(countries),
                    "total_cities": len(cities)
                }
            }
            
            logger.info(f"Successfully fetched filter data: {len(amenities)} amenities, {len(star_ratings)} star ratings, {len(neighborhoods)} neighborhoods")
            return filter_data
            
        except Exception as e:
            error_msg = f"Error fetching filter data: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=error_msg)
    
    async def _get_amenities_filter(self, db: Session) -> List[Dict[str, Any]]:
        """Get all unique amenities with counts"""
        try:
            # Get amenities with counts
            amenities_query = db.query(
                HotelAmenity.amenity_name,
                HotelAmenity.amenity_type,
                func.count(HotelAmenity.hotel_id).label('count')
            ).group_by(
                HotelAmenity.amenity_name, 
                HotelAmenity.amenity_type
            ).order_by(
                func.count(HotelAmenity.hotel_id).desc(),
                HotelAmenity.amenity_name
            ).all()
            
            amenities = []
            for amenity in amenities_query:
                amenities.append({
                    "name": amenity.amenity_name,
                    "type": amenity.amenity_type,
                    "count": amenity.count,
                    "display_name": amenity.amenity_name.replace('_', ' ').title()
                })
            
            return amenities
            
        except Exception as e:
            logger.error(f"Error fetching amenities: {str(e)}")
            return []
    
    async def _get_star_ratings_filter(self, db: Session) -> List[Dict[str, Any]]:
        """Get all unique star ratings with counts"""
        try:
            # Get star ratings with counts
            ratings_query = db.query(
                Hotel.star_rating,
                func.count(Hotel.id).label('count')
            ).filter(
                Hotel.star_rating.isnot(None),
                Hotel.star_rating > 0
            ).group_by(
                Hotel.star_rating
            ).order_by(
                Hotel.star_rating
            ).all()
            
            star_ratings = []
            for rating in ratings_query:
                star_ratings.append({
                    "rating": int(rating.star_rating),
                    "count": rating.count,
                    "display_name": f"{int(rating.star_rating)} Star"
                })
            
            return star_ratings
            
        except Exception as e:
            logger.error(f"Error fetching star ratings: {str(e)}")
            return []
    
    async def _get_neighborhoods_filter(self, db: Session) -> List[Dict[str, Any]]:
        """Get all unique neighborhoods/locations with counts"""
        try:
            # Get neighborhoods with counts
            neighborhoods_query = db.query(
                Hotel.city,
                Hotel.state,
                Hotel.country,
                func.count(Hotel.id).label('count')
            ).filter(
                Hotel.city.isnot(None),
                Hotel.city != ''
            ).group_by(
                Hotel.city, Hotel.state, Hotel.country
            ).order_by(
                func.count(Hotel.id).desc(),
                Hotel.city
            ).all()
            
            neighborhoods = []
            for neighborhood in neighborhoods_query:
                location_name = f"{neighborhood.city}"
                if neighborhood.state:
                    location_name += f", {neighborhood.state}"
                if neighborhood.country:
                    location_name += f", {neighborhood.country}"
                
                neighborhoods.append({
                    "city": neighborhood.city,
                    "state": neighborhood.state,
                    "country": neighborhood.country,
                    "display_name": location_name,
                    "count": neighborhood.count
                })
            
            return neighborhoods
            
        except Exception as e:
            logger.error(f"Error fetching neighborhoods: {str(e)}")
            return []
    
    async def _get_rate_ranges_filter(self, db: Session) -> List[Dict[str, Any]]:
        """Get rate ranges based on hotel data"""
        try:
            # Get actual rate data from hotels if available
            # This assumes you have rate information in your hotel data
            # You might need to adjust based on your actual data structure
            
            # Try to get rate statistics from hotel data
            rate_stats = db.query(
                func.min(Hotel.avg_rating).label('min_rate'),
                func.max(Hotel.avg_rating).label('max_rate'),
                func.avg(Hotel.avg_rating).label('avg_rate')
            ).filter(
                Hotel.avg_rating.isnot(None),
                Hotel.avg_rating > 0
            ).first()
            
            if rate_stats and rate_stats.min_rate and rate_stats.max_rate:
                min_rate = float(rate_stats.min_rate)
                max_rate = float(rate_stats.max_rate)
                avg_rate = float(rate_stats.avg_rate) if rate_stats.avg_rate else (min_rate + max_rate) / 2
                
                # Create dynamic rate ranges based on actual data
                rate_ranges = []
                
                # Budget range (0 to 25% of average)
                budget_max = avg_rate * 0.25
                rate_ranges.append({
                    "min": 0,
                    "max": budget_max,
                    "display_name": f"Budget ($0-${budget_max:.0f})",
                    "count": 0
                })
                
                # Economy range (25% to 50% of average)
                economy_min = budget_max
                economy_max = avg_rate * 0.5
                rate_ranges.append({
                    "min": economy_min,
                    "max": economy_max,
                    "display_name": f"Economy (${economy_min:.0f}-${economy_max:.0f})",
                    "count": 0
                })
                
                # Mid-range (50% to 100% of average)
                mid_min = economy_max
                mid_max = avg_rate
                rate_ranges.append({
                    "min": mid_min,
                    "max": mid_max,
                    "display_name": f"Mid-range (${mid_min:.0f}-${mid_max:.0f})",
                    "count": 0
                })
                
                # Upscale (100% to 150% of average)
                upscale_min = mid_max
                upscale_max = avg_rate * 1.5
                rate_ranges.append({
                    "min": upscale_min,
                    "max": upscale_max,
                    "display_name": f"Upscale (${upscale_min:.0f}-${upscale_max:.0f})",
                    "count": 0
                })
                
                # Luxury (150% to 200% of average)
                luxury_min = upscale_max
                luxury_max = avg_rate * 2.0
                rate_ranges.append({
                    "min": luxury_min,
                    "max": luxury_max,
                    "display_name": f"Luxury (${luxury_min:.0f}-${luxury_max:.0f})",
                    "count": 0
                })
                
                # Premium (200%+ of average)
                rate_ranges.append({
                    "min": luxury_max,
                    "max": None,
                    "display_name": f"Premium (${luxury_max:.0f}+)",
                    "count": 0
                })
            else:
                # Fallback to standard ranges if no rate data available
                rate_ranges = [
                    {"min": 0, "max": 50, "display_name": "Budget ($0-$50)", "count": 0},
                    {"min": 50, "max": 100, "display_name": "Economy ($50-$100)", "count": 0},
                    {"min": 100, "max": 200, "display_name": "Mid-range ($100-$200)", "count": 0},
                    {"min": 200, "max": 300, "display_name": "Upscale ($200-$300)", "count": 0},
                    {"min": 300, "max": 500, "display_name": "Luxury ($300-$500)", "count": 0},
                    {"min": 500, "max": 1000, "display_name": "Premium ($500-$1000)", "count": 0},
                    {"min": 1000, "max": None, "display_name": "Ultra-luxury ($1000+)", "count": 0}
                ]
            
            return rate_ranges
            
        except Exception as e:
            logger.error(f"Error fetching rate ranges: {str(e)}")
            return []
    
    async def _get_countries_filter(self, db: Session) -> List[Dict[str, Any]]:
        """Get all unique countries with counts"""
        try:
            countries_query = db.query(
                Hotel.country,
                func.count(Hotel.id).label('count')
            ).filter(
                Hotel.country.isnot(None),
                Hotel.country != ''
            ).group_by(
                Hotel.country
            ).order_by(
                func.count(Hotel.id).desc(),
                Hotel.country
            ).all()
            
            countries = []
            for country in countries_query:
                countries.append({
                    "name": country.country,
                    "count": country.count,
                    "display_name": country.country
                })
            
            return countries
            
        except Exception as e:
            logger.error(f"Error fetching countries: {str(e)}")
            return []
    
    async def _get_cities_filter(self, db: Session) -> List[Dict[str, Any]]:
        """Get all unique cities with counts"""
        try:
            cities_query = db.query(
                Hotel.city,
                Hotel.country,
                func.count(Hotel.id).label('count')
            ).filter(
                Hotel.city.isnot(None),
                Hotel.city != ''
            ).group_by(
                Hotel.city, Hotel.country
            ).order_by(
                func.count(Hotel.id).desc(),
                Hotel.city
            ).all()
            
            cities = []
            for city in cities_query:
                display_name = city.city
                if city.country:
                    display_name += f", {city.country}"
                
                cities.append({
                    "name": city.city,
                    "country": city.country,
                    "count": city.count,
                    "display_name": display_name
                })
            
            return cities
            
        except Exception as e:
            logger.error(f"Error fetching cities: {str(e)}")
            return []
    
    async def _get_total_hotels_count(self, db: Session) -> int:
        """Get total number of hotels in database"""
        try:
            return db.query(Hotel).count()
        except Exception as e:
            logger.error(f"Error getting total hotels count: {str(e)}")
            return 0

# Create controller instance
def get_filter_data_controller() -> FilterDataController:
    return FilterDataController()

@router.get("/all", tags=["Filter Data"])
async def get_all_filters(
    db: Session = Depends(get_db),
    controller: FilterDataController = Depends(get_filter_data_controller)
):
    """
    Get all available filter data from database.
    
    Returns:
        Dictionary containing:
        - amenities: List of all amenities with counts and types
        - star_ratings: List of all star ratings with counts
        - neighborhoods: List of all neighborhoods/locations with counts
        - rate_ranges: List of rate ranges for budget filtering
        - countries: List of all countries with counts
        - cities: List of all cities with counts
        - total_hotels: Total number of hotels in database
    """
    return await controller.get_all_filters(db)

@router.get("/amenities", tags=["Filter Data"])
async def get_amenities_filter(
    db: Session = Depends(get_db),
    controller: FilterDataController = Depends(get_filter_data_controller)
):
    """Get all amenities filter data"""
    amenities = await controller._get_amenities_filter(db)
    return {
        "amenities": amenities,
        "total": len(amenities)
    }

@router.get("/star-ratings", tags=["Filter Data"])
async def get_star_ratings_filter(
    db: Session = Depends(get_db),
    controller: FilterDataController = Depends(get_filter_data_controller)
):
    """Get all star ratings filter data"""
    star_ratings = await controller._get_star_ratings_filter(db)
    return {
        "star_ratings": star_ratings,
        "total": len(star_ratings)
    }

@router.get("/neighborhoods", tags=["Filter Data"])
async def get_neighborhoods_filter(
    db: Session = Depends(get_db),
    controller: FilterDataController = Depends(get_filter_data_controller)
):
    """Get all neighborhoods/locations filter data"""
    neighborhoods = await controller._get_neighborhoods_filter(db)
    return {
        "neighborhoods": neighborhoods,
        "total": len(neighborhoods)
    }

@router.get("/rate-ranges", tags=["Filter Data"])
async def get_rate_ranges_filter(
    db: Session = Depends(get_db),
    controller: FilterDataController = Depends(get_filter_data_controller)
):
    """Get all rate ranges filter data"""
    rate_ranges = await controller._get_rate_ranges_filter(db)
    return {
        "rate_ranges": rate_ranges,
        "total": len(rate_ranges)
    }

@router.get("/countries", tags=["Filter Data"])
async def get_countries_filter(
    db: Session = Depends(get_db),
    controller: FilterDataController = Depends(get_filter_data_controller)
):
    """Get all countries filter data"""
    countries = await controller._get_countries_filter(db)
    return {
        "countries": countries,
        "total": len(countries)
    }

@router.get("/cities", tags=["Filter Data"])
async def get_cities_filter(
    db: Session = Depends(get_db),
    controller: FilterDataController = Depends(get_filter_data_controller)
):
    """Get all cities filter data"""
    cities = await controller._get_cities_filter(db)
    return {
        "cities": cities,
        "total": len(cities)
    }

@router.get("/amenities/by-type", tags=["Filter Data"])
async def get_amenities_by_type(
    db: Session = Depends(get_db),
    controller: FilterDataController = Depends(get_filter_data_controller)
):
    """Get amenities grouped by type"""
    try:
        amenities = await controller._get_amenities_filter(db)
        
        # Group amenities by type
        amenities_by_type = {}
        for amenity in amenities:
            amenity_type = amenity.get('type', 'general')
            if amenity_type not in amenities_by_type:
                amenities_by_type[amenity_type] = []
            amenities_by_type[amenity_type].append(amenity)
        
        return {
            "amenities_by_type": amenities_by_type,
            "types": list(amenities_by_type.keys()),
            "total_types": len(amenities_by_type)
        }
    except Exception as e:
        logger.error(f"Error getting amenities by type: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/popular", tags=["Filter Data"])
async def get_popular_filters(
    db: Session = Depends(get_db),
    controller: FilterDataController = Depends(get_filter_data_controller)
):
    """Get popular filter options (top items)"""
    try:
        amenities = await controller._get_amenities_filter(db)
        neighborhoods = await controller._get_neighborhoods_filter(db)
        countries = await controller._get_countries_filter(db)
        cities = await controller._get_cities_filter(db)
        
        return {
            "popular_amenities": amenities[:10],
            "popular_neighborhoods": neighborhoods[:10],
            "popular_countries": countries[:10],
            "popular_cities": cities[:10]
        }
    except Exception as e:
        logger.error(f"Error getting popular filters: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
