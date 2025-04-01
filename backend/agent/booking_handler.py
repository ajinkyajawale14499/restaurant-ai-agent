# agent/booking_handler.py
import datetime
import re
from models import TableAvailability, TableBooking

class BookingHandler:
    """
    Handles table booking functionality
    """
    
    def __init__(self, session):
        self.session = session
    
    def get_available_dates(self, days_ahead=7):
        """
        Get a list of dates with available tables
        
        Args:
            days_ahead (int): Number of days to look ahead
            
        Returns:
            list: List of dates with available tables
        """
        today = datetime.datetime.now().date()
        date_list = []
        
        for i in range(days_ahead):
            check_date = today + datetime.timedelta(days=i)
            date_str = check_date.strftime('%Y-%m-%d')
            
            # Check if there are available tables for this date
            availability = self.session.query(TableAvailability).filter(
                TableAvailability.date == date_str,
                TableAvailability.available > 0
            ).first()
            
            if availability:
                date_list.append({
                    'date': date_str,
                    'display': check_date.strftime('%A, %B %d, %Y')
                })
        
        return date_list
    
    def get_available_times(self, date):
        """
        Get available time slots for a specific date
        
        Args:
            date (str): Date string in format 'YYYY-MM-DD'
            
        Returns:
            list: List of available time slots
        """
        availabilities = self.session.query(TableAvailability).filter(
            TableAvailability.date == date,
            TableAvailability.available > 0
        ).all()
        
        return [
            {
                'time': a.time,
                'available': a.available
            }
            for a in availabilities
        ]
    
    def is_table_available(self, date, time, guests):
        """
        Check if a table is available for the given date, time, and number of guests
        
        Args:
            date (str): Date string in format 'YYYY-MM-DD'
            time (str): Time string in format 'HH:MM AM/PM'
            guests (int): Number of guests
            
        Returns:
            bool: True if a table is available, False otherwise
        """
        # Find the closest matching time
        availability = self.session.query(TableAvailability).filter(
            TableAvailability.date == date,
            TableAvailability.time == time
        ).first()
        
        if not availability:
            return False
        
        # Simple logic: 1 table can accommodate up to 4 guests
        # For larger parties, we need more tables
        tables_needed = (guests + 3) // 4  # Ceiling division
        
        return availability.available >= tables_needed
    
    def create_booking(self, customer_info, booking_details):
        """
        Create a new table booking in the database
        
        Args:
            customer_info (dict): Customer information (name, email, phone)
            booking_details (dict): Booking details (date, time, guests, special_requests)
            
        Returns:
            TableBooking: The created booking object
        """
        # Check availability first
        date = booking_details.get('date')
        time = booking_details.get('time')
        guests = booking_details.get('guests', 1)
        
        if not self.is_table_available(date, time, guests):
            raise ValueError(f"No tables available for {guests} guests on {date} at {time}")
        
        # Create booking
        booking = TableBooking(
            customer_name=customer_info.get('name', 'Guest'),
            customer_email=customer_info.get('email'),
            customer_phone=customer_info.get('phone'),
            date=date,
            time=time,
            guests=guests,
            special_requests=booking_details.get('special_requests', ''),
            status='confirmed'
        )
        
        self.session.add(booking)
        
        # Update table availability
        tables_needed = (guests + 3) // 4  # Ceiling division
        
        availability = self.session.query(TableAvailability).filter(
            TableAvailability.date == date,
            TableAvailability.time == time
        ).first()
        
        if availability:
            availability.available -= tables_needed
        
        # Commit transaction
        self.session.commit()
        
        return booking
    
    def parse_date(self, date_str):
        """
        Parse date string into a standardized format
        
        Args:
            date_str (str): Date string from user input
            
        Returns:
            str: Standardized date string in format 'YYYY-MM-DD'
        """
        today = datetime.datetime.now().date()
        
        # Handle relative dates
        if date_str.lower() == 'today':
            return today.strftime('%Y-%m-%d')
        elif date_str.lower() == 'tomorrow':
            return (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        elif date_str.lower() == 'day after tomorrow':
            return (today + datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        
        # Handle day names (e.g., "next Monday")
        days = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 
                'friday': 4, 'saturday': 5, 'sunday': 6}
        
        for day, day_num in days.items():
            if day in date_str.lower():
                days_ahead = (day_num - today.weekday()) % 7
                if 'next' in date_str.lower() and days_ahead == 0:
                    days_ahead = 7
                return (today + datetime.timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        # Try various date formats
        formats = [
            '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%d-%m-%Y',
            '%m/%d/%y', '%m-%d-%y', '%d/%m/%y', '%d-%m-%y',
            '%b %d', '%B %d'
        ]
        
        for fmt in formats:
            try:
                if '%y' in fmt or '%Y' in fmt:
                    date_obj = datetime.datetime.strptime(date_str, fmt).date()
                else:
                    # For formats without year, assume current year
                    date_parts = datetime.datetime.strptime(date_str, fmt)
                    date_obj = date_parts.replace(year=today.year).date()
                    
                    # If the date is in the past, assume next year
                    if date_obj < today:
                        date_obj = date_obj.replace(year=today.year + 1)
                
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # If we can't parse the date, return None
        return None
    
    def parse_time(self, time_str):
        """
        Parse time string into a standardized format
        
        Args:
            time_str (str): Time string from user input
            
        Returns:
            str: Standardized time string in format 'HH:MM AM/PM'
        """
        # Handle special time names
        if time_str.lower() == 'noon':
            return '12:00 PM'
        elif time_str.lower() == 'midnight':
            return '12:00 AM'
        
        # Handle meal times
        meal_times = {
            'breakfast': '9:00 AM',
            'brunch': '11:00 AM',
            'lunch': '1:00 PM',
            'dinner': '7:00 PM'
        }
        
        for meal, time in meal_times.items():
            if meal in time_str.lower():
                return time
        
        # Handle time periods
        periods = {
            'morning': '10:00 AM',
            'afternoon': '2:00 PM',
            'evening': '7:00 PM',
            'night': '8:00 PM'
        }
        
        for period, time in periods.items():
            if period in time_str.lower():
                return time
        
        # Try to parse time formats
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)?',  # 7:30, 7:30am, 7:30 pm
            r'(\d{1,2})\s*(am|pm)',           # 7am, 7 pm
            r'(\d{1,2})\s*o\'?clock\s*(am|pm)?' # 7 o'clock, 7 o'clock pm
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, time_str.lower())
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if len(match.groups()) > 1 and match.group(2) and match.group(2).isdigit() else 0
                
                # Determine AM/PM
                am_pm = match.group(3) if len(match.groups()) > 2 and match.group(3) else None
                if not am_pm:
                    # Default to PM for hours between 5-11, AM otherwise
                    am_pm = 'PM' if 5 <= hour <= 11 else 'AM'
                else:
                    am_pm = am_pm.upper()
                
                # Adjust hour for 12-hour format
                if am_pm == 'PM' and hour < 12:
                    hour += 12
                elif am_pm == 'AM' and hour == 12:
                    hour = 0
                
                # Convert back to 12-hour format for display
                display_hour = hour % 12
                if display_hour == 0:
                    display_hour = 12
                
                return f"{display_hour}:{minute:02d} {'AM' if hour < 12 else 'PM'}"
        
        # If we can't parse the time, return None
        return None
    
    def parse_guests(self, guests_str):
        """
        Parse number of guests from string
        
        Args:
            guests_str (str): String representing number of guests
            
        Returns:
            int: Number of guests
        """
        # Handle numeric values
        if guests_str.isdigit():
            return int(guests_str)
        
        # Handle word numbers
        word_to_number = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12, 'dozen': 12
        }
        
        guests_str = guests_str.lower()
        for word, number in word_to_number.items():
            if word == guests_str:
                return number
        
        # Handle special cases
        if 'couple' in guests_str:
            return 2
        elif 'few' in guests_str:
            return 3
        elif 'several' in guests_str:
            return 4
        
        # Default to 1 if we can't determine
        return 1