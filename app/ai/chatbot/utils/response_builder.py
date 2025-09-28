"""
Response Builder
Helper functions for building chatbot responses
"""

from typing import List, Dict, Any, Optional
from app.core.logger import logger


class ResponseBuilder:
    """Utility class for building chatbot responses"""
    
    @staticmethod
    def build_greeting_response() -> Dict[str, Any]:
        """Build greeting response"""
        return {
            'message': "Hello! I'm your travel assistant. I can help you find and book hotels. Where would you like to stay?",
            'suggestions': ["New York", "Los Angeles", "Chicago", "Miami"],
            'requires_input': True,
            'next_step': 'location'
        }
    
    @staticmethod
    def build_location_request_response() -> Dict[str, Any]:
        """Build location request response"""
        return {
            'message': "I'd be happy to help you find a hotel! Which city or location are you interested in?",
            'suggestions': ["New York", "Los Angeles", "Chicago", "Miami", "Boston", "Seattle"],
            'requires_input': True,
            'next_step': 'location'
        }
    
    @staticmethod
    def build_dates_request_response(location: str) -> Dict[str, Any]:
        """Build dates request response"""
        return {
            'message': f"Perfect! I'll search for hotels in {location}. When would you like to check in and check out?",
            'suggestions': ["This weekend", "Next week", "December 15-17", "January 1-3", "Next month"],
            'requires_input': True,
            'next_step': 'dates'
        }
    
    @staticmethod
    def build_guests_request_response(location: str, dates: Dict[str, str]) -> Dict[str, Any]:
        """Build guests request response"""
        checkin = dates.get('checkin', 'N/A')
        checkout = dates.get('checkout', 'N/A')
        
        return {
            'message': f"Great! I have your dates: {checkin} to {checkout}. How many guests and rooms do you need?",
            'suggestions': ["2 adults, 1 room", "Family of 4", "1 adult, 1 room", "Group of 6", "2 adults, 2 children"],
            'requires_input': True,
            'next_step': 'guests'
        }
    
    @staticmethod
    def build_hotel_search_response(hotels: List[Dict[str, Any]], total_count: int) -> Dict[str, Any]:
        """Build hotel search response"""
        if not hotels:
            return {
                'message': "I'm sorry, I couldn't find any hotels matching your criteria. Please try a different location or dates.",
                'suggestions': ["Try different dates", "Change location", "Remove filters"],
                'requires_input': True,
                'next_step': 'location'
            }
        
        hotel_list = ResponseBuilder._format_hotel_list(hotels)
        
        return {
            'message': f"Great! I found {len(hotels)} hotels for you:\n\n{hotel_list}\n\nWould you like to book any of these hotels or apply any filters?",
            'suggestions': ["Book Hotel 1", "Show me cheaper options", "Filter by amenities", "Show more details"],
            'requires_input': True,
            'next_step': 'booking',
            'hotel_data': {'hotels': hotels, 'total_count': total_count}
        }
    
    @staticmethod
    def build_booking_success_response(booking_data: Dict[str, Any], hotel_name: str) -> Dict[str, Any]:
        """Build booking success response"""
        booking_id = booking_data.get('booking_id', 'N/A')
        status = booking_data.get('confirmation', 'Confirmed')
        
        return {
            'message': f"Congratulations! Your hotel has been booked successfully!\n\n"
                      f"Booking ID: {booking_id}\n"
                      f"Hotel: {hotel_name}\n"
                      f"Status: {status}\n\n"
                      f"Is there anything else I can help you with?",
            'suggestions': ["Book another hotel", "Cancel this booking", "Get booking details"],
            'requires_input': True,
            'next_step': 'completed',
            'booking_data': booking_data
        }
    
    @staticmethod
    def build_booking_failure_response(error_message: str) -> Dict[str, Any]:
        """Build booking failure response"""
        return {
            'message': f"Sorry, I couldn't complete the booking. {error_message}\n\nWould you like to try again or select a different hotel?",
            'suggestions': ["Try again", "Select different hotel", "Start over"],
            'requires_input': True,
            'next_step': 'booking'
        }
    
    @staticmethod
    def build_cancellation_success_response(booking_id: str) -> Dict[str, Any]:
        """Build cancellation success response"""
        return {
            'message': f"Your booking has been canceled successfully!\n\nBooking ID: {booking_id}\n\nIs there anything else I can help you with?",
            'suggestions': ["Book a new hotel", "Search for hotels", "Start over"],
            'requires_input': True,
            'next_step': 'completed'
        }
    
    @staticmethod
    def build_cancellation_failure_response(error_message: str) -> Dict[str, Any]:
        """Build cancellation failure response"""
        return {
            'message': f"Sorry, I couldn't cancel the booking. {error_message}\n\nPlease contact support for assistance.",
            'requires_input': True
        }
    
    @staticmethod
    def build_filter_response(filtered_hotels: List[Dict[str, Any]], filter_type: str) -> Dict[str, Any]:
        """Build filter response"""
        if not filtered_hotels:
            return {
                'message': f"I couldn't find any hotels matching those {filter_type} filters. Would you like to see all available hotels?",
                'suggestions': ["Show all hotels", "Try different filters", "Remove filters"],
                'requires_input': True,
                'next_step': 'booking'
            }
        
        hotel_list = ResponseBuilder._format_hotel_list(filtered_hotels)
        
        return {
            'message': f"Here are hotels with {filter_type}:\n\n{hotel_list}\n\nWould you like to book any of these?",
            'suggestions': ["Book Hotel 1", "Show me more options", "Remove filters"],
            'requires_input': True,
            'next_step': 'booking',
            'hotel_data': {'hotels': filtered_hotels}
        }
    
    @staticmethod
    def build_help_response() -> Dict[str, Any]:
        """Build help response"""
        return {
            'message': "I'm here to help you find and book hotels! Here's what I can do:\n\n"
                      "• Search for hotels by location\n"
                      "• Filter by amenities (breakfast, wifi, pool, etc.)\n"
                      "• Filter by price range\n"
                      "• Book hotels\n"
                      "• Cancel bookings\n\n"
                      "Just tell me where you'd like to stay and I'll help you find the perfect hotel!",
            'suggestions': ["Search for hotels", "Book a hotel", "Cancel booking"],
            'requires_input': True,
            'next_step': 'location'
        }
    
    @staticmethod
    def build_error_response(error_message: str) -> Dict[str, Any]:
        """Build error response"""
        return {
            'message': f"I'm sorry, I encountered an error: {error_message}. Please try again.",
            'suggestions': ["Try again", "Start over", "Get help"],
            'requires_input': True
        }
    
    @staticmethod
    def build_unknown_intent_response() -> Dict[str, Any]:
        """Build unknown intent response"""
        return {
            'message': "I'm not sure I understand. I can help you with:\n\n"
                      "• Finding hotels\n"
                      "• Booking hotels\n"
                      "• Filtering by amenities or price\n"
                      "• Canceling bookings\n\n"
                      "What would you like to do?",
            'suggestions': ["Search for hotels", "Book a hotel", "Get help"],
            'requires_input': True,
            'next_step': 'location'
        }
    
    @staticmethod
    def build_amenity_request_response() -> Dict[str, Any]:
        """Build amenity request response"""
        return {
            'message': "What amenities are you looking for? I can filter by breakfast, wifi, pool, gym, spa, and more.",
            'suggestions': ["Breakfast included", "Free wifi", "Swimming pool", "Fitness center", "Spa services"],
            'requires_input': True,
            'next_step': 'filtering'
        }
    
    @staticmethod
    def build_price_request_response() -> Dict[str, Any]:
        """Build price request response"""
        return {
            'message': "What's your budget range? I can filter hotels by price.",
            'suggestions': ["Under $100", "$100-$200", "$200-$300", "Over $300", "Best value"],
            'requires_input': True,
            'next_step': 'filtering'
        }
    
    @staticmethod
    def _format_hotel_list(hotels: List[Dict[str, Any]]) -> str:
        """Format hotel list for display"""
        try:
            if not hotels:
                return "No hotels found."
            
            formatted_list = []
            for i, hotel in enumerate(hotels[:5], 1):  # Limit to top 5
                price = hotel.get('price', 'N/A')
                currency = hotel.get('currency', 'USD')
                rating = hotel.get('rating', 'N/A')
                
                formatted_hotel = f"{i}. **{hotel.get('name', 'Unknown Hotel')}**\n"
                formatted_hotel += f"   Address: {hotel.get('address', 'N/A')}\n"
                formatted_hotel += f"   Price: ${price} {currency}\n"
                formatted_hotel += f"   Rating: {rating}/5\n"
                
                amenities = hotel.get('amenities', [])
                if amenities:
                    formatted_hotel += f"   Amenities: {', '.join(amenities[:3])}\n"
                
                formatted_list.append(formatted_hotel)
            
            return "\n".join(formatted_list)
            
        except Exception as e:
            logger.error(f"Error formatting hotel list: {str(e)}")
            return "Error displaying hotels."
    
    @staticmethod
    def build_suggestions_for_state(state: str) -> List[str]:
        """Build suggestions based on conversation state"""
        suggestions_map = {
            'greeting': ["Search for hotels", "Book a hotel", "Get help"],
            'location': ["New York", "Los Angeles", "Chicago", "Miami"],
            'dates': ["This weekend", "Next week", "December 15-17", "January 1-3"],
            'guests': ["2 adults, 1 room", "Family of 4", "1 adult, 1 room", "Group of 6"],
            'showing_results': ["Book Hotel 1", "Show me cheaper options", "Filter by amenities"],
            'filtering': ["Breakfast included", "Free wifi", "Swimming pool", "Under $200"],
            'booking': ["Yes, book it", "No, show me more", "Cancel booking"],
            'completed': ["Book another hotel", "Search for hotels", "Start over"]
        }
        
        return suggestions_map.get(state, ["Continue", "Help", "Start over"])
    
    @staticmethod
    def build_contextual_response(state: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build contextual response based on state and context"""
        try:
            if state == 'greeting':
                return ResponseBuilder.build_greeting_response()
            elif state == 'location':
                return ResponseBuilder.build_location_request_response()
            elif state == 'dates':
                location = context.get('search_criteria', {}).get('location', 'your chosen location')
                return ResponseBuilder.build_dates_request_response(location)
            elif state == 'guests':
                location = context.get('search_criteria', {}).get('location', 'your chosen location')
                dates = context.get('search_criteria', {}).get('dates', {})
                return ResponseBuilder.build_guests_request_response(location, dates)
            elif state == 'showing_results':
                hotels = context.get('selected_hotels', [])
                return ResponseBuilder.build_hotel_search_response(hotels, len(hotels))
            elif state == 'filtering':
                return ResponseBuilder.build_amenity_request_response()
            elif state == 'booking':
                return ResponseBuilder.build_booking_success_response({}, "Selected Hotel")
            else:
                return ResponseBuilder.build_unknown_intent_response()
                
        except Exception as e:
            logger.error(f"Error building contextual response: {str(e)}")
            return ResponseBuilder.build_error_response("Unable to process request")
