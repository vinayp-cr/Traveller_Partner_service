from fastapi import APIRouter, HTTPException, Query, Depends, Header
from app.models.autosuggest_model import AutocompleteRequest, AutosuggestResponse
from app.models.hotel_search_models import HotelSearchRequest, HotelSearchResponse, HotelDetailsResponse, AvailabilityRequest, AvailabilityResponse, PriceRequest, PriceResponse, BookHotelRequest, BookHotelResponse, CancelBookingRequest, CancelBookingResponse
from app.core.logger import logger
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.api.services.hotel_service import HotelService
from app.api.controllers.hotel_controller_helper import HotelControllerHelper

router = APIRouter(prefix="/api/hotel")

# Create controller instance with dependency injection
def get_hotel_controller_helper() -> HotelControllerHelper:
    hotel_service = HotelService()
    return HotelControllerHelper(hotel_service)

# FastAPI route handlers
@router.get("/autocomplete", response_model=AutosuggestResponse, tags=["Hotel Autocomplete"])
async def autocomplete(
    key: str = Query(..., description="Search query text for autocomplete", min_length=1),
    helper: HotelControllerHelper = Depends(get_hotel_controller_helper)
):
    """Get hotel autosuggestions based on text query. Uses new Xeni API v2 with query parameter."""
    # Create request object from query parameter
    payload = AutocompleteRequest(key=key)
    return await helper.autocomplete(payload)


@router.post("/search", response_model=HotelSearchResponse, tags=["Hotel Search"])
async def hotel_search(
    payload: HotelSearchRequest,
    x_correlation_id: str = Header(..., alias="x-correlation-id", description="Correlation ID from autosuggest response"),
    helper: HotelControllerHelper = Depends(get_hotel_controller_helper)
):
    """Search for hotels using the Xeni API with query parameters and correlation ID support."""
    return await helper.hotel_search(payload, x_correlation_id)


@router.post("/search-and-save", response_model=HotelSearchResponse, tags=["Hotel Search & Save"])
async def hotel_search_and_save(
    payload: HotelSearchRequest,
    x_correlation_id: str = Header(..., alias="x-correlation-id", description="Correlation ID from autosuggest response"),
    db: Session = Depends(get_db),
    helper: HotelControllerHelper = Depends(get_hotel_controller_helper)
):
    """Search for hotels using the Xeni API and save results to database."""
    return await helper.hotel_search_and_save(payload, x_correlation_id, db)


@router.get("/details/{property_id}", tags=["Hotel Details"])
async def get_hotel_details(
    property_id: str,
    x_correlation_id: str = Header(..., alias="x-correlation-id", description="Correlation ID from autosuggest response"),
    helper: HotelControllerHelper = Depends(get_hotel_controller_helper)
):
    """Get hotel details using the Xeni API with property ID and correlation ID support."""
    return await helper.get_hotel_details(property_id, x_correlation_id)


@router.post("/availability", tags=["Hotel Availability"])
async def check_hotel_availability(
    request: AvailabilityRequest,
    x_correlation_id: str = Header(..., alias="x-correlation-id", description="Correlation ID from autosuggest response"),
    helper: HotelControllerHelper = Depends(get_hotel_controller_helper)
):
    """Check hotel availability using the Xeni API with property ID, dates, and occupancy details."""
    return await helper.check_hotel_availability(request, x_correlation_id)


@router.get("/price", tags=["Hotel Pricing"])
async def get_hotel_price(
    availability_token: str = Query(..., description="Availability token from availability response"),
    currency: str = Query("USD", description="Currency code"),
    x_correlation_id: str = Header(None, alias="x-correlation-id", description="Correlation ID from autosuggest response (optional)"),
    helper: HotelControllerHelper = Depends(get_hotel_controller_helper)
):
    """Get hotel pricing using the Xeni API with availability token and currency."""
    return await helper.get_hotel_price(availability_token, currency, x_correlation_id)


@router.get("/price-and-save", tags=["Hotel Pricing & Save"])
async def get_hotel_price_and_save(
    availability_token: str = Query(..., description="Availability token from availability response"),
    currency: str = Query("USD", description="Currency code"),
    x_correlation_id: str = Header(None, alias="x-correlation-id", description="Correlation ID from autosuggest response (optional)"),
    db: Session = Depends(get_db),
    helper: HotelControllerHelper = Depends(get_hotel_controller_helper)
):
    """Get hotel pricing using the Xeni API and save room details to database."""
    return await helper.get_hotel_price_and_save(availability_token, currency, x_correlation_id, db)


@router.post("/book", tags=["Hotel Booking"])
async def book_hotel(
    request: BookHotelRequest,
    pricing_token: str = Query(..., description="Pricing token from pricing response"),
    x_correlation_id: str = Header(None, alias="x-correlation-id", description="Correlation ID from autosuggest response (optional)"),
    db: Session = Depends(get_db),
    helper: HotelControllerHelper = Depends(get_hotel_controller_helper)
):
    """Book hotel using the Xeni API with booking details and pricing token, and save to database."""
    return await helper.book_hotel(request, pricing_token, x_correlation_id, db)


@router.patch("/cancel/{booking_id}", tags=["Hotel Booking"])
async def cancel_booking(
    booking_id: str,
    request: CancelBookingRequest,
    x_correlation_id: str = Header(None, alias="x-correlation-id", description="Correlation ID from autosuggest response (optional)"),
    helper: HotelControllerHelper = Depends(get_hotel_controller_helper)
):
    """Cancel hotel booking using the Xeni API with booking ID and status."""
    return await helper.cancel_booking(booking_id, request, x_correlation_id)


