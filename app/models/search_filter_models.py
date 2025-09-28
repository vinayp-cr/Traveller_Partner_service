#!/usr/bin/env python3
"""
Search Filter Models
Models for hotel search filtering functionality
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Occupancy(BaseModel):
    """Occupancy details for hotel search"""
    numOfAdults: int = Field(..., ge=1, le=10, description="Number of adults")
    numOfChildren: int = Field(0, ge=0, le=10, description="Number of children")
    numOfRoom: int = Field(1, ge=1, le=5, description="Number of rooms")
    childAges: Optional[List[int]] = Field(None, description="Ages of children")


class BudgetRange(BaseModel):
    """Budget range for filtering"""
    min: Optional[float] = Field(None, ge=0, description="Minimum price")
    max: Optional[float] = Field(None, ge=0, description="Maximum price")


class HotelFilters(BaseModel):
    """Hotel search filters"""
    sortBy: Optional[str] = Field("recommended", description="Sort criteria")
    starRating: Optional[List[int]] = Field(None, description="Star ratings to filter by")
    guestRating: Optional[float] = Field(None, ge=0, le=10, description="Minimum guest rating")
    amenities: Optional[List[str]] = Field(None, description="Required amenities")
    neighborhoods: Optional[List[str]] = Field(None, description="Neighborhoods to filter by")
    propertyName: Optional[str] = Field(None, description="Property name search")
    budget: Optional[BudgetRange] = Field(None, description="Budget range")
    propertyTypes: Optional[List[str]] = Field(None, description="Property types")
    propertyThemes: Optional[List[str]] = Field(None, description="Property themes")
    nearbyAttractions: Optional[List[str]] = Field(None, description="Nearby attractions")


class Pagination(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")


class HotelFilterRequest(BaseModel):
    """Main request model for filtered hotel search"""
    locationId: str = Field(..., description="Location ID for search")
    checkInDate: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    checkOutDate: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    occupancies: List[Occupancy] = Field(..., description="Occupancy details")
    currency: Optional[str] = Field("USD", description="Currency code")
    filters: Optional[HotelFilters] = Field(None, description="Filter criteria")
    pagination: Optional[Pagination] = Field(None, description="Pagination parameters")


class HotelSearchResult(BaseModel):
    """Individual hotel search result"""
    id: str = Field(..., description="Hotel ID")
    name: str = Field(..., description="Hotel name")
    description: Optional[str] = Field(None, description="Hotel description")
    address: Optional[str] = Field(None, description="Hotel address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")
    postal_code: Optional[str] = Field(None, description="Postal code")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email")
    website: Optional[str] = Field(None, description="Website")
    star_rating: Optional[int] = Field(None, description="Star rating")
    avg_rating: Optional[float] = Field(None, description="Average rating")
    total_reviews: Optional[int] = Field(None, description="Total reviews")
    amenities: List[Dict[str, Any]] = Field(default_factory=list, description="Hotel amenities")
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Hotel images")
    price: Optional[float] = Field(None, description="Price per night")
    currency: Optional[str] = Field(None, description="Currency")


class FilterOptions(BaseModel):
    """Available filter options"""
    availableAmenities: List[Dict[str, Any]] = Field(default_factory=list, description="Available amenities")
    availableNeighborhoods: List[Dict[str, Any]] = Field(default_factory=list, description="Available neighborhoods")
    availablePropertyTypes: List[str] = Field(default_factory=list, description="Available property types")
    availablePropertyThemes: List[str] = Field(default_factory=list, description="Available property themes")
    availableNearbyAttractions: List[str] = Field(default_factory=list, description="Available nearby attractions")
    priceRange: Optional[Dict[str, float]] = Field(None, description="Price range (min, max)")
    starRatings: List[int] = Field(default_factory=list, description="Available star ratings")


class HotelFilterResponse(BaseModel):
    """Response model for filtered hotel search"""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: Dict[str, Any] = Field(..., description="Response data")
    hotels: List[HotelSearchResult] = Field(default_factory=list, description="Filtered hotels")
    totalCount: int = Field(0, description="Total number of hotels")
    page: int = Field(1, description="Current page")
    limit: int = Field(20, description="Items per page")
    totalPages: int = Field(0, description="Total number of pages")
    filters: Optional[FilterOptions] = Field(None, description="Available filter options")


class SortOptions(BaseModel):
    """Available sort options"""
    recommended: str = "recommended"
    price_low_to_high: str = "price_low_to_high"
    price_high_to_low: str = "price_high_to_low"
    rating: str = "rating"
    star_rating: str = "star_rating"
    name_asc: str = "name_asc"
    name_desc: str = "name_desc"


class FilterStats(BaseModel):
    """Filter statistics"""
    totalHotels: int = Field(0, description="Total hotels in database")
    filteredHotels: int = Field(0, description="Hotels after filtering")
    amenitiesCount: int = Field(0, description="Total amenities available")
    neighborhoodsCount: int = Field(0, description="Total neighborhoods available")
    averageRating: float = Field(0.0, description="Average rating of filtered hotels")
    averagePrice: float = Field(0.0, description="Average price of filtered hotels")
