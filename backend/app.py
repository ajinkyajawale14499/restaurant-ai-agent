# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

from database import init_db, get_session
from agent import RestaurantAgent
import config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config)

# IMPORTANT: Do NOT use both CORS and custom headers at the same time
# Comment out the CORS initialization completely to avoid conflicts
# CORS(app, 
#     resources={r"/*": {"origins": config.CORS_ORIGINS}},
#     supports_credentials=True)

# Use ONLY the after_request handler for CORS
@app.after_request
def add_cors_headers(response):
    # Get the origin from the request
    origin = request.headers.get('Origin', '')
    
    # Set the Access-Control-Allow-Origin header to match the exact origin
    if origin in ['http://localhost:5173', 'http://127.0.0.1:5173']:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        # For other origins, use the default
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
    
    # Add other CORS headers
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Initialize database
init_db()

# Get restaurant info from config
restaurant_info = {
    'name': config.RESTAURANT_NAME,
    'address': config.RESTAURANT_ADDRESS,
    'phone': config.RESTAURANT_PHONE,
    'email': config.RESTAURANT_EMAIL,
    'hours': config.RESTAURANT_HOURS
}

# Initialize agent
session = get_session()
agent = RestaurantAgent(session, restaurant_info)

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    """
    Process a chat message from the user
    
    Request:
    {
        "message": "User message text",
        "session_id": "Optional session ID for conversation tracking"
    }
    
    Response:
    {
        "response": {
            "text": "Bot response text",
            ... (additional context data)
        },
        "session_id": "Session ID for conversation tracking"
    }
    """
    # Handle preflight OPTIONS requests
    if request.method == 'OPTIONS':
        return jsonify(success=True)
        
    try:
        data = request.json
        message = data.get('message', '')
        session_id = data.get('session_id')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Process message with agent
        response = agent.process_message(message, session_id)
        
        # Get conversation
        conversation = agent.get_or_create_conversation(session_id)
        
        return jsonify({
            'response': response,
            'session_id': conversation['session_id']
        })
    except Exception as e:
        # Log the error
        app.logger.error(f"Error processing chat request: {str(e)}")
        # Return a user-friendly error response
        return jsonify({
            'error': 'An error occurred processing your request',
            'message': str(e)
        }), 500

@app.route('/api/menu', methods=['GET'])
def get_menu():
    """Get the restaurant menu"""
    from models import MenuItem
    session = get_session()
    menu_items = session.query(MenuItem).all()
    
    return jsonify({
        'menu': [item.to_dict() for item in menu_items]
    })

@app.route('/api/availability', methods=['GET'])
def get_availability():
    """Get table availability"""
    date = request.args.get('date')
    
    session = get_session()
    booking_handler = agent.booking_handler
    
    if date:
        # Get availability for specific date
        available_times = booking_handler.get_available_times(date)
        return jsonify({
            'date': date,
            'available_times': available_times
        })
    else:
        # Get dates with availability
        available_dates = booking_handler.get_available_dates()
        return jsonify({
            'available_dates': available_dates
        })

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get all orders (for admin purposes)"""
    from models import Order
    session = get_session()
    orders = session.query(Order).all()
    
    return jsonify({
        'orders': [order.to_dict() for order in orders]
    })

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    """Get all bookings (for admin purposes)"""
    from models import TableBooking
    session = get_session()
    bookings = session.query(TableBooking).all()
    
    return jsonify({
        'bookings': [booking.to_dict() for booking in bookings]
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Server is running'
    })

if __name__ == '__main__':
    app.run(debug=True, threaded=True)