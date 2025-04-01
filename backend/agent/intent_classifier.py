# agent/intent_classifier.py
import re
import datetime

class IntentClassifier:
    """
    Classifies user intents for the restaurant AI agent
    """
    
    def __init__(self):
        self.intents = {
            'greeting': [
                r'hi\b', r'hello\b', r'hey\b', r'howdy\b', r'greetings', 
                r'good morning', r'good afternoon', r'good evening'
            ],
            'farewell': [
                r'bye\b', r'goodbye', r'see you', r'farewell', 
                r'have a good day', r'until next time'
            ],
            'order_food': [
                r'order\b', r'get food', r'place an order', r'buy food', 
                r'food delivery', r'order food', r'food order', r'want to eat',
                r'like to order', r'would like to order', r'hungry',
                r'menu', r'what do you have', r'what can i order'
            ],
            'book_table': [
                r'book\b', r'reserve\b', r'reservation', r'table for', 
                r'book a table', r'reserve a table', r'make a reservation',
                r'table booking', r'get a table', r'have a table'
            ],
            'check_hours': [
                r'hours', r'open', r'close', r'opening time', r'closing time',
                r'when (are|do) you open', r'when (are|do) you close',
                r'business hours', r'schedule'
            ],
            'check_menu': [
                r'menu', r'food options', r'what do you serve', r'dishes',
                r'food list', r'what can i eat', r'what do you have'
            ],
            'order_status': [
                r'status', r'where is my order', r'order status',
                r'track (my|the) order', r'when will (my|the) order arrive'
            ],
            'cancel': [
                r'cancel', r'remove', r'delete'
            ],
            'help': [
                r'help', r'assist', r'support', r'how (can|do) (i|you)',
                r'what can you do'
            ],
            'affirm': [
                r'yes', r'yeah', r'yep', r'correct', r'right', 
                r'that\'s right', r'sounds good', r'okay', r'ok'
            ],
            'deny': [
                r'no', r'nope', r'not', r'don\'t', r'cancel', r'wrong'
            ]
        }
        
        self.entities = {
            'food_item': [],  # Will be populated from menu data
            'date': [
                r'today', r'tomorrow', r'day after tomorrow',
                r'next (monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
                r'on (monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
                r'\d{1,2}[/-]\d{1,2}', r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}'
            ],
            'time': [
                r'\d{1,2}:\d{2}', r'\d{1,2} (am|pm)', r'\d{1,2}(am|pm)',
                r'\d{1,2} o\'?clock', r'noon', r'midnight',
                r'(morning|afternoon|evening|night)',
                r'breakfast', r'lunch', r'dinner', r'brunch'
            ],
            'number': [
                r'\d+', r'one', r'two', r'three', r'four', r'five', 
                r'six', r'seven', r'eight', r'nine', r'ten',
                r'eleven', r'twelve', r'dozen', r'couple', r'few', r'several'
            ],
            'phone': [
                r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
                r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}'
            ],
            'email': [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            ],
            'name': [
                r'(my name is|i am|this is) ([a-zA-Z]+ ?[a-zA-Z]*)'
            ]
        }
    
    def set_menu_items(self, menu_items):
        """Set the menu items for better intent classification"""
        self.entities['food_item'] = []
        for item in menu_items:
            # Create regex patterns from menu item names
            item_name = item['name'].lower()
            parts = item_name.split()
            
            # Add full name pattern
            self.entities['food_item'].append(r'\b' + re.escape(item_name) + r'\b')
            
            # For items with multiple words, also match key words
            if len(parts) > 1:
                for part in parts:
                    if len(part) > 3 and part not in ['with', 'and', 'the']:
                        self.entities['food_item'].append(r'\b' + re.escape(part) + r'\b')
    
    def classify_intent(self, message):
        """
        Classify the user's intent from their message
        
        Args:
            message (str): User's message
            
        Returns:
            dict: Dictionary with intent, confidence, and extracted entities
        """
        message = message.lower()
        
        # Score each intent
        intent_scores = {}
        for intent, patterns in self.intents.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, message)
                score += len(matches)
            intent_scores[intent] = score
        
        # Find highest scoring intent
        max_score = 0
        classified_intent = 'unknown'
        for intent, score in intent_scores.items():
            if score > max_score:
                max_score = score
                classified_intent = intent
                
        # Set confidence based on score
        confidence = min(max_score * 0.2, 0.95) if max_score > 0 else 0.1
        
        # Extract entities
        entities = self._extract_entities(message)
        
        return {
            'intent': classified_intent,
            'confidence': confidence,
            'entities': entities
        }
        
    def _extract_entities(self, message):
        """Extract entities from the message"""
        entities = {}
        
        for entity_type, patterns in self.entities.items():
            extracted = []
            for pattern in patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                if matches:
                    if entity_type == 'name':
                        # For name patterns, extract only the name part
                        for match in matches:
                            if isinstance(match, tuple) and len(match) > 1:
                                extracted.append(match[1].strip())
                    else:
                        extracted.extend(matches)
            
            if extracted:
                entities[entity_type] = list(set(extracted))  # Remove duplicates
        
        # Special case for date processing
        if 'date' in entities:
            processed_dates = []
            today = datetime.datetime.now().date()
            
            for date_str in entities['date']:
                try:
                    if date_str.lower() == 'today':
                        processed_dates.append(today.strftime('%Y-%m-%d'))
                    elif date_str.lower() == 'tomorrow':
                        processed_dates.append((today + datetime.timedelta(days=1)).strftime('%Y-%m-%d'))
                    elif date_str.lower() == 'day after tomorrow':
                        processed_dates.append((today + datetime.timedelta(days=2)).strftime('%Y-%m-%d'))
                    elif 'next' in date_str.lower() or 'on' in date_str.lower():
                        # Handle "next monday" or "on friday"
                        day_of_week = re.search(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', date_str.lower()).group(1)
                        target_day = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}[day_of_week]
                        days_ahead = (target_day - today.weekday()) % 7
                        if days_ahead == 0 and 'next' in date_str.lower():
                            days_ahead = 7  # Next Monday means the Monday after this one
                        processed_dates.append((today + datetime.timedelta(days=days_ahead)).strftime('%Y-%m-%d'))
                    else:
                        # Try to parse various date formats
                        processed_dates.append(date_str)  # Fallback to original
                except Exception as e:
                    processed_dates.append(date_str)  # Keep original on error
            
            entities['processed_date'] = processed_dates
        
        return entities