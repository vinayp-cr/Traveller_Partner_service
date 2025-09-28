"""
Chat Service
Main service for processing chat messages and managing conversation flow
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from app.ai.chatbot.models.intent_models import Intent, ChatResponse, ConversationState
from app.ai.chatbot.services.intent_service import IntentService
from app.ai.chatbot.services.hotel_integration_service import HotelIntegrationService
from app.ai.chatbot.repositories.chat_repository import ChatRepository
from app.core.logger import logger


class ChatService:
    """Main service for chat processing and conversation management"""
    
    def __init__(self):
        self.intent_service = IntentService()
        self.hotel_service = HotelIntegrationService()
        self.chat_repository = ChatRepository()
    
    async def process_message(self, session_id: str, user_message: str, user_id: Optional[str] = None) -> ChatResponse:
        """
        Process user message and generate bot response
        
        Args:
            session_id: Chat session ID
            user_message: User's message
            user_id: Optional user ID
            
        Returns:
            Chat response
        """
        try:
            # Get or create chat session
            session = await self.chat_repository.get_or_create_session(session_id, user_id)
            
            # Save user message
            await self.chat_repository.save_message(
                session_id=session_id,
                message_type="user",
                content=user_message
            )
            
            # Recognize intent
            intent = self.intent_service.recognize_intent(user_message)
            
            # Get conversation state
            context = await self.chat_repository.get_booking_context(session_id)
            current_state = self._determine_conversation_state(intent, context)
            
            # Process based on intent and state
            response = await self._process_intent(intent, current_state, context, session_id)
            
            # Save bot response
            await self.chat_repository.save_message(
                session_id=session_id,
                message_type="bot",
                content=response.message,
                intent=intent.type,
                entities=intent.entities
            )
            
            # Update booking context
            await self._update_booking_context(session_id, intent, response, context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return ChatResponse(
                message="Sorry, I encountered an error. Please try again.",
                requires_input=True
            )
    
    def _determine_conversation_state(self, intent: Intent, context: Optional[Dict[str, Any]]) -> ConversationState:
        """Determine current conversation state"""
        try:
            if not context:
                return ConversationState.GREETING
            
            current_step = context.get('current_step')
            if current_step:
                return ConversationState(current_step)
            
            # Determine state based on available information
            search_criteria = context.get('search_criteria', {})
            
            if not search_criteria.get('location'):
                return ConversationState.LOCATION_NEEDED
            elif not search_criteria.get('dates'):
                return ConversationState.DATES_NEEDED
            elif not search_criteria.get('guests'):
                return ConversationState.GUESTS_NEEDED
            elif search_criteria and not context.get('selected_hotels'):
                return ConversationState.SHOWING_RESULTS
            else:
                return ConversationState.BOOKING
                
        except Exception as e:
            logger.error(f"Error determining conversation state: {str(e)}")
            return ConversationState.GREETING
    
    async def _process_intent(self, intent: Intent, state: ConversationState, context: Optional[Dict[str, Any]], session_id: str) -> ChatResponse:
        """Process intent based on current conversation state"""
        try:
            if intent.type == "greeting":
                return await self._handle_greeting()
            elif intent.type == "hotel_search":
                return await self._handle_hotel_search(intent, state, context, session_id)
            elif intent.type == "location":
                return await self._handle_location(intent, state, context, session_id)
            elif intent.type == "dates":
                return await self._handle_dates(intent, state, context, session_id)
            elif intent.type == "guests":
                return await self._handle_guests(intent, state, context, session_id)
            elif intent.type == "amenities":
                return await self._handle_amenities(intent, state, context, session_id)
            elif intent.type == "price":
                return await self._handle_price(intent, state, context, session_id)
            elif intent.type == "filter":
                return await self._handle_filter(intent, state, context, session_id)
            elif intent.type == "booking":
                return await self._handle_booking(intent, state, context, session_id)
            elif intent.type == "cancel":
                return await self._handle_cancel(intent, state, context, session_id)
            elif intent.type == "help":
                return await self._handle_help()
            else:
                return await self._handle_unknown(intent, state, context)
                
        except Exception as e:
            logger.error(f"Error processing intent: {str(e)}")
            return ChatResponse(
                message="I'm sorry, I didn't understand that. Could you please rephrase?",
                requires_input=True
            )
    
    async def _handle_greeting(self) -> ChatResponse:
        """Handle greeting intent"""
        return ChatResponse(
            message="Hello! I'm your travel assistant. I can help you find and book hotels. Where would you like to stay?",
            suggestions=["New York", "Los Angeles", "Chicago", "Miami"],
            requires_input=True,
            next_step="location"
        )
    
    async def _handle_hotel_search(self, intent: Intent, state: ConversationState, context: Optional[Dict[str, Any]], session_id: str) -> ChatResponse:
        """Handle hotel search intent"""
        try:
            # Extract search criteria
            criteria = self.intent_service.extract_search_criteria(intent)
            
            # Update context with new criteria
            if context:
                context['search_criteria'].update(criteria)
            else:
                context = {'search_criteria': criteria}
            
            # Check if we have enough information to search
            if not criteria.get('location'):
                return ChatResponse(
                    message="I'd be happy to help you find a hotel! Which city or location are you interested in?",
                    requires_input=True,
                    next_step="location"
                )
            
            # Search for hotels
            search_results = await self.hotel_service.search_hotels_via_chat(criteria)
            
            if search_results['success']:
                # Update context with search results
                context['selected_hotels'] = search_results['hotels']
                context['current_step'] = 'showing_results'
                
                # Format hotel list for display
                hotel_list = self._format_hotel_list(search_results['hotels'])
                
                return ChatResponse(
                    message=f"Great! I found {len(search_results['hotels'])} hotels for you:\n\n{hotel_list}\n\nWould you like to book any of these hotels or apply any filters?",
                    hotel_data=search_results,
                    suggestions=["Book Hotel 1", "Show me cheaper options", "Filter by amenities", "Show more details"],
                    requires_input=True,
                    next_step="booking"
                )
            else:
                return ChatResponse(
                    message="I'm sorry, I couldn't find any hotels matching your criteria. Please try a different location or dates.",
                    requires_input=True,
                    next_step="location"
                )
                
        except Exception as e:
            logger.error(f"Error handling hotel search: {str(e)}")
            return ChatResponse(
                message="I encountered an error while searching for hotels. Please try again.",
                requires_input=True
            )
    
    async def _handle_location(self, intent: Intent, state: ConversationState, context: Optional[Dict[str, Any]], session_id: str) -> ChatResponse:
        """Handle location intent"""
        try:
            criteria = self.intent_service.extract_search_criteria(intent)
            location = criteria.get('location')
            
            if location:
                # Update context with location
                if context:
                    context['search_criteria']['location'] = location
                else:
                    context = {'search_criteria': {'location': location}}
                
                return ChatResponse(
                    message=f"Perfect! I'll search for hotels in {location}. When would you like to check in and check out?",
                    suggestions=["This weekend", "Next week", "December 15-17", "January 1-3"],
                    requires_input=True,
                    next_step="dates"
                )
            else:
                return ChatResponse(
                    message="I'd be happy to help you find a hotel! Which city or location are you interested in?",
                    requires_input=True,
                    next_step="location"
                )
                
        except Exception as e:
            logger.error(f"Error handling location: {str(e)}")
            return ChatResponse(
                message="I didn't catch the location. Could you please tell me which city you'd like to stay in?",
                requires_input=True
            )
    
    async def _handle_dates(self, intent: Intent, state: ConversationState, context: Optional[Dict[str, Any]], session_id: str) -> ChatResponse:
        """Handle dates intent"""
        try:
            criteria = self.intent_service.extract_search_criteria(intent)
            dates = criteria.get('dates', {})
            
            if dates:
                # Update context with dates
                if context:
                    context['search_criteria']['dates'] = dates
                else:
                    context = {'search_criteria': {'dates': dates}}
                
                return ChatResponse(
                    message=f"Great! I have your dates: {dates.get('checkin')} to {dates.get('checkout')}. How many guests and rooms do you need?",
                    suggestions=["2 adults, 1 room", "Family of 4", "1 adult, 1 room", "Group of 6"],
                    requires_input=True,
                    next_step="guests"
                )
            else:
                return ChatResponse(
                    message="When would you like to check in and check out?",
                    requires_input=True,
                    next_step="dates"
                )
                
        except Exception as e:
            logger.error(f"Error handling dates: {str(e)}")
            return ChatResponse(
                message="I didn't catch the dates. Could you please tell me your check-in and check-out dates?",
                requires_input=True
            )
    
    async def _handle_guests(self, intent: Intent, state: ConversationState, context: Optional[Dict[str, Any]], session_id: str) -> ChatResponse:
        """Handle guests intent"""
        try:
            criteria = self.intent_service.extract_search_criteria(intent)
            guests = criteria.get('guests', {})
            
            if guests:
                # Update context with guest information
                if context:
                    context['search_criteria']['guests'] = guests
                else:
                    context = {'search_criteria': {'guests': guests}}
                
                # Now we have enough information to search
                search_results = await self.hotel_service.search_hotels_via_chat(context['search_criteria'])
                
                if search_results['success']:
                    context['selected_hotels'] = search_results['hotels']
                    context['current_step'] = 'showing_results'
                    
                    hotel_list = self._format_hotel_list(search_results['hotels'])
                    
                    return ChatResponse(
                        message=f"Perfect! I found {len(search_results['hotels'])} hotels for you:\n\n{hotel_list}\n\nWould you like to book any of these hotels?",
                        hotel_data=search_results,
                        suggestions=["Book Hotel 1", "Show me cheaper options", "Filter by amenities"],
                        requires_input=True,
                        next_step="booking"
                    )
                else:
                    return ChatResponse(
                        message="I'm sorry, I couldn't find any hotels matching your criteria. Please try different dates or location.",
                        requires_input=True,
                        next_step="location"
                    )
            else:
                return ChatResponse(
                    message="How many guests and rooms do you need?",
                    requires_input=True,
                    next_step="guests"
                )
                
        except Exception as e:
            logger.error(f"Error handling guests: {str(e)}")
            return ChatResponse(
                message="I didn't catch the guest information. Could you please tell me how many adults, children, and rooms you need?",
                requires_input=True
            )
    
    async def _handle_amenities(self, intent: Intent, state: ConversationState, context: Optional[Dict[str, Any]], session_id: str) -> ChatResponse:
        """Handle amenities intent"""
        try:
            criteria = self.intent_service.extract_search_criteria(intent)
            amenities = criteria.get('amenities', [])
            
            if amenities and context and context.get('selected_hotels'):
                # Apply amenity filter
                filtered_hotels = await self.hotel_service.apply_filters(
                    context['selected_hotels'],
                    {'amenities': amenities}
                )
                
                if filtered_hotels:
                    context['selected_hotels'] = filtered_hotels
                    hotel_list = self._format_hotel_list(filtered_hotels)
                    
                    return ChatResponse(
                        message=f"Here are hotels with {', '.join(amenities)}:\n\n{hotel_list}\n\nWould you like to book any of these?",
                        hotel_data={'hotels': filtered_hotels},
                        suggestions=["Book Hotel 1", "Show me more options", "Remove filters"],
                        requires_input=True,
                        next_step="booking"
                    )
                else:
                    return ChatResponse(
                        message=f"I couldn't find any hotels with {', '.join(amenities)}. Would you like to see all available hotels?",
                        suggestions=["Show all hotels", "Try different amenities", "Remove filters"],
                        requires_input=True,
                        next_step="booking"
                    )
            else:
                return ChatResponse(
                    message="What amenities are you looking for? I can filter by breakfast, wifi, pool, gym, spa, and more.",
                    suggestions=["Breakfast included", "Free wifi", "Swimming pool", "Fitness center"],
                    requires_input=True,
                    next_step="filtering"
                )
                
        except Exception as e:
            logger.error(f"Error handling amenities: {str(e)}")
            return ChatResponse(
                message="I encountered an error while filtering by amenities. Please try again.",
                requires_input=True
            )
    
    async def _handle_price(self, intent: Intent, state: ConversationState, context: Optional[Dict[str, Any]], session_id: str) -> ChatResponse:
        """Handle price intent"""
        try:
            criteria = self.intent_service.extract_search_criteria(intent)
            price_range = criteria.get('price_range', {})
            
            if price_range and context and context.get('selected_hotels'):
                # Apply price filter
                filtered_hotels = await self.hotel_service.apply_filters(
                    context['selected_hotels'],
                    {'price_range': price_range}
                )
                
                if filtered_hotels:
                    context['selected_hotels'] = filtered_hotels
                    hotel_list = self._format_hotel_list(filtered_hotels)
                    
                    return ChatResponse(
                        message=f"Here are hotels in your price range:\n\n{hotel_list}\n\nWould you like to book any of these?",
                        hotel_data={'hotels': filtered_hotels},
                        suggestions=["Book Hotel 1", "Show me more options", "Adjust price range"],
                        requires_input=True,
                        next_step="booking"
                    )
                else:
                    return ChatResponse(
                        message="I couldn't find any hotels in that price range. Would you like to see all available hotels?",
                        suggestions=["Show all hotels", "Try different price range", "Remove filters"],
                        requires_input=True,
                        next_step="booking"
                    )
            else:
                return ChatResponse(
                    message="What's your budget range? I can filter hotels by price.",
                    suggestions=["Under $100", "$100-$200", "$200-$300", "Over $300"],
                    requires_input=True,
                    next_step="filtering"
                )
                
        except Exception as e:
            logger.error(f"Error handling price: {str(e)}")
            return ChatResponse(
                message="I encountered an error while filtering by price. Please try again.",
                requires_input=True
            )
    
    async def _handle_filter(self, intent: Intent, state: ConversationState, context: Optional[Dict[str, Any]], session_id: str) -> ChatResponse:
        """Handle filter intent"""
        try:
            criteria = self.intent_service.extract_search_criteria(intent)
            
            if context and context.get('selected_hotels'):
                # Apply filters
                filtered_hotels = await self.hotel_service.apply_filters(
                    context['selected_hotels'],
                    criteria
                )
                
                if filtered_hotels:
                    context['selected_hotels'] = filtered_hotels
                    hotel_list = self._format_hotel_list(filtered_hotels)
                    
                    return ChatResponse(
                        message=f"Here are the filtered results:\n\n{hotel_list}\n\nWould you like to book any of these?",
                        hotel_data={'hotels': filtered_hotels},
                        suggestions=["Book Hotel 1", "Show me more options", "Remove filters"],
                        requires_input=True,
                        next_step="booking"
                    )
                else:
                    return ChatResponse(
                        message="I couldn't find any hotels matching those filters. Would you like to see all available hotels?",
                        suggestions=["Show all hotels", "Try different filters", "Remove filters"],
                        requires_input=True,
                        next_step="booking"
                    )
            else:
                return ChatResponse(
                    message="I need to search for hotels first. Where would you like to stay?",
                    requires_input=True,
                    next_step="location"
                )
                
        except Exception as e:
            logger.error(f"Error handling filter: {str(e)}")
            return ChatResponse(
                message="I encountered an error while applying filters. Please try again.",
                requires_input=True
            )
    
    async def _handle_booking(self, intent: Intent, state: ConversationState, context: Optional[Dict[str, Any]], session_id: str) -> ChatResponse:
        """Handle booking intent"""
        try:
            if not context or not context.get('selected_hotels'):
                return ChatResponse(
                    message="I need to search for hotels first. Where would you like to stay?",
                    requires_input=True,
                    next_step="location"
                )
            
            # For now, book the first hotel (in a real implementation, you'd let user select)
            hotel = context['selected_hotels'][0]
            
            # Build booking details (in a real implementation, you'd collect this from user)
            booking_details = {
                'hotel_id': hotel['id'],
                'booking_id': f"CHAT_{hotel['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'title': 'Mr',
                'first_name': 'Guest',
                'last_name': 'User',
                'email': 'guest@example.com',
                'country_code': '1',
                'phone_number': '0000000000',
                'pricing_token': hotel.get('pricing_token', '')
            }
            
            # Book hotel
            booking_result = await self.hotel_service.book_hotel_via_chat(
                hotel['id'],
                booking_details
            )
            
            if booking_result['success']:
                context['booking_id'] = booking_result['booking_id']
                context['current_step'] = 'completed'
                
                return ChatResponse(
                    message=f"Congratulations! Your hotel has been booked successfully!\n\nBooking ID: {booking_result['booking_id']}\nHotel: {hotel['name']}\nStatus: {booking_result['confirmation']}\n\nIs there anything else I can help you with?",
                    booking_data=booking_result,
                    suggestions=["Book another hotel", "Cancel this booking", "Get booking details"],
                    requires_input=True,
                    next_step="completed"
                )
            else:
                return ChatResponse(
                    message=f"Sorry, I couldn't complete the booking. {booking_result['message']}\n\nWould you like to try again or select a different hotel?",
                    suggestions=["Try again", "Select different hotel", "Start over"],
                    requires_input=True,
                    next_step="booking"
                )
                
        except Exception as e:
            logger.error(f"Error handling booking: {str(e)}")
            return ChatResponse(
                message="I encountered an error while booking the hotel. Please try again.",
                requires_input=True
            )
    
    async def _handle_cancel(self, intent: Intent, state: ConversationState, context: Optional[Dict[str, Any]], session_id: str) -> ChatResponse:
        """Handle cancel intent"""
        try:
            if not context or not context.get('booking_id'):
                return ChatResponse(
                    message="I don't see any active bookings to cancel. Would you like to search for a hotel?",
                    requires_input=True,
                    next_step="location"
                )
            
            # Cancel booking
            cancel_result = await self.hotel_service.cancel_booking_via_chat(
                context['booking_id']
            )
            
            if cancel_result['success']:
                context['booking_id'] = None
                context['current_step'] = 'completed'
                
                return ChatResponse(
                    message=f"Your booking has been canceled successfully!\n\nBooking ID: {cancel_result['booking_id']}\n\nIs there anything else I can help you with?",
                    suggestions=["Book a new hotel", "Search for hotels", "Start over"],
                    requires_input=True,
                    next_step="completed"
                )
            else:
                return ChatResponse(
                    message=f"Sorry, I couldn't cancel the booking. {cancel_result['message']}\n\nPlease contact support for assistance.",
                    requires_input=True
                )
                
        except Exception as e:
            logger.error(f"Error handling cancel: {str(e)}")
            return ChatResponse(
                message="I encountered an error while canceling the booking. Please try again.",
                requires_input=True
            )
    
    async def _handle_help(self) -> ChatResponse:
        """Handle help intent"""
        return ChatResponse(
            message="I'm here to help you find and book hotels! Here's what I can do:\n\n"
                   "• Search for hotels by location\n"
                   "• Filter by amenities (breakfast, wifi, pool, etc.)\n"
                   "• Filter by price range\n"
                   "• Book hotels\n"
                   "• Cancel bookings\n\n"
                   "Just tell me where you'd like to stay and I'll help you find the perfect hotel!",
            suggestions=["Search for hotels", "Book a hotel", "Cancel booking"],
            requires_input=True,
            next_step="location"
        )
    
    async def _handle_unknown(self, intent: Intent, state: ConversationState, context: Optional[Dict[str, Any]]) -> ChatResponse:
        """Handle unknown intent"""
        return ChatResponse(
            message="I'm not sure I understand. I can help you with:\n\n"
                   "• Finding hotels\n"
                   "• Booking hotels\n"
                   "• Filtering by amenities or price\n"
                   "• Canceling bookings\n\n"
                   "What would you like to do?",
            suggestions=["Search for hotels", "Book a hotel", "Get help"],
            requires_input=True,
            next_step="location"
        )
    
    def _format_hotel_list(self, hotels: List[Dict[str, Any]]) -> str:
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
    
    async def _update_booking_context(self, session_id: str, intent: Intent, response: ChatResponse, context: Optional[Dict[str, Any]]):
        """Update booking context with new information"""
        try:
            if not context:
                context = {'search_criteria': {}}
            
            # Update context based on response
            if response.hotel_data:
                context['selected_hotels'] = response.hotel_data.get('hotels', [])
            
            if response.booking_data:
                context['booking_id'] = response.booking_data.get('booking_id')
            
            if response.next_step:
                context['current_step'] = response.next_step
            
            # Save updated context
            await self.chat_repository.save_booking_context(session_id, context)
            
        except Exception as e:
            logger.error(f"Error updating booking context: {str(e)}")
