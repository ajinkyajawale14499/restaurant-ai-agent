# agent/response_generator.py
import random

class ResponseGenerator:
    """
    Generates natural language responses for the restaurant AI agent
    """
    
    def __init__(self, restaurant_info):
        self.restaurant_info = restaurant_info
        self.responses = self._initialize_responses()
        
    def _initialize_responses(self):
        """Initialize response templates"""
        return {
            'greeting': [
                f"Hello! Welcome to {self.restaurant_info['name']}. How can I help you today?",
                f"Hi there! Thanks for contacting {self.restaurant_info['name']}. What can I do for you?",
                f"Welcome to {self.restaurant_info['name']}! Would you like to place an order or make a reservation?"
            ],
            'farewell': [
                "Thank you for your time! Have a great day!",
                "Thanks for chatting with us. Come back soon!",
                f"Thank you for choosing {self.restaurant_info['name']}. We look forward to serving you!"
            ],
            'unknown': [
                "I'm sorry, I didn't understand that. Can you please rephrase?",
                "I'm not sure what you're asking for. Would you like to place an order or make a reservation?",
                "I didn't catch that. How can I help you today?"
            ],
            'order_inquiry': [
                "Would you like to place an order for delivery or takeout?",
                "What would you like to order today?",
                "I'd be happy to take your order. What would you like to have?"
            ],
            'booking_inquiry': [
                "Would you like to make a table reservation? I can help with that.",
                "I can assist you with booking a table. How many people will be dining and when?",
                "When would you like to reserve a table, and for how many people?"
            ],
            'menu_inquiry': [
                f"Here's our menu at {self.restaurant_info['name']}:",
                "Let me show you our current menu:",
                "Here are the dishes we offer:"
            ],
            'order_confirmation': [
                "Great! I've placed your order. Your order number is {order_id}.",
                "Your order has been confirmed! Order #{order_id} will be ready at {time}.",
                "Thank you for your order! We've got everything set for Order #{order_id}."
            ],
            'booking_confirmation': [
                "Perfect! Your table for {guests} is booked for {date} at {time}.",
                "Great! I've reserved a table for {guests} on {date} at {time}.",
                "Your reservation is confirmed for {guests} on {date} at {time}. We look forward to seeing you!"
            ],
            'order_details_request': [
                "Can you please confirm what items you'd like to order?",
                "What dishes would you like to include in your order?",
                "Please let me know the specific items you'd like to order."
            ],
            'booking_details_request': [
                "What date and time would you like to book a table for?",
                "How many people will be dining, and when would you like to come?",
                "Please let me know the date, time, and number of guests for your reservation."
            ],
            'contact_request': [
                "Could I get your name and contact information for the {purpose}?",
                "May I have your name and a phone number for the {purpose}?",
                "What name should I put for the {purpose}, and how can we reach you?"
            ],
            'suggest_menu_items': [
                "Some of our popular items include: {items}",
                "Here are some dishes you might enjoy: {items}",
                "I recommend trying our: {items}"
            ],
            'suggest_times': [
                "We have tables available at the following times on {date}: {times}",
                "For {date}, we can offer you a table at: {times}",
                "These time slots are available on {date}: {times}"
            ],
            'no_availability': [
                "I'm sorry, we don't have any tables available at that time.",
                "Unfortunately, we're fully booked for that time slot.",
                "I apologize, but we don't have availability for that time and date."
            ],
            'alternative_suggestion': [
                "How about {alternative} instead?",
                "Would {alternative} work for you?",
                "Could I suggest {alternative} as an alternative?"
            ],
            'help': [
                f"I'm the {self.restaurant_info['name']} assistant. I can help you place an order or make a table reservation. What would you like to do?",
                "I can assist you with ordering food or booking a table. How can I help you today?",
                "You can ask me about our menu, place an order, or make a reservation. What would you like to do?"
            ],
            'hours_info': [
                f"Our hours are: {self.format_hours()}",
                f"{self.restaurant_info['name']} is open: {self.format_hours()}",
                f"We're open: {self.format_hours()}"
            ]
        }
    
    def format_hours(self):
        """Format restaurant hours for display"""
        hours_text = ""
        for day, hours in self.restaurant_info['hours'].items():
            hours_text += f"{day}: {hours}, "
        return hours_text.rstrip(", ")
    
    def get_response(self, response_type, **kwargs):
        """
        Get a response of the specified type with placeholders filled in
        
        Args:
            response_type (str): Type of response to generate
            **kwargs: Placeholder values
            
        Returns:
            str: Generated response
        """
        if response_type not in self.responses:
            response_type = 'unknown'
            
        templates = self.responses[response_type]
        template = random.choice(templates)
        
        # Fill in any placeholders
        try:
            return template.format(**kwargs)
        except KeyError:
            # If we're missing a placeholder value, fallback to a different template
            for t in templates:
                try:
                    return t.format(**kwargs)
                except KeyError:
                    continue
            
            # If all templates fail, return a generic response
            return "I understand. How else can I assist you?"
    
    def format_menu_items(self, items):
        """Format a list of menu items for display"""
        return ", ".join([f"{item['name']} (${item['price']:.2f})" for item in items])
    
    def format_order_summary(self, items, total):
        """Format order summary for display"""
        summary = "Here's your order summary:\n"
        for item in items:
            summary += f"- {item['quantity']}x {item['name']} (${item['price']:.2f} each)\n"
        summary += f"\nTotal: ${total:.2f}"
        return summary
    
    def format_booking_summary(self, booking_details):
        """Format booking summary for display"""
        summary = f"Table reservation for {booking_details['guests']} guests\n"
        summary += f"Date: {booking_details['date']}\n"
        summary += f"Time: {booking_details['time']}\n"
        
        if booking_details.get('special_requests'):
            summary += f"Special requests: {booking_details['special_requests']}\n"
            
        return summary
    
    def format_available_times(self, times):
        """Format available times for display"""
        return ", ".join([time['time'] for time in times])