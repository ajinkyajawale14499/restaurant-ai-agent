import React, { useState, useEffect, useRef } from 'react';
import './Chat.css';
import MenuDisplay from './MenuDisplay';
import OrderSummary from './OrderSummary';
import BookingSummary from './BookingSummary';
import apiService from '../apiService';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [menuItems, setMenuItems] = useState([]);
  const [currentOrder, setCurrentOrder] = useState(null);
  const [currentBooking, setCurrentBooking] = useState(null);
  const messagesEndRef = useRef(null);

  // Add initial welcome message
  useEffect(() => {
    setMessages([
      {
        text: "Welcome to Green Garden Restaurant! I'm your AI assistant. How can I help you today? You can ask me about our menu, place an order, or make a table reservation.",
        sender: 'bot',
        timestamp: new Date().toISOString()
      }
    ]);
  }, []);

  // Scroll to bottom of messages
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message to chat
    const userMessage = {
      text: input,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Send message to backend using the apiService
      const response = await apiService.chat.sendMessage(input, sessionId);
      console.log('API Response:', response); // Debug log

      // Store session ID if not already set
      if (!sessionId && response.data.session_id) {
        setSessionId(response.data.session_id);
      }

      // Add bot response to chat
      const botResponse = {
        text: response.data.response.text,
        sender: 'bot',
        timestamp: new Date().toISOString(),
        data: response.data.response
      };
      setMessages(prevMessages => [...prevMessages, botResponse]);

      // Process additional data in response
      processResponseData(response.data.response);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      setMessages(prevMessages => [
        ...prevMessages, 
        {
          text: `Sorry, there was an error processing your request: ${error.message}`,
          sender: 'bot',
          timestamp: new Date().toISOString(),
          isError: true
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const processResponseData = (response) => {
    // Handle menu display
    if (response.menu) {
      setMenuItems(response.menu);
      setShowMenu(true);
    } else {
      setShowMenu(false);
    }

    // Handle order data
    if (response.items) {
      setCurrentOrder({
        items: response.items,
        total: response.total || response.items.reduce((sum, item) => sum + (item.price * item.quantity), 0)
      });
    } else if (response.order) {
      setCurrentOrder(response.order);
    }

    // Handle booking data
    if (response.booking) {
      setCurrentBooking(response.booking);
    }
  };

  const formatMessage = (message) => {
    // Split message by newlines to handle formatting
    return message.text.split('\n').map((line, index) => (
      <span key={index}>
        {line}
        <br />
      </span>
    ));
  };

  const handleQuickReply = (text) => {
    setInput(text);
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'} ${message.isError ? 'error' : ''}`}
          >
            <div className="message-content">
              {formatMessage(message)}
            </div>
            <div className="message-timestamp">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message bot-message typing">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {showMenu && menuItems.length > 0 && (
        <div className="menu-container">
          <MenuDisplay menuItems={menuItems} onSelectItem={handleQuickReply} />
        </div>
      )}

      {currentOrder && (
        <div className="order-summary-container">
          <OrderSummary order={currentOrder} />
        </div>
      )}

      {currentBooking && (
        <div className="booking-summary-container">
          <BookingSummary booking={currentBooking} />
        </div>
      )}

      <form onSubmit={handleSubmit} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={handleInputChange}
          placeholder="Type your message here..."
          className="chat-input"
          disabled={isLoading}
        />
        <button type="submit" className="chat-send-button" disabled={isLoading}>
          Send
        </button>
      </form>

      <div className="quick-replies">
        <button onClick={() => handleQuickReply("Show me the menu")}>Show Menu</button>
        <button onClick={() => handleQuickReply("I want to order food")}>Order Food</button>
        <button onClick={() => handleQuickReply("I'd like to make a reservation")}>Book Table</button>
      </div>
    </div>
  );
};

export default Chat;