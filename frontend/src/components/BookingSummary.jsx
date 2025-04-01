import React from 'react';
import './BookingSummary.css';

const BookingSummary = ({ booking }) => {
  const isConfirmed = booking.id || booking.booking_id;
  
  // Format date - handle different possible formats
  const formatDate = (dateString) => {
    try {
      if (!dateString) return 'N/A';
      
      // Check if the date is in YYYY-MM-DD format
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
        const [year, month, day] = dateString.split('-');
        return new Date(year, month - 1, day).toLocaleDateString();
      }
      
      return new Date(dateString).toLocaleDateString();
    } catch (e) {
      return dateString; // Return as is if parsing fails
    }
  };

  return (
    <div className="booking-summary">
      <h2>{isConfirmed ? 'Reservation Confirmed' : 'Current Reservation'}</h2>
      
      <div className="booking-details">
        <div className="booking-detail">
          <span className="label">Date:</span>
          <span className="value">{formatDate(booking.date)}</span>
        </div>
        
        <div className="booking-detail">
          <span className="label">Time:</span>
          <span className="value">{booking.time}</span>
        </div>
        
        <div className="booking-detail">
          <span className="label">Guests:</span>
          <span className="value">{booking.guests}</span>
        </div>
        
        {isConfirmed && (
          <>
            <div className="booking-detail">
              <span className="label">Reservation #:</span>
              <span className="value confirmation-number">{booking.id || booking.booking_id}</span>
            </div>
            
            {booking.customer_name && (
              <div className="booking-detail">
                <span className="label">Name:</span>
                <span className="value">{booking.customer_name}</span>
              </div>
            )}
            
            {booking.booking_date && (
              <div className="booking-detail">
                <span className="label">Booked On:</span>
                <span className="value">{new Date(booking.booking_date).toLocaleString()}</span>
              </div>
            )}
            
            {booking.status && (
              <div className="booking-detail">
                <span className="label">Status:</span>
                <span className={`value status ${booking.status.toLowerCase()}`}>
                  {booking.status}
                </span>
              </div>
            )}
          </>
        )}
        
        {booking.special_requests && (
          <div className="booking-detail special-requests">
            <span className="label">Special Requests:</span>
            <span className="value">{booking.special_requests}</span>
          </div>
        )}
      </div>
      
      {isConfirmed ? (
        <div className="confirmation-message">
          <p>Your table reservation is confirmed!</p>
          <p>Please arrive 10 minutes before your reservation time.</p>
          {booking.status === 'confirmed' && (
            <p className="cancel-info">
              If you need to cancel or modify your reservation,
              please contact us at least 2 hours in advance.
            </p>
          )}
        </div>
      ) : (
        <p className="booking-instructions">
          Continue chatting with our AI assistant to complete your reservation.
        </p>
      )}
    </div>
  );
};

export default BookingSummary;