# models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class MenuItem(Base):
    __tablename__ = 'menu_items'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price
        }

class TableAvailability(Base):
    __tablename__ = 'table_availability'
    
    id = Column(Integer, primary_key=True)
    date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    time = Column(String(10), nullable=False)  # Format: HH:MM AM/PM
    available = Column(Integer, nullable=False, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'time': self.time,
            'available': self.available
        }

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100))
    customer_phone = Column(String(20))
    total_amount = Column(Float, nullable=False)
    order_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20), default='pending')  # pending, confirmed, delivered, cancelled
    
    items = relationship("OrderItem", back_populates="order")
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'total_amount': self.total_amount,
            'order_date': self.order_date.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    menu_item_id = Column(Integer, ForeignKey('menu_items.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Float, nullable=False)  # Price at the time of order
    
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem")
    
    def to_dict(self):
        return {
            'id': self.id,
            'menu_item_id': self.menu_item_id,
            'menu_item_name': self.menu_item.name if self.menu_item else None,
            'quantity': self.quantity,
            'price': self.price
        }

class TableBooking(Base):
    __tablename__ = 'table_bookings'
    
    id = Column(Integer, primary_key=True)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100))
    customer_phone = Column(String(20))
    date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    time = Column(String(10), nullable=False)  # Format: HH:MM AM/PM
    guests = Column(Integer, nullable=False)
    special_requests = Column(Text)
    booking_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20), default='confirmed')  # confirmed, cancelled
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'date': self.date,
            'time': self.time,
            'guests': self.guests,
            'special_requests': self.special_requests,
            'booking_date': self.booking_date.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status
        }

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), nullable=False)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_message': self.user_message,
            'bot_response': self.bot_response,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }