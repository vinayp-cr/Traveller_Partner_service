"""
Hotel Integration Service
Integrates chatbot with existing hotel APIs
"""

from typing import Dict, Any, List, Optional
from app.api.services.hotel_service import HotelService
from app.models.hotel_search_models import HotelSearchRequest, BookHotelRequest, RoomGuest, PhoneData
from app.core.logger import logger


class HotelIntegrationService:
    """Service for integrating chatbot with hotel APIs"""
    
    def __init__(self):
        self.hotel_service = HotelService()
    
    async def search_hotels_via_chat(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search hotels using natural language criteria
        
        Args:
            criteria: Search criteria extracted from chat
            
        Returns:
            Hotel search results formatted for chat
        """
        try:
            # Convert chat criteria to hotel search request
            search_request = self._build_search_request(criteria)
            
            # Call existing hotel search API
            search_response = await self.hotel_service.search_hotels(search_request)
            
            # Format response for chat
            return self._format_search_results(search_response)
            
        except Exception as e:
            logger.error(f"Error searching hotels via chat: {str(e)}")
            return {
                'success': False,
                'message': 'Sorry, I encountered an error while searching for hotels.',
                'hotels': []
            }
    
    def _build_search_request(self, criteria: Dict[str, Any]) -> HotelSearchRequest:
        """Build hotel search request from chat criteria"""
        try:
            # Extract location
            location = criteria.get('location', 'New York')
            lat, lng = self._get_coordinates(location)
            
            # Extract dates
            dates = criteria.get('dates', {})
            checkin_date = dates.get('checkin', '2024-12-15')
            checkout_date = dates.get('checkout', '2024-12-17')
            
            # Extract guests
            guests = criteria.get('guests', {'adults': 2, 'children': 0, 'rooms': 1})
            
            # Build search request
            search_request = HotelSearchRequest(
                checkInDate=checkin_date,
                checkOutDate=checkout_date,
                lat=lat,
                lng=lng,
                nationality="US",
                type="leisure",
                occupancies=[{
                    "noOfRoom": guests.get('rooms', 1),
                    "adults": guests.get('adults', 2),
                    "children": guests.get('children', 0)
                }],
                currency="USD"
            )
            
            return search_request
            
        except Exception as e:
            logger.error(f"Error building search request: {str(e)}")
            # Return default search request
            return HotelSearchRequest(
                checkInDate="2024-12-15",
                checkOutDate="2024-12-17",
                lat=40.7128,
                lng=-74.0060,
                nationality="US",
                type="leisure",
                occupancies=[{"noOfRoom": 1, "adults": 2, "children": 0}],
                currency="USD"
            )
    
    def _get_coordinates(self, location: str) -> tuple[float, float]:
        """Get coordinates for location (simplified)"""
        # This is a simplified coordinate lookup
        # In production, you'd use a geocoding service
        location_coords = {
            'new york': (40.7128, -74.0060),
            'nyc': (40.7128, -74.0060),
            'manhattan': (40.7831, -73.9712),
            'brooklyn': (40.6782, -73.9442),
            'queens': (40.7282, -73.7949),
            'bronx': (40.8448, -73.8648),
            'times square': (40.7580, -73.9855),
            'central park': (40.7829, -73.9654),
            'wall street': (40.7074, -74.0113),
            'soho': (40.7231, -74.0026),
            'chelsea': (40.7505, -74.0014)
        }
        
        location_lower = location.lower().strip()
        return location_coords.get(location_lower, (40.7128, -74.0060))
    
    def _format_search_results(self, search_response: Dict[str, Any]) -> Dict[str, Any]:
        """Format hotel search results for chat display"""
        try:
            if not search_response.get('success', False):
                return {
                    'success': False,
                    'message': 'No hotels found matching your criteria.',
                    'hotels': []
                }
            
            hotels = search_response.get('data', {}).get('hotels', [])
            
            # Format hotels for chat
            formatted_hotels = []
            for hotel in hotels[:5]:  # Limit to top 5 results
                formatted_hotel = {
                    'id': hotel.get('id'),
                    'name': hotel.get('name'),
                    'address': hotel.get('address'),
                    'rating': hotel.get('rating'),
                    'price': hotel.get('price'),
                    'currency': hotel.get('currency', 'USD'),
                    'amenities': hotel.get('amenities', []),
                    'images': hotel.get('images', []),
                    'description': hotel.get('description', ''),
                    'availability': hotel.get('availability', True)
                }
                formatted_hotels.append(formatted_hotel)
            
            return {
                'success': True,
                'message': f'Found {len(formatted_hotels)} hotels for you!',
                'hotels': formatted_hotels,
                'total_count': len(hotels)
            }
            
        except Exception as e:
            logger.error(f"Error formatting search results: {str(e)}")
            return {
                'success': False,
                'message': 'Error processing hotel search results.',
                'hotels': []
            }
    
    async def apply_filters(self, hotels: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply filters to hotel results
        
        Args:
            hotels: List of hotels
            filters: Filter criteria
            
        Returns:
            Filtered hotel list
        """
        try:
            filtered_hotels = hotels.copy()
            
            # Filter by amenities
            if 'amenities' in filters:
                required_amenities = filters['amenities']
                filtered_hotels = [
                    hotel for hotel in filtered_hotels
                    if any(amenity in hotel.get('amenities', []) for amenity in required_amenities)
                ]
            
            # Filter by price range
            if 'price_range' in filters:
                price_range = filters['price_range']
                min_price = price_range.get('min', 0)
                max_price = price_range.get('max', float('inf'))
                
                filtered_hotels = [
                    hotel for hotel in filtered_hotels
                    if min_price <= hotel.get('price', 0) <= max_price
                ]
            
            # Filter by rating
            if 'min_rating' in filters:
                min_rating = filters['min_rating']
                filtered_hotels = [
                    hotel for hotel in filtered_hotels
                    if hotel.get('rating', 0) >= min_rating
                ]
            
            return filtered_hotels
            
        except Exception as e:
            logger.error(f"Error applying filters: {str(e)}")
            return hotels
    
    async def book_hotel_via_chat(self, hotel_id: str, booking_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Book hotel via chat
        
        Args:
            hotel_id: Hotel ID to book
            booking_details: Booking details from chat
            
        Returns:
            Booking result
        """
        try:
            # Build booking request
            booking_request = BookHotelRequest(
                booking_id=f"CHAT_{hotel_id}_{booking_details.get('booking_id', 'UNKNOWN')}",
                rooms=[
                    RoomGuest(
                        title=booking_details.get('title', 'Mr'),
                        first_name=booking_details.get('first_name', 'Guest'),
                        last_name=booking_details.get('last_name', 'User')
                    )
                ],
                email=booking_details.get('email', 'guest@example.com'),
                phone=PhoneData(
                    country_code=booking_details.get('country_code', '1'),
                    number=booking_details.get('phone_number', '0000000000')
                )
            )
            
            # Get pricing token (this would need to be passed from the search results)
            pricing_token = booking_details.get('pricing_token', '')
            
            # Call existing booking API
            booking_response = await self.hotel_service.book_hotel(
                request=booking_request,
                pricing_token=pricing_token
            )
            
            # Format response for chat
            return self._format_booking_result(booking_response)
            
        except Exception as e:
            logger.error(f"Error booking hotel via chat: {str(e)}")
            return {
                'success': False,
                'message': 'Sorry, I encountered an error while booking the hotel.',
                'booking_id': None
            }
    
    def _format_booking_result(self, booking_response: Dict[str, Any]) -> Dict[str, Any]:
        """Format booking result for chat"""
        try:
            if booking_response.get('status') == 'success':
                return {
                    'success': True,
                    'message': 'Hotel booked successfully!',
                    'booking_id': booking_response.get('data', {}).get('booking_id'),
                    'confirmation': booking_response.get('data', {}).get('booking_status'),
                    'details': booking_response.get('data', {})
                }
            else:
                return {
                    'success': False,
                    'message': 'Booking failed. Please try again.',
                    'booking_id': None,
                    'error': booking_response.get('message', 'Unknown error')
                }
                
        except Exception as e:
            logger.error(f"Error formatting booking result: {str(e)}")
            return {
                'success': False,
                'message': 'Error processing booking result.',
                'booking_id': None
            }
    
    async def cancel_booking_via_chat(self, booking_id: str) -> Dict[str, Any]:
        """
        Cancel booking via chat
        
        Args:
            booking_id: Booking ID to cancel
            
        Returns:
            Cancellation result
        """
        try:
            # Call existing cancellation API
            cancel_response = await self.hotel_service.cancel_booking(
                booking_id=booking_id,
                request={'booking_status': 'CANCELLED'}
            )
            
            # Format response for chat
            return self._format_cancellation_result(cancel_response)
            
        except Exception as e:
            logger.error(f"Error canceling booking via chat: {str(e)}")
            return {
                'success': False,
                'message': 'Sorry, I encountered an error while canceling the booking.',
                'booking_id': booking_id
            }
    
    def _format_cancellation_result(self, cancel_response: Dict[str, Any]) -> Dict[str, Any]:
        """Format cancellation result for chat"""
        try:
            if cancel_response.get('status') == 'success':
                return {
                    'success': True,
                    'message': 'Booking canceled successfully!',
                    'booking_id': cancel_response.get('booking_id'),
                    'refund_info': cancel_response.get('refund_info', {})
                }
            else:
                return {
                    'success': False,
                    'message': 'Cancellation failed. Please contact support.',
                    'booking_id': cancel_response.get('booking_id'),
                    'error': cancel_response.get('message', 'Unknown error')
                }
                
        except Exception as e:
            logger.error(f"Error formatting cancellation result: {str(e)}")
            return {
                'success': False,
                'message': 'Error processing cancellation result.',
                'booking_id': None
            }
