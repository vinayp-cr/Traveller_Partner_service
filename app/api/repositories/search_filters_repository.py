#!/usr/bin/env python3
"""
Search Filters Repository
Database operations for hotel search filtering
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from typing import List, Dict, Any, Optional, Tuple
from app.models.hotel_entities import Hotel, HotelAmenity, HotelImage
from app.models.search_filter_models import HotelFilters, Pagination, FilterOptions
from app.core.logger import logger


class SearchFiltersRepository:
    """Repository for hotel search filtering operations"""
    
    def __init__(self):
        self.logger = logger
    
    def search_hotels_with_filters(self, db: Session, filters: HotelFilters, pagination: Pagination) -> Tuple[List[Hotel], int]:
        """
        Search hotels with applied filters
        
        Args:
            db: Database session
            filters: Filter criteria
            pagination: Pagination parameters
            
        Returns:
            Tuple of (filtered_hotels, total_count)
        """
        try:
            # Start with base query
            query = db.query(Hotel).distinct()
            
            # Apply filters
            query = self._apply_filters(query, filters)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply sorting
            query = self._apply_sorting(query, filters.sortBy)
            
            # Apply pagination
            offset = (pagination.page - 1) * pagination.limit
            hotels = query.offset(offset).limit(pagination.limit).all()
            
            self.logger.info(f"Found {len(hotels)} hotels out of {total_count} total after filtering")
            return hotels, total_count
            
        except Exception as e:
            self.logger.error(f"Error in search_hotels_with_filters: {str(e)}")
            raise e
    
    def _apply_filters(self, query, filters: HotelFilters):
        """Apply filter conditions to the query"""
        try:
            # Star rating filter
            if filters.starRating and len(filters.starRating) > 0:
                query = query.filter(Hotel.star_rating.in_(filters.starRating))
            
            # Guest rating filter
            if filters.guestRating and filters.guestRating > 0:
                query = query.filter(Hotel.avg_rating >= filters.guestRating)
            
            # Property name filter
            if filters.propertyName and filters.propertyName.strip():
                search_term = f"%{filters.propertyName.strip()}%"
                query = query.filter(Hotel.name.ilike(search_term))
            
            # Budget filter (if price field exists)
            if filters.budget:
                if filters.budget.min is not None:
                    # Assuming we have a price field, adjust as needed
                    # query = query.filter(Hotel.price >= filters.budget.min)
                    pass
                if filters.budget.max is not None:
                    # query = query.filter(Hotel.price <= filters.budget.max)
                    pass
            
            # Amenities filter
            if filters.amenities and len(filters.amenities) > 0:
                # Use subquery to find hotels with all required amenities
                amenity_subquery = db.query(HotelAmenity.hotel_id).filter(
                    HotelAmenity.amenity_name.in_(filters.amenities)
                ).group_by(HotelAmenity.hotel_id).having(
                    func.count(HotelAmenity.amenity_name) == len(filters.amenities)
                ).subquery()
                
                query = query.filter(Hotel.id.in_(
                    db.query(amenity_subquery.c.hotel_id)
                ))
            
            # Neighborhood filter (using city field)
            if filters.neighborhoods and len(filters.neighborhoods) > 0:
                neighborhood_conditions = []
                for neighborhood in filters.neighborhoods:
                    neighborhood_conditions.append(
                        or_(
                            Hotel.city.ilike(f"%{neighborhood}%"),
                            Hotel.address.ilike(f"%{neighborhood}%")
                        )
                    )
                query = query.filter(or_(*neighborhood_conditions))
            
            # Property types filter (if we have this field)
            if filters.propertyTypes and len(filters.propertyTypes) > 0:
                # Assuming we have a property_type field, adjust as needed
                # query = query.filter(Hotel.property_type.in_(filters.propertyTypes))
                pass
            
            # Property themes filter (if we have this field)
            if filters.propertyThemes and len(filters.propertyThemes) > 0:
                # Assuming we have a property_theme field, adjust as needed
                # query = query.filter(Hotel.property_theme.in_(filters.propertyThemes))
                pass
            
            # Nearby attractions filter (using address/city fields)
            if filters.nearbyAttractions and len(filters.nearbyAttractions) > 0:
                attraction_conditions = []
                for attraction in filters.nearbyAttractions:
                    attraction_conditions.append(
                        or_(
                            Hotel.address.ilike(f"%{attraction}%"),
                            Hotel.city.ilike(f"%{attraction}%")
                        )
                    )
                query = query.filter(or_(*attraction_conditions))
            
            return query
            
        except Exception as e:
            self.logger.error(f"Error applying filters: {str(e)}")
            raise e
    
    def _apply_sorting(self, query, sort_by: str):
        """Apply sorting to the query"""
        try:
            if sort_by == "price_low_to_high":
                # Assuming we have a price field, adjust as needed
                # query = query.order_by(asc(Hotel.price))
                query = query.order_by(asc(Hotel.avg_rating))
            elif sort_by == "price_high_to_low":
                # query = query.order_by(desc(Hotel.price))
                query = query.order_by(desc(Hotel.avg_rating))
            elif sort_by == "rating":
                query = query.order_by(desc(Hotel.avg_rating))
            elif sort_by == "star_rating":
                query = query.order_by(desc(Hotel.star_rating))
            elif sort_by == "name_asc":
                query = query.order_by(asc(Hotel.name))
            elif sort_by == "name_desc":
                query = query.order_by(desc(Hotel.name))
            else:  # recommended (default)
                query = query.order_by(desc(Hotel.avg_rating), desc(Hotel.star_rating))
            
            return query
            
        except Exception as e:
            self.logger.error(f"Error applying sorting: {str(e)}")
            raise e
    
    def get_hotel_with_details(self, db: Session, hotel_id: str) -> Optional[Hotel]:
        """
        Get hotel with amenities and images
        
        Args:
            db: Database session
            hotel_id: Hotel ID
            
        Returns:
            Hotel object with amenities and images
        """
        try:
            hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
            if hotel:
                # Load amenities and images
                hotel.amenities = db.query(HotelAmenity).filter(HotelAmenity.hotel_id == hotel_id).all()
                hotel.images = db.query(HotelImage).filter(HotelImage.hotel_id == hotel_id).all()
            return hotel
            
        except Exception as e:
            self.logger.error(f"Error getting hotel with details: {str(e)}")
            raise e
    
    def get_available_filter_options(self, db: Session) -> FilterOptions:
        """
        Get available filter options for the UI
        
        Args:
            db: Database session
            
        Returns:
            FilterOptions object with available choices
        """
        try:
            # Get available amenities
            amenities = db.query(
                HotelAmenity.amenity_name,
                func.count(HotelAmenity.hotel_id).label('count')
            ).group_by(HotelAmenity.amenity_name).all()
            
            available_amenities = [
                {"name": amenity.amenity_name, "count": amenity.count}
                for amenity in amenities
            ]
            
            # Get available neighborhoods (using city field)
            neighborhoods = db.query(
                Hotel.city,
                func.count(Hotel.id).label('count')
            ).filter(Hotel.city.isnot(None)).group_by(Hotel.city).all()
            
            available_neighborhoods = [
                {"name": neighborhood.city, "count": neighborhood.count}
                for neighborhood in neighborhoods
            ]
            
            # Get available star ratings
            star_ratings = db.query(Hotel.star_rating).filter(
                Hotel.star_rating.isnot(None)
            ).distinct().all()
            
            available_star_ratings = [rating.star_rating for rating in star_ratings]
            available_star_ratings.sort()
            
            # Get price range (if we have price field)
            # price_stats = db.query(
            #     func.min(Hotel.price).label('min_price'),
            #     func.max(Hotel.price).label('max_price')
            # ).filter(Hotel.price.isnot(None)).first()
            
            # price_range = None
            # if price_stats and price_stats.min_price is not None:
            #     price_range = {
            #         "min": float(price_stats.min_price),
            #         "max": float(price_stats.max_price)
            #     }
            
            return FilterOptions(
                availableAmenities=available_amenities,
                availableNeighborhoods=available_neighborhoods,
                availablePropertyTypes=[],  # Add if we have this field
                availablePropertyThemes=[],  # Add if we have this field
                availableNearbyAttractions=[],  # Add if we have this field
                priceRange=None,  # Add if we have price field
                starRatings=available_star_ratings
            )
            
        except Exception as e:
            self.logger.error(f"Error getting filter options: {str(e)}")
            raise e
    
    def get_filter_stats(self, db: Session, filters: Optional[HotelFilters] = None) -> Dict[str, Any]:
        """
        Get statistics for filtered results
        
        Args:
            db: Database session
            filters: Applied filters
            
        Returns:
            Dictionary with filter statistics
        """
        try:
            # Get total hotels count
            total_hotels = db.query(Hotel).count()
            
            # Get filtered count
            if filters:
                query = db.query(Hotel)
                query = self._apply_filters(query, filters)
                filtered_count = query.count()
            else:
                filtered_count = total_hotels
            
            # Get average rating
            avg_rating_result = db.query(func.avg(Hotel.avg_rating)).filter(
                Hotel.avg_rating.isnot(None)
            ).scalar()
            average_rating = float(avg_rating_result) if avg_rating_result else 0.0
            
            # Get amenities count
            amenities_count = db.query(HotelAmenity).count()
            
            # Get neighborhoods count
            neighborhoods_count = db.query(Hotel.city).filter(
                Hotel.city.isnot(None)
            ).distinct().count()
            
            return {
                "totalHotels": total_hotels,
                "filteredHotels": filtered_count,
                "amenitiesCount": amenities_count,
                "neighborhoodsCount": neighborhoods_count,
                "averageRating": average_rating,
                "averagePrice": 0.0  # Add if we have price field
            }
            
        except Exception as e:
            self.logger.error(f"Error getting filter stats: {str(e)}")
            raise e
