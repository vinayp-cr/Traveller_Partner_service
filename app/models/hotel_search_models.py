"""
Hotel Search Models
Pydantic models for the Xeni Hotel Search API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any


class Occupancy(BaseModel):
    """Occupancy details for hotel search"""
    adults: int = Field(..., description="Number of adults")
    childs: int = Field(..., description="Number of children")
    childages: List[int] = Field(default_factory=list, description="Ages of children")


class SortCriteria(BaseModel):
    """Sort criteria for hotel search"""
    key: str = Field(..., description="Sort key (e.g., 'price')")
    order: str = Field(..., description="Sort order ('asc' or 'desc')")


class Filters(BaseModel):
    """Filter criteria for hotel search"""
    ratings: Optional[List[int]] = Field(None, description="Star ratings to filter by")
    amenities: Optional[List[str]] = Field(None, description="Amenities to filter by")
    name: Optional[str] = Field(None, description="Hotel name filter")
    min_price: Optional[float] = Field(None, description="Minimum price filter")
    max_price: Optional[float] = Field(None, description="Maximum price filter")


class HotelSearchRequest(BaseModel):
    """Request model for hotel search API"""
    checkin_date: str = Field(..., description="Check-in date (template: {{checkin_date}})")
    checkout_date: str = Field(..., description="Check-out date (template: {{checkout_date}})")
    occupancy: List[Occupancy] = Field(..., description="Occupancy details")
    country_of_residence: str = Field(..., description="Country of residence code")
    place_id: str = Field(..., description="Place ID (template: {{place_id}})")
    lat: float = Field(..., description="Latitude coordinate")
    lng: float= Field(..., description="Longitude coordinate")
    radius: Optional[int] = Field(None, description="Search radius in kilometers")
    sort: List[SortCriteria] = Field(..., description="Sort criteria")
    filters: Optional[Filters] = Field(None, description="Filter criteria")
    is_async: bool = Field(False, description="Whether to use async processing")


# Response Models
class LocationData(BaseModel):
    """Location coordinates"""
    lat: float = Field(..., description="Latitude")
    long: float = Field(..., description="Longitude")


class Address(BaseModel):
    """Address information"""
    line_1: str = Field(..., description="Address line 1")
    country: str = Field(..., description="Country")
    state: str = Field(..., description="State")
    city: str = Field(..., description="City")
    postal_code: str = Field(..., description="Postal code")


class Contact(BaseModel):
    """Contact information"""
    phone: str = Field(..., description="Phone number")
    address: Address = Field(..., description="Address details")


class Ratings(BaseModel):
    """Rating information"""
    star_rating: int = Field(..., description="Star rating")
    user_rating: float = Field(..., description="User rating")


class Rate(BaseModel):
    """Rate information"""
    base_rate: float = Field(..., description="Base rate")
    total_rate: float = Field(..., description="Total rate")
    tax_and_fees: float = Field(..., description="Tax and fees")
    currency: str = Field(..., description="Currency code")


class Image(BaseModel):
    """Image information"""
    thumbnail: str = Field(..., description="Thumbnail image URL")
    large: str = Field(..., description="Large image URL")
    extra_large: str = Field(..., description="Extra large image URL")


class HotelData(BaseModel):
    """Individual hotel data"""
    property_id: str = Field(..., description="Property ID")
    name: str = Field(..., description="Hotel name")
    location: LocationData = Field(..., description="Location coordinates")
    contact: Contact = Field(..., description="Contact information")
    ratings: Ratings = Field(..., description="Rating information")
    rate: Rate = Field(..., description="Rate information")
    amenities: List[str] = Field(..., description="List of amenities")
    image: Image = Field(..., description="Image information")
    chain: str = Field(..., description="Hotel chain")


class HotelSearchData(BaseModel):
    """Search data container"""
    total: int = Field(..., description="Total number of hotels found")
    hotels: List[HotelData] = Field(..., description="List of hotels")


class HotelSearchSuccessResponse(BaseModel):
    """Success response for hotel search API"""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: HotelSearchData = Field(..., description="Search data")
    correlation_id: Optional[str] = Field(None, description="X-Correlation-Id from response headers")


class ErrorField(BaseModel):
    """Error field information"""
    name: str = Field(..., description="Field name that caused the error")
    type: str = Field(..., description="Field type (query, body, etc.)")


class ErrorDescription(BaseModel):
    """Error description details"""
    type: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Error message")
    fields: Optional[List[ErrorField]] = Field(None, description="Fields that caused the error")


class HotelSearchErrorResponse(BaseModel):
    """Error response for hotel search API"""
    desc: List[ErrorDescription] = Field(..., description="List of error descriptions")
    error: str = Field(..., description="Main error message")
    status: str = Field(..., description="Error status")
    correlation_id: Optional[str] = Field(None, description="X-Correlation-Id from response headers")


# Union type for all possible responses
HotelSearchResponse = Union[HotelSearchSuccessResponse, HotelSearchErrorResponse]


# Hotel Details Models
class ContactData(BaseModel):
    """Contact information for hotel details"""
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[Dict[str, Any]] = Field(None, description="Address information")


class LocationData(BaseModel):
    """Location information for hotel details"""
    lat: Optional[float] = Field(None, description="Latitude")
    long: Optional[float] = Field(None, description="Longitude")


class RatingsData(BaseModel):
    """Rating information for hotel details"""
    star_rating: Optional[int] = Field(None, description="Star rating")
    user_rating: Optional[float] = Field(None, description="User rating")


class PolicyData(BaseModel):
    """Policy information for hotel details"""
    type: str = Field(..., description="Policy type")
    description: str = Field(..., description="Policy description")


class HighlightData(BaseModel):
    """Highlight information for hotel details"""
    type: str = Field(..., description="Highlight type")
    description: str = Field(..., description="Highlight description")


class ImageData(BaseModel):
    """Image information for hotel details"""
    thumbnail: List[str] = Field(default_factory=list, description="Thumbnail image URLs")
    small: List[str] = Field(default_factory=list, description="Small image URLs")
    large: List[str] = Field(default_factory=list, description="Large image URLs")
    extra_large: List[str] = Field(default_factory=list, description="Extra large image URLs")


class HotelDetailsData(BaseModel):
    """Hotel details data"""
    property_id: str = Field(..., description="Property ID")
    name: str = Field(..., description="Hotel name")
    contact: Optional[ContactData] = Field(None, description="Contact information")
    location: Optional[LocationData] = Field(None, description="Location information")
    ratings: Optional[RatingsData] = Field(None, description="Rating information")
    accessibilities: List[str] = Field(default_factory=list, description="Accessibility features")
    amenities: List[str] = Field(default_factory=list, description="Hotel amenities")
    policies: List[PolicyData] = Field(default_factory=list, description="Hotel policies")
    highlights: List[HighlightData] = Field(default_factory=list, description="Hotel highlights")
    images: Optional[ImageData] = Field(None, description="Hotel images")


class HotelDetailsSuccessResponse(BaseModel):
    """Success response for hotel details API"""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: HotelDetailsData = Field(..., description="Hotel details data")


class HotelDetailsErrorResponse(BaseModel):
    """Error response for hotel details API"""
    desc: List[ErrorDescription] = Field(..., description="Error descriptions")
    error: str = Field(..., description="Error message")
    status: str = Field(..., description="Error status")


# Union type for all possible responses
HotelDetailsResponse = Union[HotelDetailsSuccessResponse, HotelDetailsErrorResponse]


# Hotel Availability Models
class AvailabilityOccupancy(BaseModel):
    """Occupancy details for availability request"""
    adults: int = Field(..., description="Number of adults")
    childs: int = Field(..., description="Number of children")
    childages: List[int] = Field(default_factory=list, description="Ages of children")


class AvailabilityRequest(BaseModel):
    """Request model for hotel availability API"""
    property_id: str = Field(..., description="Property ID")
    checkin_date: str = Field(..., description="Check-in date")
    checkout_date: str = Field(..., description="Check-out date")
    occupancy: List[AvailabilityOccupancy] = Field(..., description="Occupancy details")
    country_of_residence: str = Field(..., description="Country of residence code")


class BedData(BaseModel):
    """Bed configuration data"""
    name: str = Field(..., description="Bed type name")
    availability_token: str = Field(..., description="Availability token")


class CancellationPolicyData(BaseModel):
    """Cancellation policy data"""
    start: str = Field(..., description="Policy start date")
    end: str = Field(..., description="Policy end date")
    value: int = Field(..., description="Policy value")
    currency: str = Field(..., description="Currency")
    type: str = Field(..., description="Policy type")
    estimate_amount: int = Field(..., description="Estimated amount")


class RateData(BaseModel):
    """Rate information for availability"""
    refundable: bool = Field(..., description="Whether rate is refundable")
    base_rate: float = Field(..., description="Base rate")
    tax_and_fees: int = Field(..., description="Tax and fees")
    total_rate: float = Field(..., description="Total rate")
    currency: str = Field(..., description="Currency")
    retail_price: float = Field(..., description="Retail price")
    saved_price: float = Field(..., description="Amount saved")
    board_basis: List[str] = Field(..., description="Board basis")
    beds: List[BedData] = Field(..., description="Bed configuration")
    cancellation_policy: List[CancellationPolicyData] = Field(..., description="Cancellation policy")
    amenities: List[str] = Field(..., description="Rate amenities")
    extras: List[str] = Field(..., description="Rate extras")


class AreaData(BaseModel):
    """Area measurements"""
    square_meters: int = Field(..., description="Area in square meters")
    square_feet: int = Field(..., description="Area in square feet")


class AvailabilityData(BaseModel):
    """Availability data for a room type"""
    id: str = Field(..., description="Room type ID")
    name: str = Field(..., description="Room type name")
    sleeps: int = Field(..., description="Number of people it sleeps")
    descriptions: str = Field(..., description="Room descriptions")
    images: ImageData = Field(..., description="Room images")
    availability: int = Field(..., description="Number of available units")
    amenities: List[str] = Field(..., description="Room amenities")
    rates: List[RateData] = Field(..., description="Rate information")
    area: AreaData = Field(..., description="Room area")


class AvailabilitySuccessResponse(BaseModel):
    """Success response for availability API"""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: List[AvailabilityData] = Field(..., description="Availability data")


class AvailabilityErrorResponse(BaseModel):
    """Error response for availability API"""
    desc: List[ErrorDescription] = Field(..., description="Error descriptions")
    error: str = Field(..., description="Error message")
    status: str = Field(..., description="Error status")


class AvailabilityResponse(BaseModel):
    """Response model for availability API"""
    success: Optional[AvailabilitySuccessResponse] = None
    error: Optional[AvailabilityErrorResponse] = None


# Hotel Pricing Models
class PriceRequest(BaseModel):
    """Request model for hotel pricing API"""
    availability_token: str = Field(..., description="Availability token from availability response")
    currency: str = Field(default="USD", description="Currency code")


class RoomImages(BaseModel):
    """Room images with different sizes"""
    thumbnail: List[str] = Field(..., description="Thumbnail images")
    small: List[str] = Field(..., description="Small images")
    large: List[str] = Field(..., description="Large images")
    extra_large: List[str] = Field(..., description="Extra large images")


class RoomPriceData(BaseModel):
    """Room pricing data"""
    id: str = Field(..., description="Room ID")
    name: str = Field(..., description="Room name")
    descriptions: str = Field(..., description="Room descriptions")
    images: RoomImages = Field(..., description="Room images")
    amenities: List[str] = Field(..., description="Room amenities")
    number_of_adults: int = Field(..., description="Number of adults")
    bed: str = Field(..., description="Bed configuration")
    all_guest_info_required: bool = Field(..., description="All guest info required")
    special_request_supported: bool = Field(..., description="Special request supported")


class PriceData(BaseModel):
    """Enhanced pricing data for hotel"""
    status: str = Field(..., description="Availability status")
    property_id: str = Field(..., description="Property ID")
    checkin_date: str = Field(..., description="Check-in date")
    checkout_date: str = Field(..., description="Check-out date")
    refundable: bool = Field(..., description="Whether rate is refundable")
    board_basis: List[str] = Field(..., description="Board basis")
    base_rate: float = Field(..., description="Base rate")
    tax_and_fees: float = Field(..., description="Tax and fees")
    retail_price: float = Field(..., description="Retail price")
    saved_price: float = Field(..., description="Amount saved")
    total_price: float = Field(..., description="Total price")
    currency: str = Field(..., description="Currency")
    cancellation_policy: List[CancellationPolicyData] = Field(..., description="Cancellation policy")
    rooms: List[RoomPriceData] = Field(..., description="Room details")
    pricing_token: str = Field(..., description="Pricing token for booking")


class PriceSuccessResponse(BaseModel):
    """Success response for pricing API"""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: PriceData = Field(..., description="Pricing data")


class PriceErrorResponse(BaseModel):
    """Error response for pricing API"""
    desc: List[ErrorDescription] = Field(..., description="Error descriptions")
    error: str = Field(..., description="Error message")
    status: str = Field(..., description="Error status")


class PriceResponse(BaseModel):
    """Response model for pricing API"""
    success: Optional[PriceSuccessResponse] = None
    error: Optional[PriceErrorResponse] = None


# Hotel Booking Models
class RoomGuest(BaseModel):
    """Guest information for booking"""
    title: str = Field(..., description="Guest title (Mr, Mrs, Ms, etc.)")
    first_name: str = Field(..., description="Guest first name")
    last_name: str = Field(..., description="Guest last name")


class PhoneData(BaseModel):
    """Phone number information"""
    country_code: str = Field(..., description="Country code")
    number: str = Field(..., description="Phone number")


class BookHotelRequest(BaseModel):
    """Request model for hotel booking API"""
    booking_id: str = Field(..., description="Booking ID")
    rooms: List[RoomGuest] = Field(..., description="Guest information for each room")
    email: str = Field(..., description="Email address for booking confirmation")
    phone: PhoneData = Field(..., description="Phone number information")


class BookingData(BaseModel):
    """Booking data from successful booking"""
    booking_id: str = Field(..., description="Booking ID")
    booking_status: str = Field(..., description="Booking status (CONFIRMED, PENDING, etc.)")


class BookHotelSuccessResponse(BaseModel):
    """Success response for booking API"""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: BookingData = Field(..., description="Booking data")


class BookHotelErrorResponse(BaseModel):
    """Error response for booking API"""
    desc: List[ErrorDescription] = Field(..., description="Error descriptions")
    error: str = Field(..., description="Error message")
    status: str = Field(..., description="Error status")


class BookHotelResponse(BaseModel):
    """Response model for booking API"""
    success: Optional[BookHotelSuccessResponse] = None
    error: Optional[BookHotelErrorResponse] = None


# Hotel Cancellation Models
class CancelBookingRequest(BaseModel):
    """Request model for hotel booking cancellation API"""
    booking_status: str = Field("CANCELLED", description="Booking status to set (e.g., CANCELLED)")


class CancellationData(BaseModel):
    """Cancellation data from successful cancellation"""
    booking_id: str = Field(..., description="Booking ID")
    cancellation_status: str = Field(..., description="Cancellation status (CANCELLED, PENDING, etc.)")
    refund_amount: Optional[float] = Field(None, description="Refund amount if applicable")
    cancellation_fee: Optional[float] = Field(None, description="Cancellation fee if applicable")


class CancelBookingSuccessResponse(BaseModel):
    """Success response for cancellation API"""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: CancellationData = Field(..., description="Cancellation data")


class CancelBookingErrorResponse(BaseModel):
    """Error response for cancellation API"""
    desc: List[ErrorDescription] = Field(..., description="Error descriptions")
    error: str = Field(..., description="Error message")
    status: str = Field(..., description="Error status")


class CancelBookingResponse(BaseModel):
    """Response model for cancellation API"""
    success: Optional[CancelBookingSuccessResponse] = None
    error: Optional[CancelBookingErrorResponse] = None
