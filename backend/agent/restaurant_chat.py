#!/usr/bin/env python3
"""
This script fixes multiple issues in the restaurant chat application:
1. Improves menu item recognition
2. Fixes order completion
3. Enhances error handling

Run this from your project's root directory.
"""

import os
import re
import shutil

def backup_file(filepath):
    """Create a backup of the original file"""
    backup_path = filepath + '.bak'
    shutil.copy2(filepath, backup_path)
    print(f"Backup created at {backup_path}")

def replace_function(content, function_name, new_function):
    """Replace a function in the content with a new implementation"""
    # Find the function
    pattern = fr'def {function_name}\([^)]*\):.*?(?=\n\s*def|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print(f"Could not find function '{function_name}'. Make sure you're running this on the correct file.")
        return content, False
    
    # Get the function definition and the indentation
    old_function = match.group(0)
    
    # Replace with the fixed function
    new_content = content.replace(old_function, new_function)
    
    return new_content, True

def fix_order_handler(filepath):
    """Fix the identify_menu_items function in OrderHandler"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    new_identify_items_function = '''def identify_menu_items(self, message):
        """
        Identify potential menu items from a message
        
        Args:
            message (str): User message
            
        Returns:
            list: List of potential menu items
        """
        message = message.lower()
        potential_items = {}
        
        # Try exact matching first
        for name, item in self.menu_by_name.items():
            if name in message:
                potential_items[item.id] = {
                    'item': item,
                    'confidence': 1.0,
                    'quantity': 1  # Default quantity
                }
        
        # If no exact matches, try keyword matching with a more lenient approach
        if not potential_items:
            # Check if the message contains only the item name without price
            for name, item in self.menu_by_name.items():
                # Remove special characters and convert to lowercase for comparison
                clean_name = ''.join(c for c in name if c.isalnum() or c.isspace()).lower()
                clean_message = ''.join(c for c in message if c.isalnum() or c.isspace()).lower()
                
                if clean_name in clean_message or clean_message in clean_name:
                    potential_items[item.id] = {
                        'item': item,
                        'confidence': 0.9,
                        'quantity': 1
                    }
                    break  # Found a match, no need to continue
        
        # If still no matches, try more aggressive fuzzy matching
        if not potential_items:
            words = set(re.findall(r'\\b\\w+\\b', message))
            for word in words:
                if len(word) >= 4:  # Only consider words of reasonable length
                    for name, item in self.menu_by_name.items():
                        if word in name.lower():
                            potential_items[item.id] = {
                                'item': item,
                                'confidence': 0.7,
                                'quantity': 1
                            }
                            break
        
        # If still no matches, try the original keyword matching
        if not potential_items:
            words = set(re.findall(r'\\b\\w+\\b', message))
            for word in words:
                if word in self.keyword_to_menu:
                    for item in self.keyword_to_menu[word]:
                        # Skip items already matched
                        if item.id in potential_items:
                            continue
                            
                        # Calculate a confidence score based on word match
                        item_words = set(re.findall(r'\\b\\w+\\b', item.name.lower()))
                        matching_words = words.intersection(item_words)
                        confidence = len(matching_words) / len(item_words)
                        
                        if confidence > 0.2:  # Lower threshold for accepting a match
                            potential_items[item.id] = {
                                'item': item,
                                'confidence': confidence,
                                'quantity': 1  # Default quantity
                            }
        
        # Extract quantities
        quantity_patterns = [
            r'(\\d+)\\s+([a-zA-Z\\s]+)',  # "2 margherita pizza"
            r'([a-zA-Z\\s]+)\\s+(\\d+)',  # "margherita pizza 2"
        ]
        
        for pattern in quantity_patterns:
            matches = re.findall(pattern, message)
            for match in matches:
                # Determine which group is the quantity and which is the item
                if match[0].isdigit():
                    quantity, item_text = int(match[0]), match[1]
                else:
                    item_text, quantity = match[0], int(match[1])
                
                # Try to find matching item
                for item_id, item_data in potential_items.items():
                    item_name = item_data['item'].name.lower()
                    if item_text.lower() in item_name or item_name in item_text.lower():
                        potential_items[item_id]['quantity'] = quantity
                        break
        
        # Debug print - log what was recognized
        print(f"Identified items from message '{message}': {[item_data['item'].name for _, item_data in potential_items.items()]}")
        
        return [
            {
                'id': item_id,
                'name': item_data['item'].name,
                'price': item_data['item'].price,
                'quantity': item_data['quantity'],
                'confidence': item_data['confidence']
            }
            for item_id, item_data in potential_items.items()
        ]'''
    
    new_content, success = replace_function(content, "identify_menu_items", new_identify_items_function)
    
    if success:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False

def fix_agent_init(filepath):
    """Fix functions in the RestaurantAgent class"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix process_message function
    new_process_message = '''def process_message(self, message, session_id=None):
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
            }'''
    
    new_handle_ordering_state = '''def handle_ordering_state(self, intent, entities, conversation):
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
            completion_phrases = ['that\\'s all', 'nothing', 'done', 'complete', 'finish', 'no more', 'that is all']
            
            # Check if the message contains any completion phrase
            if any(phrase in message.lower() for phrase in completion_phrases) or intent == 'affirm' or intent == 'deny':
                if ordering.get('items') and len(ordering['items']) > 0:
                    ordering['stage'] = 'confirmation'
                    total = self.order_handler.calculate_total(ordering['items'])
                    order_summary = self.response_generator.format_order_summary(ordering['items'], total)
                    
                    return {
                        'text': f"{order_summary}\\n\\nWould you like to proceed with this order?",
                        'items': ordering['items'],
                        'total': total
                    }
                else:
                    # No items yet
                    suggested_items = self.order_handler.get_menu_suggestions(max_items=5)
                    return {
                        'text': "You haven't selected any items yet. Here are some suggestions:\\n\\n" + 
                              self.response_generator.format_menu_items(suggested_items),
                        'suggestions': suggested_items
                    }
            
            # Check if trying to add items
            if intent == 'order_food' and entities.get('food_item'):
                # Add items to the order
                new_items = self.order_handler.identify_menu_items(" ".join(entities['food_item']))
                
                if new_items:
                    # Add to existing items
                    existing_ids = [item['id'] for item in ordering.get('items', [])]
                    for item in new_items:
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
                    
                    # Generate response
                    return {
                        'text': f"I've added {', '.join([f'{item[\\'quantity\\']}x {item[\\'name\\']}' for item in new_items])} to your order. Would you like anything else?",
                        'items': ordering['items']
                    }
                
            # Otherwise ask for more items
            return {
                'text': "What else would you like to order? Or say 'that\\'s all' if you\\'re done."
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
        }'''
    
    # First replace process_message
    new_content, success1 = replace_function(content, "process_message", new_process_message)
    
    if not success1:
        return False
    
    # Then replace handle_ordering_state in the updated content
    new_content, success2 = replace_function(new_content, "handle_ordering_state", new_handle_ordering_state)
    
    if success1 and success2:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    
    return False

def main():
    # Path to the files
    order_handler_path = os.path.join('backend', 'agent', 'order_handler.py')
    agent_init_path = os.path.join('backend', 'agent', '__init__.py')
    
    if not os.path.exists(order_handler_path) or not os.path.exists(agent_init_path):
        print("Could not find required files. Make sure you're running this script from the project root.")
        return
    
    # Create backups
    backup_file(order_handler_path)
    backup_file(agent_init_path)
    
    # Fix the files
    order_handler_success = fix_order_handler(order_handler_path)
    agent_init_success = fix_agent_init(agent_init_path)
    
    if order_handler_success and agent_init_success:
        print("Successfully patched all files!")
        print("Restart your Flask server for the changes to take effect.")
    else:
        if not order_handler_success:
            print("Failed to patch order_handler.py")
        if not agent_init_success:
            print("Failed to patch agent/__init__.py")
        print("You may need to manually update the files.")

if __name__ == "__main__":
    main()