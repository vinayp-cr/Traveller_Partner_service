#!/usr/bin/env python3
"""
Consolidated Search Filters Service
Standalone service for consolidated search functionality without modifying existing services
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.logger import logger
from app.models.hotel_entities import Hotel, HotelAmenity, HotelImage
from sqlalchemy import and_, or_, func, desc, asc


class ConsolidatedSearchService:
    """
    Standalone service for consolidated search functionality.
    Does not modify existing services, models, or repositories.
    """
    
    def __init__(self):
        pass
    
    def search_hotels_comprehensive(self, db: Session, filters: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        """Comprehensive hotel search with all available filters"""
        try:
            query = db.query(Hotel)
            
            # Apply filters dynamically
            if filters.get('amenities'):
                query = self._apply_amenities_filter(db, query, filters['amenities'])
            
            if filters.get('min_rating') is not None:
                query = query.filter(Hotel.avg_rating >= filters['min_rating'])
            
            if filters.get('star_ratings'):
                query = query.filter(Hotel.star_rating.in_(filters['star_ratings']))
            
            if filters.get('property_name'):
                query = query.filter(Hotel.name.ilike(f"%{filters['property_name']}%"))
            
            if filters.get('neighborhoods'):
                query = query.filter(or_(
                    Hotel.city.in_([n.lower() for n in filters['neighborhoods']]),
                    Hotel.state.in_([n.lower() for n in filters['neighborhoods']])
                ))
            
            if filters.get('location'):
                query = query.filter(or_(
                    Hotel.city.ilike(f"%{filters['location']}%"),
                    Hotel.state.ilike(f"%{filters['location']}%"),
                    Hotel.country.ilike(f"%{filters['location']}%")
                ))
            
            # Apply sorting
            sort_by = filters.get('sort_by', 'recommended')
            query = self._apply_sorting(query, sort_by)
            
            # Apply limit
            hotels = query.limit(limit).all()
            
            # Convert to response format
            return [self._hotel_to_dict(hotel, db) for hotel in hotels]
            
        except Exception as e:
            logger.error(f"Error in comprehensive search: {str(e)}")
            raise e
    
    def search_hotels_quick(self, db: Session, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Quick search by name, location, or amenity"""
        try:
            # Search by hotel name first
            hotels = db.query(Hotel).filter(
                Hotel.name.ilike(f"%{query_text}%")
            ).limit(limit).all()
            
            # If no results by name, search by location
            if not hotels:
                hotels = db.query(Hotel).filter(or_(
                    Hotel.city.ilike(f"%{query_text}%"),
                    Hotel.state.ilike(f"%{query_text}%"),
                    Hotel.country.ilike(f"%{query_text}%")
                )).limit(limit).all()
            
            # If still no results, search by amenities
            if not hotels:
                hotels = db.query(Hotel).join(HotelAmenity).filter(
                    HotelAmenity.amenity_name.ilike(f"%{query_text}%")
                ).limit(limit).all()
            
            return [self._hotel_to_dict(hotel, db) for hotel in hotels]
            
        except Exception as e:
            logger.error(f"Error in quick search: {str(e)}")
            raise e
    
    def search_hotels_by_amenities(self, db: Session, amenities: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search hotels that have ALL specified amenities"""
        try:
            # Get hotels that have all specified amenities
            subquery = db.query(HotelAmenity.hotel_id).filter(
                HotelAmenity.amenity_name.in_(amenities)
            ).group_by(HotelAmenity.hotel_id).having(
                func.count(HotelAmenity.amenity_name) == len(amenities)
            ).subquery()
            
            hotels = db.query(Hotel).join(
                subquery, Hotel.id == subquery.c.hotel_id
            ).limit(limit).all()
            
            return [self._hotel_to_dict(hotel, db) for hotel in hotels]
            
        except Exception as e:
            logger.error(f"Error searching by amenities: {str(e)}")
            raise e
    
    def search_hotels_by_rating(self, db: Session, min_rating: float, limit: int = 10) -> List[Dict[str, Any]]:
        """Search hotels by minimum rating"""
        try:
            hotels = db.query(Hotel).filter(
                Hotel.avg_rating >= min_rating
            ).order_by(desc(Hotel.avg_rating)).limit(limit).all()
            
            return [self._hotel_to_dict(hotel, db) for hotel in hotels]
            
        except Exception as e:
            logger.error(f"Error searching by rating: {str(e)}")
            raise e
    
    def search_hotels_by_location(self, db: Session, location: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search hotels by location"""
        try:
            hotels = db.query(Hotel).filter(or_(
                Hotel.city.ilike(f"%{location}%"),
                Hotel.state.ilike(f"%{location}%"),
                Hotel.country.ilike(f"%{location}%")
            )).limit(limit).all()
            
            return [self._hotel_to_dict(hotel, db) for hotel in hotels]
            
        except Exception as e:
            logger.error(f"Error searching by location: {str(e)}")
            raise e
    
    def get_filter_options(self, db: Session) -> Dict[str, Any]:
        """Get available filter options"""
        try:
            # Get amenities with counts
            amenities = db.query(
                HotelAmenity.amenity_name,
                func.count(HotelAmenity.hotel_id).label('count')
            ).group_by(HotelAmenity.amenity_name).all()
            
            # Get unique cities and states
            locations = db.query(Hotel.city, Hotel.state).distinct().all()
            
            # Get star ratings
            star_ratings = db.query(Hotel.star_rating).distinct().all()
            
            # Get price range
            price_range = db.query(
                func.min(Hotel.avg_rating),  # Using rating as proxy for price
                func.max(Hotel.avg_rating)
            ).first()
            
            return {
                "available_amenities": [
                    {"name": amenity[0], "count": amenity[1]} 
                    for amenity in amenities
                ],
                "available_neighborhoods": [
                    {"name": f"{loc[0]}, {loc[1]}", "count": 1} 
                    for loc in locations if loc[0] and loc[1]
                ],
                "available_property_types": ["hotel", "resort", "boutique", "apartment"],
                "available_property_themes": ["business", "luxury", "family", "romantic"],
                "available_nearby_attractions": ["airport", "beach", "downtown", "shopping"],
                "price_range": {
                    "min": price_range[0] if price_range[0] else 0,
                    "max": price_range[1] if price_range[1] else 10
                },
                "star_ratings": [rating[0] for rating in star_ratings if rating[0]]
            }
            
        except Exception as e:
            logger.error(f"Error getting filter options: {str(e)}")
            raise e
    
    def get_search_stats(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get search statistics"""
        try:
            # Total hotels
            total_hotels = db.query(Hotel).count()
            
            # Filtered count if filters provided
            filtered_count = total_hotels
            if filters:
                query = db.query(Hotel)
                if filters.get('amenities'):
                    query = self._apply_amenities_filter(query, filters['amenities'])
                if filters.get('min_rating') is not None:
                    query = query.filter(Hotel.avg_rating >= filters['min_rating'])
                if filters.get('star_ratings'):
                    query = query.filter(Hotel.star_rating.in_(filters['star_ratings']))
                filtered_count = query.count()
            
            # Average rating
            avg_rating = db.query(func.avg(Hotel.avg_rating)).scalar() or 0
            
            # Amenities count
            amenities_count = db.query(HotelAmenity).count()
            
            return {
                "total_hotels": total_hotels,
                "filtered_hotels": filtered_count,
                "average_rating": round(avg_rating, 2),
                "total_amenities": amenities_count,
                "filters_applied": filters or {}
            }
            
        except Exception as e:
            logger.error(f"Error getting search stats: {str(e)}")
            raise e
    
    def get_sort_options(self) -> Dict[str, str]:
        """Get available sorting options"""
        return {
            "recommended": "Recommended (default)",
            "price_low_to_high": "Price: Low to High",
            "price_high_to_low": "Price: High to Low",
            "rating": "Guest Rating (High to Low)",
            "star_rating": "Star Rating (High to Low)",
            "name_asc": "Name: A to Z",
            "name_desc": "Name: Z to A"
        }
    
    def _apply_amenities_filter(self, db: Session, query, amenities: List[str]):
        """Apply amenities filter to query"""
        subquery = db.query(HotelAmenity.hotel_id).filter(
            HotelAmenity.amenity_name.in_(amenities)
        ).group_by(HotelAmenity.hotel_id).having(
            func.count(HotelAmenity.amenity_name) == len(amenities)
        ).subquery()
        
        return query.join(subquery, Hotel.id == subquery.c.hotel_id)
    
    def _apply_sorting(self, query, sort_by: str):
        """Apply sorting to query"""
        if sort_by == "rating":
            return query.order_by(desc(Hotel.avg_rating))
        elif sort_by == "star_rating":
            return query.order_by(desc(Hotel.star_rating))
        elif sort_by == "name_asc":
            return query.order_by(asc(Hotel.name))
        elif sort_by == "name_desc":
            return query.order_by(desc(Hotel.name))
        elif sort_by == "price_low_to_high":
            return query.order_by(asc(Hotel.avg_rating))  # Using rating as proxy
        elif sort_by == "price_high_to_low":
            return query.order_by(desc(Hotel.avg_rating))  # Using rating as proxy
        else:  # recommended
            return query.order_by(desc(Hotel.avg_rating), desc(Hotel.star_rating))
    
    def _hotel_to_dict(self, hotel: Hotel, db: Session) -> Dict[str, Any]:
        """Convert hotel entity to dictionary with amenities and images"""
        try:
            # Get amenities
            amenities = db.query(HotelAmenity).filter(
                HotelAmenity.hotel_id == hotel.id
            ).all()
            
            # Get images
            images = db.query(HotelImage).filter(
                HotelImage.hotel_id == hotel.id
            ).all()
            
            return {
                "id": hotel.id,
                "name": hotel.name,
                "description": hotel.description or "",
                "address": hotel.address or "",
                "city": hotel.city or "",
                "state": hotel.state or "",
                "country": hotel.country or "",
                "postal_code": hotel.postal_code or "",
                "latitude": float(hotel.latitude) if hotel.latitude else None,
                "longitude": float(hotel.longitude) if hotel.longitude else None,
                "star_rating": hotel.star_rating,
                "avg_rating": float(hotel.avg_rating) if hotel.avg_rating else None,
                "total_reviews": hotel.total_reviews or 0,
                "amenities": [
                    {
                        "name": amenity.amenity_name,
                        "type": amenity.amenity_type or "general"
                    }
                    for amenity in amenities
                ],
                "images": [
                    {
                        "url": image.image,
                        "caption": image.caption or "",
                        "is_primary": image.is_primary or False,
                        "sort_order": image.sort_order or 0
                    }
                    for image in images
                ],
                "price": None,  # Not available in current schema
                "currency": "USD"  # Default currency
            }
            
        except Exception as e:
            logger.error(f"Error converting hotel to dict: {str(e)}")
            # Return basic hotel info if conversion fails
            return {
                "id": hotel.id,
                "name": hotel.name,
                "description": hotel.description or "",
                "address": hotel.address or "",
                "city": hotel.city or "",
                "state": hotel.state or "",
                "country": hotel.country or "",
                "star_rating": hotel.star_rating,
                "avg_rating": float(hotel.avg_rating) if hotel.avg_rating else None,
                "amenities": [],
                "images": []
            }
