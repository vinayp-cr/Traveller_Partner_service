"""
NLP Utilities
Helper functions for natural language processing
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.logger import logger


class NLPUtils:
    """Utility class for natural language processing"""
    
    @staticmethod
    def extract_dates(text: str) -> List[Dict[str, str]]:
        """
        Extract dates from text
        
        Args:
            text: Input text
            
        Returns:
            List of extracted dates
        """
        try:
            dates = []
            text_lower = text.lower()
            
            # Relative dates
            if 'today' in text_lower:
                today = datetime.now()
                dates.append({
                    'type': 'checkin',
                    'date': today.strftime('%Y-%m-%d'),
                    'confidence': 0.9
                })
            elif 'tomorrow' in text_lower:
                tomorrow = datetime.now() + timedelta(days=1)
                dates.append({
                    'type': 'checkin',
                    'date': tomorrow.strftime('%Y-%m-%d'),
                    'confidence': 0.9
                })
            elif 'next week' in text_lower:
                next_week = datetime.now() + timedelta(days=7)
                dates.append({
                    'type': 'checkin',
                    'date': next_week.strftime('%Y-%m-%d'),
                    'confidence': 0.8
                })
            elif 'this weekend' in text_lower:
                # Find next Saturday
                today = datetime.now()
                days_ahead = (5 - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                saturday = today + timedelta(days=days_ahead)
                dates.append({
                    'type': 'checkin',
                    'date': saturday.strftime('%Y-%m-%d'),
                    'confidence': 0.8
                })
            
            # Specific dates (MM/DD/YYYY or YYYY-MM-DD)
            date_patterns = [
                r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b',
                r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b'
            ]
            
            for pattern in date_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    try:
                        if len(match.group(1)) == 4:  # YYYY-MM-DD format
                            year, month, day = match.groups()
                        else:  # MM/DD/YYYY format
                            month, day, year = match.groups()
                        
                        # Convert 2-digit year to 4-digit
                        if len(year) == 2:
                            year = '20' + year
                        
                        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        dates.append({
                            'type': 'checkin',
                            'date': date_str,
                            'confidence': 0.7
                        })
                    except ValueError:
                        continue
            
            return dates
            
        except Exception as e:
            logger.error(f"Error extracting dates: {str(e)}")
            return []
    
    @staticmethod
    def extract_numbers(text: str) -> List[Dict[str, Any]]:
        """
        Extract numbers from text
        
        Args:
            text: Input text
            
        Returns:
            List of extracted numbers with context
        """
        try:
            numbers = []
            text_lower = text.lower()
            
            # Number patterns
            patterns = [
                (r'\b(\d+)\s*(adults?|people|guests?)\b', 'adults'),
                (r'\b(\d+)\s*(children?|kids?)\b', 'children'),
                (r'\b(\d+)\s*(rooms?)\b', 'rooms'),
                (r'\b(\d+)\s*(nights?)\b', 'nights'),
                (r'\b(\d+)\s*(\$|dollars?)\b', 'price'),
                (r'\b(\d+)\s*(stars?)\b', 'rating')
            ]
            
            for pattern, context in patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    numbers.append({
                        'value': int(match.group(1)),
                        'context': context,
                        'confidence': 0.8
                    })
            
            # Word numbers
            word_numbers = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
            }
            
            for word, num in word_numbers.items():
                if word in text_lower:
                    numbers.append({
                        'value': num,
                        'context': 'general',
                        'confidence': 0.6
                    })
            
            return numbers
            
        except Exception as e:
            logger.error(f"Error extracting numbers: {str(e)}")
            return []
    
    @staticmethod
    def extract_locations(text: str) -> List[Dict[str, str]]:
        """
        Extract locations from text
        
        Args:
            text: Input text
            
        Returns:
            List of extracted locations
        """
        try:
            locations = []
            text_lower = text.lower()
            
            # Common location patterns
            location_patterns = [
                (r'\b(new york|nyc|manhattan|brooklyn|queens|bronx|staten island)\b', 'city'),
                (r'\b(times square|central park|wall street|soho|chelsea|greenwich)\b', 'neighborhood'),
                (r'\b(beach|ocean|downtown|uptown|midtown|east side|west side)\b', 'area'),
                (r'\b(airport|station|bus stop|metro|subway)\b', 'transportation'),
                (r'\b(hotel|motel|inn|resort|hostel)\b', 'accommodation')
            ]
            
            for pattern, location_type in location_patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    locations.append({
                        'value': match.group(1),
                        'type': location_type,
                        'confidence': 0.8
                    })
            
            return locations
            
        except Exception as e:
            logger.error(f"Error extracting locations: {str(e)}")
            return []
    
    @staticmethod
    def extract_amenities(text: str) -> List[Dict[str, str]]:
        """
        Extract amenities from text
        
        Args:
            text: Input text
            
        Returns:
            List of extracted amenities
        """
        try:
            amenities = []
            text_lower = text.lower()
            
            # Amenity patterns
            amenity_patterns = [
                (r'\b(breakfast|continental breakfast|free breakfast)\b', 'breakfast'),
                (r'\b(wifi|internet|wireless|free wifi)\b', 'wifi'),
                (r'\b(pool|swimming pool|outdoor pool|indoor pool)\b', 'pool'),
                (r'\b(gym|fitness|fitness center|workout|exercise)\b', 'gym'),
                (r'\b(spa|massage|wellness|relaxation)\b', 'spa'),
                (r'\b(parking|valet|free parking)\b', 'parking'),
                (r'\b(restaurant|dining|food|meal)\b', 'restaurant'),
                (r'\b(bar|lounge|cocktail|drinks)\b', 'bar'),
                (r'\b(room service|in-room dining|24-hour service)\b', 'room_service'),
                (r'\b(concierge|front desk|assistance|help)\b', 'concierge'),
                (r'\b(air conditioning|heating|balcony|ocean view|city view)\b', 'room_features')
            ]
            
            for pattern, amenity_type in amenity_patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    amenities.append({
                        'value': match.group(1),
                        'type': amenity_type,
                        'confidence': 0.8
                    })
            
            return amenities
            
        except Exception as e:
            logger.error(f"Error extracting amenities: {str(e)}")
            return []
    
    @staticmethod
    def extract_price_ranges(text: str) -> List[Dict[str, Any]]:
        """
        Extract price ranges from text
        
        Args:
            text: Input text
            
        Returns:
            List of extracted price ranges
        """
        try:
            price_ranges = []
            text_lower = text.lower()
            
            # Price range patterns
            patterns = [
                (r'\b(under|below|less than)\s*(\$?\d+)\b', 'max'),
                (r'\b(above|more than|over)\s*(\$?\d+)\b', 'min'),
                (r'\b(\$?\d+)\s*(to|and|-\s*)\s*(\$?\d+)\b', 'range'),
                (r'\b(cheap|budget|affordable|expensive|luxury|premium)\b', 'qualitative')
            ]
            
            for pattern, price_type in patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    if price_type == 'range':
                        min_price = float(match.group(1).replace('$', ''))
                        max_price = float(match.group(3).replace('$', ''))
                        price_ranges.append({
                            'min': min_price,
                            'max': max_price,
                            'type': 'range',
                            'confidence': 0.8
                        })
                    elif price_type in ['min', 'max']:
                        price = float(match.group(2).replace('$', ''))
                        price_ranges.append({
                            price_type: price,
                            'type': price_type,
                            'confidence': 0.8
                        })
                    else:  # qualitative
                        price_ranges.append({
                            'type': 'qualitative',
                            'value': match.group(1),
                            'confidence': 0.6
                        })
            
            return price_ranges
            
        except Exception as e:
            logger.error(f"Error extracting price ranges: {str(e)}")
            return []
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        try:
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Remove special characters but keep basic punctuation
            text = re.sub(r'[^\w\s.,!?$%-]', '', text)
            
            # Normalize common abbreviations
            text = text.replace('nyc', 'new york city')
            text = text.replace('ny', 'new york')
            text = text.replace('la', 'los angeles')
            text = text.replace('sf', 'san francisco')
            
            return text
            
        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            return text
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """
        Calculate text similarity using simple word overlap
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        try:
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 3) -> List[str]:
        """
        Extract keywords from text
        
        Args:
            text: Input text
            min_length: Minimum keyword length
            
        Returns:
            List of keywords
        """
        try:
            # Remove common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
                'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
                'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
                'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
                'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
                'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
            }
            
            # Extract words
            words = re.findall(r'\b\w+\b', text.lower())
            
            # Filter by length and stop words
            keywords = [
                word for word in words
                if len(word) >= min_length and word not in stop_words
            ]
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
