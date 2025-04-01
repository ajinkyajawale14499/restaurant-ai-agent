# database.py
import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, MenuItem, TableAvailability

# Create database engine with connect_args to make it thread-safe
DATABASE_URL = "sqlite:///restaurant.db"
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},  # This is the critical fix
    pool_pre_ping=True,  # This helps with connection validation
    pool_recycle=3600    # Recycle connections every hour
)

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)  # scoped_session handles thread-local sessions

def init_db():
    """Initialize the database"""
    # Create tables
    Base.metadata.create_all(engine)
    
    # Seed database with initial data if tables are empty
    session = Session()
    try:
        # Check if menu items exist
        if session.query(MenuItem).count() == 0:
            load_menu_data(session)
        
        # Check if table availability exists
        if session.query(TableAvailability).count() == 0:
            load_table_data(session)
            
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error initializing database: {e}")
    finally:
        session.close()

def load_menu_data(session):
    """Load menu data from JSON file"""
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'menu.json')
        with open(data_path, 'r') as f:
            menu_data = json.load(f)
            
        for item in menu_data:
            menu_item = MenuItem(
                id=item['id'],
                name=item['name'],
                price=item['price']
            )
            session.add(menu_item)
            
    except Exception as e:
        print(f"Error loading menu data: {e}")
        raise

def load_table_data(session):
    """Load table availability data from JSON file"""
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'tables.json')
        with open(data_path, 'r') as f:
            tables_data = json.load(f)
            
        for date, times in tables_data.items():
            for time, availability in times.items():
                table_availability = TableAvailability(
                    date=date,
                    time=time,
                    available=availability['available']
                )
                session.add(table_availability)
                
    except Exception as e:
        print(f"Error loading table data: {e}")
        raise

def get_session():
    """Get a database session"""
    return Session()