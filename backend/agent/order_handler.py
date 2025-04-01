# agent/order_handler.py
from models import Order, OrderItem
import re

class OrderHandler:
    """
    Handles food ordering functionality
    """
    
    def __init__(self, session, menu_items):
        self.session = session
        self.menu_items = menu_items
        self.menu_by_id = {item.id: item for item in menu_items}
        self.menu_by_name = {item.name.lower(): item for item in menu_items}
        
        # Build keyword index for fuzzy matching
        self.keyword_to_menu = {}
        for item in menu_items:
            words = item.name.lower().split()
            for word in words:
                if len(word) > 3 and word not in ['with', 'and', 'the']:
                    if word not in self.keyword_to_menu:
                        self.keyword_to_menu[word] = []
                    self.keyword_to_menu[word].append(item)
    
    def identify_menu_items(self, message):
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
            words = set(re.findall(r'\b\w+\b', message))
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
            words = set(re.findall(r'\b\w+\b', message))
            for word in words:
                if word in self.keyword_to_menu:
                    for item in self.keyword_to_menu[word]:
                        # Skip items already matched
                        if item.id in potential_items:
                            continue
                            
                        # Calculate a confidence score based on word match
                        item_words = set(re.findall(r'\b\w+\b', item.name.lower()))
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
            r'(\d+)\s+([a-zA-Z\s]+)',  # "2 margherita pizza"
            r'([a-zA-Z\s]+)\s+(\d+)',  # "margherita pizza 2"
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
        ]
    
    def calculate_total(self, items):
        """
        Calculate the total price for an order
        
        Args:
            items (list): List of order items with quantity
            
        Returns:
            float: Total price
        """
        total = 0.0
        for item in items:
            total += item['price'] * item['quantity']
        return round(total, 2)
    
    def create_order(self, customer_info, items):
        """
        Create a new order in the database
        
        Args:
            customer_info (dict): Customer information (name, email, phone)
            items (list): List of order items with quantity
            
        Returns:
            Order: The created order object
        """
        # Calculate total amount
        total_amount = self.calculate_total(items)
        
        # Create order
        order = Order(
            customer_name=customer_info.get('name', 'Guest'),
            customer_email=customer_info.get('email'),
            customer_phone=customer_info.get('phone'),
            total_amount=total_amount,
            status='confirmed'
        )
        self.session.add(order)
        self.session.flush()  # Get the order ID
        
        # Create order items
        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item['id'],
                quantity=item['quantity'],
                price=item['price']
            )
            self.session.add(order_item)
        
        # Commit transaction
        self.session.commit()
        
        return order
    
    def get_menu_suggestions(self, keywords=None, max_items=5):
        """
        Get menu suggestions based on keywords or popular items
        
        Args:
            keywords (list): List of keywords to match
            max_items (int): Maximum number of items to return
            
        Returns:
            list: List of suggested menu items
        """
        if not keywords:
            # Return some random items if no keywords provided
            import random
            suggested_items = random.sample(list(self.menu_by_id.values()), min(max_items, len(self.menu_by_id)))
            return [item.to_dict() for item in suggested_items]
        
        # Try to match keywords with menu items
        matched_items = {}
        for keyword in keywords:
            keyword = keyword.lower()
            for item in self.menu_items:
                if keyword in item.name.lower() and item.id not in matched_items:
                    matched_items[item.id] = item
                    
                    if len(matched_items) >= max_items:
                        break
            
            if len(matched_items) >= max_items:
                break
        
        # If we don't have enough matches, add some random items
        if len(matched_items) < max_items:
            remaining_items = [item for item in self.menu_items if item.id not in matched_items]
            import random
            additional_items = random.sample(remaining_items, min(max_items - len(matched_items), len(remaining_items)))
            
            for item in additional_items:
                matched_items[item.id] = item
        
        return [item.to_dict() for item in matched_items.values()]