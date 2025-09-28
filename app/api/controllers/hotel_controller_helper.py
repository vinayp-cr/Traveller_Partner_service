from fastapi import HTTPException
from app.models.autosuggest_model import AutocompleteRequest, AutosuggestResponse, AutosuggestSuccessResponse, AutosuggestErrorResponse
from app.models.hotel_search_models import HotelSearchRequest, HotelSearchResponse, HotelDetailsResponse, AvailabilityRequest, AvailabilityResponse, PriceRequest, PriceResponse, BookHotelRequest, BookHotelResponse, CancelBookingRequest, CancelBookingResponse
from app.core.logger import logger
from sqlalchemy.orm import Session
from app.api.services.hotel_service import HotelService
from app.utilities.message_loader import message_loader
import uuid
import traceback


class HotelControllerHelper:
    """Helper class containing business logic for endpoints hotel operations."""
    
    def __init__(self, hotel_service: HotelService):
        self.hotel_service = hotel_service

    async def autocomplete(self, payload: AutocompleteRequest) -> AutosuggestResponse:
        """
        Get hotel autocomplete suggestions.
        Async implementation for better performance.
        
        Args:
            payload: AutocompleteRequest with search criteria
            
        Returns:
            AutosuggestResponse with hotel suggestions
        """
        try:
            logger.info(f"Processing autocomplete request for query: {payload.key}")
            
            # Get the API response asynchronously
            response_data = await self.hotel_service.get_hotel_autosuggestions_async(payload)
            
            logger.info(f"Autocomplete request completed successfully")
            return response_data
            
        except Exception as ex:
            logger.error(f"Autocomplete error: {str(ex)}")
            raise HTTPException(status_code=500, detail=str(ex))

    # New v2 API methods
    async def hotel_search(self, payload, x_correlation_id: str):
        """
        Search for hotels using the new v2 API.
        
        Args:
            payload: HotelSearchRequest with search criteria
            x_correlation_id: Correlation ID from autosuggest response
            
        Returns:
            HotelSearchResponse with search results
        """
        try:
            logger.info(f"Processing hotel search request with correlation ID: {x_correlation_id}")
            
            # Call the hotel service
            response = await self.hotel_service.search_hotels(payload, x_correlation_id)
            
            logger.info(f"Hotel search completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Hotel search error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error searching hotels: {str(e)}")

    async def hotel_search_and_save(self, payload: HotelSearchRequest, x_correlation_id: str, db: Session) -> HotelSearchResponse:
        """
        Search for hotels using the Xeni API and save results to database.
        
        Args:
            payload: HotelSearchRequest with search criteria
            x_correlation_id: Correlation ID from autosuggest response
            db: Database session
            
        Returns:
            HotelSearchResponse with search results
        """
        try:
            logger.info(f"Processing hotel search and save request for place: {payload.place_id}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Call the service method to search and save
            result = await self.hotel_service.search_hotels_and_save(payload, x_correlation_id, db)
            
            logger.info(f"Hotel search and save completed successfully. Found {len(result.get('data', {}).get('hotels', []))} hotels")
            return result
            
        except Exception as e:
            logger.error(f"Error in hotel search and save: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def get_hotel_details(self, property_id: str, x_correlation_id: str):
        """
        Get hotel details using the new v2 API.
        
        Args:
            property_id: Hotel property ID
            x_correlation_id: Correlation ID from autosuggest response
            
        Returns:
            HotelDetailsResponse with hotel details
        """
        try:
            logger.info(f"Processing hotel details request for property: {property_id}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Call the hotel service
            response = await self.hotel_service.get_hotel_details(property_id, x_correlation_id)
            
            logger.info(f"Hotel details request completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Hotel details error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error getting hotel details: {str(e)}")

    async def check_hotel_availability(self, request: AvailabilityRequest, x_correlation_id: str):
        """
        Check hotel availability using the new v2 API.
        
        Args:
            request: AvailabilityRequest with search criteria
            x_correlation_id: Correlation ID from autosuggest response
            
        Returns:
            AvailabilityResponse with availability data
        """
        try:
            logger.info(f"Processing hotel availability request for property: {request.property_id}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Call the hotel service
            response = await self.hotel_service.check_hotel_availability(request, x_correlation_id)
            
            logger.info(f"Hotel availability request completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Hotel availability error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error checking hotel availability: {str(e)}")

    async def get_hotel_price(self, availability_token: str, currency: str = "USD", x_correlation_id: str = None):
        """
        Get hotel pricing using the new v2 API.
        
        Args:
            availability_token: Token from availability response
            currency: Currency code (default: USD)
            x_correlation_id: Correlation ID from autosuggest response
            
        Returns:
            PriceResponse with pricing data
        """
        try:
            logger.info(f"Processing hotel pricing request for token: {availability_token}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Call the hotel service
            response = await self.hotel_service.get_hotel_price(availability_token, currency, x_correlation_id)
            
            logger.info(f"Hotel pricing request completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Hotel pricing error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error getting hotel pricing: {str(e)}")

    async def get_hotel_price_and_save(self, availability_token: str, currency: str = "USD", x_correlation_id: str = None, db: Session = None):
        """
        Get hotel pricing using the Xeni API and save room details to database.
        
        Args:
            availability_token: Token from availability response
            currency: Currency code (default: USD)
            x_correlation_id: Correlation ID from autosuggest response
            db: Database session
            
        Returns:
            PriceResponse with pricing data
        """
        try:
            logger.info(f"Processing hotel pricing and save request for token: {availability_token}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Call the service method to get price and save
            response = await self.hotel_service.get_hotel_price_and_save(availability_token, currency, x_correlation_id, db)
            
            logger.info(f"Hotel pricing and save request completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Hotel pricing and save error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error getting hotel pricing and saving: {str(e)}")

    async def book_hotel(self, request: BookHotelRequest, pricing_token: str, x_correlation_id: str = None, db: Session = None):
        """
        Book hotel using the new v2 API and save to database.
        
        Args:
            request: BookHotelRequest with booking details
            pricing_token: Token from pricing response
            x_correlation_id: Correlation ID from autosuggest response
            db: Database session (optional)
            
        Returns:
            BookHotelResponse with booking confirmation and database details
        """
        try:
            logger.info(f"Processing hotel booking request with pricing token: {pricing_token}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Call the hotel service with database session
            response = await self.hotel_service.book_hotel(request, pricing_token, x_correlation_id, db)
            
            logger.info(f"Hotel booking request completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Hotel booking error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error booking hotel: {str(e)}")

    async def cancel_booking(self, booking_id: str, request: CancelBookingRequest, x_correlation_id: str = None):
        """
        Cancel hotel booking using the new v2 API.
        
        Args:
            booking_id: Booking ID to cancel
            request: CancelBookingRequest with cancellation details
            x_correlation_id: Correlation ID from autosuggest response
            
        Returns:
            CancelBookingResponse with cancellation confirmation
        """
        try:
            logger.info(f"Processing hotel booking cancellation for booking ID: {booking_id}")
            logger.info(f"Using correlation ID: {x_correlation_id}")
            
            # Call the hotel service
            response = await self.hotel_service.cancel_booking(booking_id, request, x_correlation_id)
            
            logger.info(f"Hotel booking cancellation completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Hotel booking cancellation error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error cancelling hotel booking: {str(e)}")