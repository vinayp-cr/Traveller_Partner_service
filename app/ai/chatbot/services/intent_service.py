"""
Intent Recognition Service
Basic NLP for intent detection and entity extraction
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.ai.chatbot.models.intent_models import Intent, Entity, IntentType, EntityType, ConversationState
from app.core.logger import logger


class IntentService:
    """Service for intent recognition and entity extraction"""
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
        self.amenity_keywords = self._load_amenity_keywords()
    
    def _load_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Load intent recognition patterns"""
        return {
            IntentType.GREETING: [
                r'\b(hello|hi|hey|start|begin)\b',
                r'\b(good morning|good afternoon|good evening)\b',
                r'\b(help|assist)\b'
            ],
            IntentType.HOTEL_SEARCH: [
                r'\b(hotel|hotels|accommodation|stay|book|reserve)\b',
                r'\b(find|search|look for|need)\b.*\b(hotel|place to stay)\b',
                r'\b(where|where can|where should)\b.*\b(stay|sleep)\b'
            ],
            IntentType.LOCATION: [
                r'\b(in|at|near|around|close to)\b',
                r'\b(location|place|city|area|neighborhood)\b',
                r'\b(manhattan|brooklyn|queens|bronx|staten island)\b',
                r'\b(times square|central park|wall street|soho|chelsea)\b'
            ],
            IntentType.DATES: [
                r'\b(check.?in|check.?out|arrival|departure|dates)\b',
                r'\b(tomorrow|today|yesterday|next week|this weekend)\b',
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b'
            ],
            IntentType.GUESTS: [
                r'\b(adults|children|guests|people|rooms|room)\b',
                r'\b(how many|number of|count)\b',
                r'\b(family|couple|single|group)\b'
            ],
            IntentType.AMENITIES: [
                r'\b(breakfast|wifi|internet|pool|gym|fitness|spa|parking)\b',
                r'\b(restaurant|bar|room service|concierge)\b',
                r'\b(air conditioning|heating|balcony|ocean view)\b'
            ],
            IntentType.PRICE: [
                r'\b(price|cost|rate|cheap|expensive|budget|affordable)\b',
                r'\b(under|below|less than|more than|above)\b.*\b(\$|dollar|dollars)\b',
                r'\b(best price|lowest|highest|range)\b'
            ],
            IntentType.FILTER: [
                r'\b(filter|show|only|with|nearby|near)\b',
                r'\b(beach|ocean|downtown|airport|station)\b',
                r'\b(4 star|5 star|luxury|budget|boutique)\b'
            ],
            IntentType.BOOKING: [
                r'\b(book|reserve|confirm|select|choose|take)\b',
                r'\b(i want|i need|i\'ll take|i\'ll book)\b',
                r'\b(yes|confirm|proceed|go ahead)\b'
            ],
            IntentType.CANCEL: [
                r'\b(cancel|refund|change|modify|update)\b',
                r'\b(no|don\'t want|not interested)\b'
            ],
            IntentType.HELP: [
                r'\b(help|what|how|options|available)\b',
                r'\b(what can|what do|show me)\b'
            ]
        }
    
    def _load_entity_patterns(self) -> Dict[EntityType, List[str]]:
        """Load entity extraction patterns"""
        return {
            EntityType.LOCATION: [
                r'\b(new york|nyc|manhattan|brooklyn|queens|bronx|staten island)\b',
                r'\b(times square|central park|wall street|soho|chelsea|greenwich)\b',
                r'\b(beach|ocean|downtown|uptown|midtown|east side|west side)\b'
            ],
            EntityType.DATE: [
                r'\b(today|tomorrow|yesterday|next week|this weekend)\b',
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b'
            ],
            EntityType.NUMBER: [
                r'\b(\d+)\b.*\b(adults|children|guests|people|rooms|room)\b',
                r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\b',
                r'\b(\d+)\b'
            ],
            EntityType.AMENITY: [
                r'\b(breakfast|wifi|internet|pool|gym|fitness|spa|parking)\b',
                r'\b(restaurant|bar|room service|concierge|valet)\b',
                r'\b(air conditioning|heating|balcony|ocean view|city view)\b'
            ],
            EntityType.PRICE_RANGE: [
                r'\b(under|below|less than|more than|above)\b.*\b(\$|dollar|dollars)\b',
                r'\b(\$?\d+)\b.*\b(to|and|-\s*)\b.*\b(\$?\d+)\b',
                r'\b(cheap|budget|affordable|expensive|luxury|premium)\b'
            ],
            EntityType.HOTEL_NAME: [
                r'\b(marriott|hilton|hyatt|sheraton|westin|radisson)\b',
                r'\b(ritz|four seasons|mandarin|peninsula|shangri-la)\b'
            ]
        }
    
    def _load_amenity_keywords(self) -> Dict[str, List[str]]:
        """Load amenity keywords for better matching"""
        return {
            'breakfast': ['breakfast', 'continental breakfast', 'free breakfast', 'complimentary breakfast'],
            'wifi': ['wifi', 'internet', 'wireless', 'free wifi', 'complimentary wifi'],
            'pool': ['pool', 'swimming pool', 'outdoor pool', 'indoor pool'],
            'gym': ['gym', 'fitness', 'fitness center', 'workout', 'exercise'],
            'spa': ['spa', 'massage', 'wellness', 'relaxation'],
            'parking': ['parking', 'valet', 'free parking', 'complimentary parking'],
            'restaurant': ['restaurant', 'dining', 'food', 'meal'],
            'bar': ['bar', 'lounge', 'cocktail', 'drinks'],
            'room_service': ['room service', 'in-room dining', '24-hour service'],
            'concierge': ['concierge', 'front desk', 'assistance', 'help']
        }
    
    def recognize_intent(self, text: str) -> Intent:
        """
        Recognize intent from user message
        
        Args:
            text: User message text
            
        Returns:
            Intent object with recognized intent and entities
        """
        try:
            text_lower = text.lower().strip()
            
            # Find best matching intent
            best_intent = IntentType.UNKNOWN
            best_confidence = 0.0
            
            for intent_type, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        confidence = self._calculate_confidence(pattern, text_lower)
                        if confidence > best_confidence:
                            best_intent = intent_type
                            best_confidence = confidence
            
            # Extract entities
            entities = self._extract_entities(text_lower)
            
            return Intent(
                type=best_intent,
                confidence=best_confidence,
                entities=entities,
                raw_text=text
            )
            
        except Exception as e:
            logger.error(f"Error recognizing intent: {str(e)}")
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                entities=[],
                raw_text=text
            )
    
    def _calculate_confidence(self, pattern: str, text: str) -> float:
        """Calculate confidence score for pattern match"""
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if not matches:
                return 0.0
            
            # Base confidence on number of matches and pattern complexity
            match_count = len(matches)
            pattern_complexity = len(pattern.split('|'))
            
            # Simple confidence calculation
            confidence = min(0.9, (match_count * 0.3) + (pattern_complexity * 0.1))
            return confidence
            
        except Exception:
            return 0.5  # Default confidence
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from text"""
        entities = []
        
        try:
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        entity = Entity(
                            type=entity_type,
                            value=match.group().strip(),
                            confidence=0.8,  # Default confidence
                            start_pos=match.start(),
                            end_pos=match.end()
                        )
                        entities.append(entity)
            
            # Remove duplicates and sort by position
            entities = self._deduplicate_entities(entities)
            entities.sort(key=lambda x: x.start_pos)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return []
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = (entity.type, entity.value.lower())
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def extract_search_criteria(self, intent: Intent) -> Dict[str, Any]:
        """Extract search criteria from intent and entities"""
        criteria = {}
        
        try:
            # Extract location
            location_entities = [e for e in intent.entities if e.type == EntityType.LOCATION]
            if location_entities:
                criteria['location'] = location_entities[0].value
            
            # Extract dates
            date_entities = [e for e in intent.entities if e.type == EntityType.DATE]
            if date_entities:
                criteria['dates'] = self._parse_dates(date_entities[0].value)
            
            # Extract guest count
            number_entities = [e for e in intent.entities if e.type == EntityType.NUMBER]
            if number_entities:
                criteria['guests'] = self._parse_numbers(number_entities[0].value)
            
            # Extract amenities
            amenity_entities = [e for e in intent.entities if e.type == EntityType.AMENITY]
            if amenity_entities:
                criteria['amenities'] = [e.value for e in amenity_entities]
            
            # Extract price range
            price_entities = [e for e in intent.entities if e.type == EntityType.PRICE_RANGE]
            if price_entities:
                criteria['price_range'] = self._parse_price_range(price_entities[0].value)
            
            return criteria
            
        except Exception as e:
            logger.error(f"Error extracting search criteria: {str(e)}")
            return {}
    
    def _parse_dates(self, date_text: str) -> Dict[str, str]:
        """Parse date text into structured format"""
        # This is a simplified date parser
        # In production, you'd want more sophisticated date parsing
        today = datetime.now()
        
        if 'tomorrow' in date_text.lower():
            tomorrow = today + timedelta(days=1)
            return {
                'checkin': tomorrow.strftime('%Y-%m-%d'),
                'checkout': (tomorrow + timedelta(days=1)).strftime('%Y-%m-%d')
            }
        elif 'next week' in date_text.lower():
            next_week = today + timedelta(days=7)
            return {
                'checkin': next_week.strftime('%Y-%m-%d'),
                'checkout': (next_week + timedelta(days=1)).strftime('%Y-%m-%d')
            }
        
        # Default to next weekend
        next_weekend = today + timedelta(days=(5 - today.weekday()) % 7)
        return {
            'checkin': next_weekend.strftime('%Y-%m-%d'),
            'checkout': (next_weekend + timedelta(days=2)).strftime('%Y-%m-%d')
        }
    
    def _parse_numbers(self, number_text: str) -> Dict[str, int]:
        """Parse number text into guest counts"""
        # Simple number parsing
        numbers = re.findall(r'\d+', number_text)
        if numbers:
            count = int(numbers[0])
            return {
                'adults': count,
                'children': 0,
                'rooms': 1
            }
        
        return {'adults': 2, 'children': 0, 'rooms': 1}
    
    def _parse_price_range(self, price_text: str) -> Dict[str, float]:
        """Parse price range text"""
        # Extract numbers from price text
        numbers = re.findall(r'\d+', price_text)
        if numbers:
            if 'under' in price_text.lower() or 'below' in price_text.lower():
                return {'max': float(numbers[0])}
            elif 'above' in price_text.lower() or 'more than' in price_text.lower():
                return {'min': float(numbers[0])}
            elif len(numbers) >= 2:
                return {'min': float(numbers[0]), 'max': float(numbers[1])}
        
        return {}
