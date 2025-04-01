# agent/__init__.py
from .intent_classifier import IntentClassifier
from .order_handler import OrderHandler
from .booking_handler import BookingHandler
from .response_generator import ResponseGenerator
import json
import uuid

class RestaurantAgent:
    """
    Main restaurant AI agent that coordinates between components
    """
    
    def __init__(self, session, restaurant_info):
        self.session = session
        self.restaurant_info = restaurant_info
        
        # Initialize components
        self.intent_classifier = IntentClassifier()
        self.response_generator = ResponseGenerator(restaurant_info)
        
        # Load menu items
        from models import MenuItem
        self.menu_items = session.query(MenuItem).all()
        
        # Set menu items in the intent classifier for better detection
        self.intent_classifier.set_menu_items([item.to_dict() for item in self.menu_items])
        
        # Initialize handlers
        self.order_handler = OrderHandler(session, self.menu_items)
        self.booking_handler = BookingHandler(session)
        
        # Conversation state
        self.conversations = {}
    
    def get_or_create_conversation(self, session_id=None):
        """Get or create a conversation for the session"""
        if not session_id:
            session_id = str(uuid.uuid4())
            
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                'session_id': session_id,
                'state': 'initial',
                'context': {},
                'history': []
            }
            
        return self.conversations[session_id]
    
    def process_message(self, message, session_id=None):
        """
        Process a user message and generate a response
        
        Args:
            message (str): User message
            session_id (str): Session ID for conversation tracking
            
        Returns:
            dict: Response with text and any additional data
        """
        # Get or create conversation
        conversation = self.get_or_create_conversation(session_id)
        
        try:
            # Add message to history
            conversation['history'].append({
                'user': message
            })
            
            # Classify intent
            classification = self.intent_classifier.classify_intent(message)
            intent = classification['intent']
            entities = classification['entities']
            
            # Debug logging
            print(f"Message: '{message}'")
            print(f"Classified intent: '{intent}'")
            print(f"Entities: {entities}")
            print(f"Current state: '{conversation['state']}'")
            
            # Update history with classification
            conversation['history'][-1]['classification'] = classification
            
            # Special handling for menu items - direct item selection
            if conversation['state'] == 'ordering':
                # Check if the message might contain menu items
                items = self.order_handler.identify_menu_items(message)
                if items:
                    print(f"Items identified: {items}")
                    # Update the conversation context
                    ordering = conversation['context'].get('ordering', {'items': [], 'stage': 'item_selection'})
                    # Add to existing items
                    existing_ids = [item['id'] for item in ordering.get('items', [])]
                    for item in items:
                        if item['id'] in existing_ids:
                            # Update quantity of existing item
                            for existing_item in ordering['items']:
                                if existing_item['id'] == item['id']:
                                    existing_item['quantity'] += item['quantity']
                        else:
                            # Add new item
                            if 'items' not in ordering:
                                ordering['items'] = []
                            ordering['items'].append(item)
                    
                    # Save the updated ordering context
                    conversation['context']['ordering'] = ordering
            
            # Generate response based on intent and state
            response = self.handle_intent(intent, entities, conversation)
            
            # Add response to history
            conversation['history'].append({
                'bot': response['text']
            })
            
            # Store in database
            from models import Conversation as ConversationModel
            conv_record = ConversationModel(
                session_id=conversation['session_id'],
                user_message=message,
                bot_response=response['text']
            )
            self.session.add(conv_record)
            self.session.commit()
            
            return response
        except Exception as e:
            import traceback
            print(f"Error processing message: {e}")
            print(traceback.format_exc())
            
            # Add a friendly error response to history
            conversation['history'].append({
                'bot': f"I'm sorry, I encountered an error processing your request. Please try again."
            })
            
            # Return error response
            return {
                'text': f"I'm sorry, I encountered an error processing your request. Please try again.",
                'error': str(e)
            }
    
    def handle_intent(self, intent, entities, conversation):
        """
        Handle the classified intent
        
        Args:
            intent (str): Classified intent
            entities (dict): Extracted entities
            conversation (dict): Conversation state
            
        Returns:
            dict: Response with text and any additional data
        """
        state = conversation['state']
        context = conversation['context']
        
        # Handle based on current state
        if state == 'initial':
            return self.handle_initial_state(intent, entities, conversation)
        elif state == 'ordering':
            return self.handle_ordering_state(intent, entities, conversation)
        elif state == 'booking':
            return self.handle_booking_state(intent, entities, conversation)
        else:
            # Fallback to intent-based handling
            return self.handle_by_intent(intent, entities, conversation)
    
    def handle_initial_state(self, intent, entities, conversation):
        """Handle initial conversation state"""
        context = conversation['context']
        
        if intent == 'greeting':
            return {
                'text': self.response_generator.get_response('greeting')
            }
        elif intent == 'order_food':
            conversation['state'] = 'ordering'
            context['ordering'] = {
                'items': [],
                'stage': 'item_selection'
            }
            
            # Check if we already have items in the message
            suggested_items = []
            if entities.get('food_item'):
                items = self.order_handler.identify_menu_items(" ".join(entities['food_item']))
                if items:
                    context['ordering']['items'] = items
                    items_text = ', '.join(f"{item['quantity']}x {item['name']}" for item in items)
                    return {
                        'text': f"I've added {items_text} to your order. Would you like anything else?",
                        'items': items
                    }
            
            # Otherwise suggest menu items
            suggested_items = self.order_handler.get_menu_suggestions(max_items=5)
            return {
                'text': self.response_generator.get_response('order_inquiry') + "\n\n" + 
                       self.response_generator.get_response('suggest_menu_items', 
                                                          items=self.response_generator.format_menu_items(suggested_items)),
                'suggestions': suggested_items
            }
            
        elif intent == 'book_table':
            conversation['state'] = 'booking'
            context['booking'] = {
                'stage': 'date_selection'
            }
            
            # Process any entities we already have
            if entities.get('processed_date'):
                context['booking']['date'] = entities['processed_date'][0]
                context['booking']['stage'] = 'time_selection'
                
                # Get available times for the date
                available_times = self.booking_handler.get_available_times(context['booking']['date'])
                
                if not available_times:
                    return {
                        'text': self.response_generator.get_response('no_availability') + " Would you like to try another date?",
                        'available_dates': self.booking_handler.get_available_dates()
                    }
                
                times_text = self.response_generator.format_available_times(available_times)
                return {
                    'text': self.response_generator.get_response('suggest_times', 
                                                              date=context['booking']['date'],
                                                              times=times_text),
                    'available_times': available_times
                }
            
            # If no date provided, ask for one
            available_dates = self.booking_handler.get_available_dates()
            return {
                'text': self.response_generator.get_response('booking_inquiry'),
                'available_dates': available_dates
            }
            
        elif intent == 'check_menu':
            menu_items = [item.to_dict() for item in self.menu_items]
            return {
                'text': self.response_generator.get_response('menu_inquiry'),
                'menu': menu_items
            }
            
        elif intent == 'check_hours':
            return {
                'text': self.response_generator.get_response('hours_info')
            }
            
        elif intent == 'help':
            return {
                'text': self.response_generator.get_response('help')
            }
            
        else:
            # Handle unknown intent
            return {
                'text': self.response_generator.get_response('unknown')
            }
    
    def handle_ordering_state(self, intent, entities, conversation):
        """Handle ordering conversation state"""
        context = conversation['context']
        ordering = context['ordering']
        message = conversation['history'][-1]['user'] if conversation['history'] else ""
        
        if intent == 'cancel':
            conversation['state'] = 'initial'
            return {
                'text': "I've cancelled your order. Is there anything else I can help with?"
            }
            
        if ordering['stage'] == 'item_selection':
            # Check for order completion phrases first
            completion_phrases = ['that\'s all', 'nothing', 'done', 'complete', 'finish', 'no more', 'that is all']
            
            # Check if the message contains any completion phrase
            if any(phrase in message.lower() for phrase in completion_phrases) or intent == 'affirm' or intent == 'deny':
                if ordering['items']:
                    ordering['stage'] = 'confirmation'
                    total = self.order_handler.calculate_total(ordering['items'])
                    order_summary = self.response_generator.format_order_summary(ordering['items'], total)
                    
                    return {
                        'text': f"{order_summary}\n\nWould you like to proceed with this order?",
                        'items': ordering['items'],
                        'total': total
                    }
                else:
                    # No items yet
                    suggested_items = self.order_handler.get_menu_suggestions(max_items=5)
                    return {
                        'text': "You haven't selected any items yet. Here are some suggestions:\n\n" + 
                            self.response_generator.format_menu_items(suggested_items),
                        'suggestions': suggested_items
                    }
            
            # Check if trying to add items
            if intent == 'order_food' and entities.get('food_item'):
                # Add items to the order
                new_items = self.order_handler.identify_menu_items(" ".join(entities['food_item']))
                
                if new_items:
                    # Add to existing items
                    existing_ids = [item['id'] for item in ordering['items']]
                    for item in new_items:
                        if item['id'] in existing_ids:
                            # Update quantity of existing item
                            for existing_item in ordering['items']:
                                if existing_item['id'] == item['id']:
                                    existing_item['quantity'] += item['quantity']
                        else:
                            # Add new item
                            ordering['items'].append(item)
                    
                    # Generate response
                    items_text = ', '.join(f"{item['quantity']}x {item['name']}" for item in new_items)
                    return {
                        'text': f"{items_text} to your order. Would you like anything else?",
                        'items': ordering['items']
                    }
                
            # Otherwise ask for more items
            return {
                'text': "What else would you like to order? Or say 'that's all' if you're done."
            }
            
        elif ordering['stage'] == 'confirmation':
            if intent == 'affirm' or any(word in message.lower() for word in ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay']):
                # Proceed to customer details
                ordering['stage'] = 'customer_details'
                
                # Extract any customer details from entities
                customer_info = {}
                if entities.get('name'):
                    customer_info['name'] = entities['name'][0]
                if entities.get('phone'):
                    customer_info['phone'] = entities['phone'][0]
                if entities.get('email'):
                    customer_info['email'] = entities['email'][0]
                
                context['ordering']['customer_info'] = customer_info
                
                # If we already have sufficient info, proceed to order creation
                if customer_info.get('name') and (customer_info.get('phone') or customer_info.get('email')):
                    return self.complete_order(conversation)
                
                return {
                    'text': self.response_generator.get_response('contact_request', purpose="order")
                }
                
            elif intent == 'deny' or any(word in message.lower() for word in ['no', 'nope', 'cancel']):
                # Back to item selection
                ordering['stage'] = 'item_selection'
                return {
                    'text': "No problem. What changes would you like to make to your order?"
                }
            
            # If neither affirm nor deny, assume they want to make changes
            ordering['stage'] = 'item_selection'
            return {
                'text': "What would you like to change in your order?"
            }
            
        elif ordering['stage'] == 'customer_details':
            # Extract customer details
            customer_info = context['ordering'].get('customer_info', {})
            
            if entities.get('name') and not customer_info.get('name'):
                customer_info['name'] = entities['name'][0]
            if entities.get('phone') and not customer_info.get('phone'):
                customer_info['phone'] = entities['phone'][0]
            if entities.get('email') and not customer_info.get('email'):
                customer_info['email'] = entities['email'][0]
            
            context['ordering']['customer_info'] = customer_info
            
            # Check if we have enough info
            if customer_info.get('name') and (customer_info.get('phone') or customer_info.get('email')):
                return self.complete_order(conversation)
            
            # Ask for missing information
            if not customer_info.get('name'):
                return {
                    'text': "What name should I put for this order?"
                }
            else:
                return {
                    'text': "How can we contact you? Please provide a phone number or email."
                }
                
        return {
            'text': "Is there anything else you'd like to add to your order?"
        }
    
    def handle_booking_state(self, intent, entities, conversation):
        """Handle booking conversation state"""
        context = conversation['context']
        booking = context.get('booking', {})
        
        if intent == 'cancel':
            conversation['state'] = 'initial'
            return {
                'text': "I've cancelled your reservation request. Is there anything else I can help with?"
            }
            
        if booking['stage'] == 'date_selection':
            if entities.get('processed_date'):
                booking['date'] = entities['processed_date'][0]
                booking['stage'] = 'time_selection'
                
                # Get available times for the date
                available_times = self.booking_handler.get_available_times(booking['date'])
                
                if not available_times:
                    return {
                        'text': self.response_generator.get_response('no_availability') + " Would you like to try another date?",
                        'available_dates': self.booking_handler.get_available_dates()
                    }
                
                times_text = self.response_generator.format_available_times(available_times)
                return {
                    'text': self.response_generator.get_response('suggest_times', 
                                                              date=booking['date'],
                                                              times=times_text),
                    'available_times': available_times
                }
            
            # No date found, ask again
            available_dates = self.booking_handler.get_available_dates()
            return {
                'text': "What date would you like to make a reservation for?",
                'available_dates': available_dates
            }
            
        elif booking['stage'] == 'time_selection':
            if entities.get('time'):
                time_str = entities['time'][0]
                processed_time = self.booking_handler.parse_time(time_str)
                
                if processed_time:
                    booking['time'] = processed_time
                    booking['stage'] = 'guests_selection'
                    
                    # Check if we already have number of guests
                    if booking.get('guests'):
                        return self.handle_booking_state(intent, entities, conversation)
                    
                    return {
                        'text': "How many people will be dining?"
                    }
                
                # Invalid time
                available_times = self.booking_handler.get_available_times(booking['date'])
                times_text = self.response_generator.format_available_times(available_times)
                
                return {
                    'text': f"I'm sorry, I couldn't understand that time. Available times for {booking['date']} are: {times_text}",
                    'available_times': available_times
                }
            
            # No time found, ask again
            available_times = self.booking_handler.get_available_times(booking['date'])
            times_text = self.response_generator.format_available_times(available_times)
            
            return {
                'text': f"What time would you like to book the table? Available times are: {times_text}",
                'available_times': available_times
            }
            
        elif booking['stage'] == 'guests_selection':
            if entities.get('number'):
                number_str = entities['number'][0]
                guests = self.booking_handler.parse_guests(number_str)
                booking['guests'] = guests
                booking['stage'] = 'confirmation'
                
                # Check availability
                is_available = self.booking_handler.is_table_available(
                    booking['date'], booking['time'], booking['guests']
                )
                
                if not is_available:
                    booking['stage'] = 'time_selection'
                    available_times = self.booking_handler.get_available_times(booking['date'])
                    times_text = self.response_generator.format_available_times(available_times)
                    
                    return {
                        'text': f"I'm sorry, we don't have availability for {booking['guests']} guests at {booking['time']} on {booking['date']}. Available times are: {times_text}",
                        'available_times': available_times
                    }
                
                # Show booking summary
                booking_summary = self.response_generator.format_booking_summary(booking)
                return {
                    'text': f"{booking_summary}\n\nWould you like to confirm this reservation?",
                    'booking': booking
                }
            
            # No number found, ask again
            return {
                'text': "How many people will be in your party?"
            }
            
        elif booking['stage'] == 'confirmation':
            if intent == 'affirm':
                # Proceed to customer details
                booking['stage'] = 'customer_details'
                
                # Extract any customer details from entities
                customer_info = {}
                if entities.get('name'):
                    customer_info['name'] = entities['name'][0]
                if entities.get('phone'):
                    customer_info['phone'] = entities['phone'][0]
                if entities.get('email'):
                    customer_info['email'] = entities['email'][0]
                
                context['booking']['customer_info'] = customer_info
                
                # If we already have sufficient info, proceed to booking creation
                if customer_info.get('name') and (customer_info.get('phone') or customer_info.get('email')):
                    return self.complete_booking(conversation)
                
                return {
                    'text': self.response_generator.get_response('contact_request', purpose="reservation")
                }
                
            elif intent == 'deny':
                # Go back to date selection
                booking['stage'] = 'date_selection'
                return {
                    'text': "No problem. Let's start over. What date would you like to make a reservation for?",
                    'available_dates': self.booking_handler.get_available_dates()
                }
            
            # If neither affirm nor deny, assume they want to make changes
            booking['stage'] = 'date_selection'
            return {
                'text': "What would you like to change in your reservation?",
                'available_dates': self.booking_handler.get_available_dates()
            }
            
        elif booking['stage'] == 'customer_details':
            # Extract customer details
            customer_info = context['booking'].get('customer_info', {})
            
            if entities.get('name') and not customer_info.get('name'):
                customer_info['name'] = entities['name'][0]
            if entities.get('phone') and not customer_info.get('phone'):
                customer_info['phone'] = entities['phone'][0]
            if entities.get('email') and not customer_info.get('email'):
                customer_info['email'] = entities['email'][0]
            
            context['booking']['customer_info'] = customer_info
            
            # Check if we have enough info
            if customer_info.get('name') and (customer_info.get('phone') or customer_info.get('email')):
                return self.complete_booking(conversation)
            
            # Ask for missing information
            if not customer_info.get('name'):
                return {
                    'text': "What name should I put for this reservation?"
                }
            else:
                return {
                    'text': "How can we contact you? Please provide a phone number or email."
                }
        
        # Fallback
        return {
            'text': "Let's continue with your reservation. What date would you like to book?",
            'available_dates': self.booking_handler.get_available_dates()
        }
    
    def handle_by_intent(self, intent, entities, conversation):
        """Handle based purely on intent"""
        if intent == 'greeting':
            return {
                'text': self.response_generator.get_response('greeting')
            }
        elif intent == 'farewell':
            return {
                'text': self.response_generator.get_response('farewell')
            }
        elif intent == 'order_food':
            conversation['state'] = 'ordering'
            context = conversation['context']
            context['ordering'] = {
                'items': [],
                'stage': 'item_selection'
            }
            
            # Check for food items in the message
            if entities.get('food_item'):
                items = self.order_handler.identify_menu_items(" ".join(entities['food_item']))
                if items:
                    context['ordering']['items'] = items
                    return {
                        'text': {', '.join([f"{item['quantity']}x {item['name']}" for item in items])},
                        'items': items
                    }
            
            # Otherwise suggest menu items
            suggested_items = self.order_handler.get_menu_suggestions(max_items=5)
            return {
                'text': self.response_generator.get_response('order_inquiry') + "\n\n" + 
                       self.response_generator.get_response('suggest_menu_items', 
                                                          items=self.response_generator.format_menu_items(suggested_items)),
                'suggestions': suggested_items
            }
            
        elif intent == 'book_table':
            conversation['state'] = 'booking'
            context = conversation['context']
            context['booking'] = {
                'stage': 'date_selection'
            }
            
            # Process any entities we already have
            if entities.get('processed_date'):
                context['booking']['date'] = entities['processed_date'][0]
                context['booking']['stage'] = 'time_selection'
                
                # Get available times for the date
                available_times = self.booking_handler.get_available_times(context['booking']['date'])
                
                if not available_times:
                    return {
                        'text': self.response_generator.get_response('no_availability') + " Would you like to try another date?",
                        'available_dates': self.booking_handler.get_available_dates()
                    }
                
                times_text = self.response_generator.format_available_times(available_times)
                return {
                    'text': self.response_generator.get_response('suggest_times', 
                                                              date=context['booking']['date'],
                                                              times=times_text),
                    'available_times': available_times
                }
            
            # If no date provided, ask for one
            available_dates = self.booking_handler.get_available_dates()
            return {
                'text': self.response_generator.get_response('booking_inquiry'),
                'available_dates': available_dates
            }
            
        elif intent == 'check_menu':
            menu_items = [item.to_dict() for item in self.menu_items]
            return {
                'text': self.response_generator.get_response('menu_inquiry'),
                'menu': menu_items
            }
            
        elif intent == 'check_hours':
            return {
                'text': self.response_generator.get_response('hours_info')
            }
            
        elif intent == 'help':
            return {
                'text': self.response_generator.get_response('help')
            }
            
        else:
            # Unknown intent
            return {
                'text': self.response_generator.get_response('unknown')
            }
    
    def complete_order(self, conversation):
        """
        Complete the order process
        
        Args:
            conversation (dict): Conversation state
            
        Returns:
            dict: Response with confirmation text
        """
        context = conversation['context']
        ordering = context['ordering']
        customer_info = ordering.get('customer_info', {})
        
        # Create order in database
        try:
            order = self.order_handler.create_order(customer_info, ordering['items'])
            
            # Reset conversation state
            conversation['state'] = 'initial'
            
            return {
                'text': self.response_generator.get_response('order_confirmation', 
                                                          order_id=order.id,
                                                          time="30 minutes"),
                'order': order.to_dict()
            }
        except Exception as e:
            # Handle error
            return {
                'text': f"I'm sorry, there was an error processing your order: {str(e)}. Please try again."
            }
    
    def complete_booking(self, conversation):
        """
        Complete the booking process
        
        Args:
            conversation (dict): Conversation state
            
        Returns:
            dict: Response with confirmation text
        """
        context = conversation['context']
        booking_data = context['booking']
        customer_info = booking_data.get('customer_info', {})
        
        # Create booking in database
        try:
            booking_details = {
                'date': booking_data['date'],
                'time': booking_data['time'],
                'guests': booking_data['guests'],
                'special_requests': booking_data.get('special_requests', '')
            }
            
            booking = self.booking_handler.create_booking(customer_info, booking_details)
            
            # Reset conversation state
            conversation['state'] = 'initial'
            
            return {
                'text': self.response_generator.get_response('booking_confirmation',
                                                          date=booking.date,
                                                          time=booking.time,
                                                          guests=booking.guests),
                'booking': booking.to_dict()
            }
        except Exception as e:
            # Handle error
            return {
                'text': f"I'm sorry, there was an error processing your booking: {str(e)}. Please try again."
            }