# config.py
import os

# Flask configuration
DEBUG = True
SECRET_KEY = os.environ.get('SECRET_KEY') or 'development-key'

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///restaurant.db'

# Restaurant configuration
RESTAURANT_NAME = "Green Garden Vegetarian"
RESTAURANT_ADDRESS = "123 Veggies Ave, Plant City"
RESTAURANT_PHONE = "+1 (555) 123-4567"
RESTAURANT_EMAIL = "info@greengarden.com"
RESTAURANT_HOURS = {
    "Monday": "11:00 AM - 9:00 PM",
    "Tuesday": "11:00 AM - 9:00 PM",
    "Wednesday": "11:00 AM - 9:00 PM",
    "Thursday": "11:00 AM - 10:00 PM",
    "Friday": "11:00 AM - 11:00 PM",
    "Saturday": "10:00 AM - 11:00 PM",
    "Sunday": "10:00 AM - 9:00 PM"
}

# CORS configuration
CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:5173', 'http://127.0.0.1:5173']