import React from 'react';
import './OrderSummary.css';

const OrderSummary = ({ order }) => {
  // Handle different order data structures
  const items = order.items || [];
  const total = order.total || order.total_amount || 
                items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  
  // Check if this is a confirmed order with order ID
  const isConfirmed = order.id || order.order_id;
  
  return (
    <div className="order-summary">
      <h2>{isConfirmed ? 'Order Confirmed' : 'Current Order'}</h2>
      
      {isConfirmed && (
        <div className="order-info">
          <p className="order-id">Order #{order.id || order.order_id}</p>
          {order.customer_name && <p>Name: {order.customer_name}</p>}
          {order.order_date && <p>Date: {new Date(order.order_date).toLocaleString()}</p>}
          {order.status && <p className="order-status">Status: {order.status}</p>}
        </div>
      )}
      
      <div className="order-items">
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => {
              // Handle different item data structures
              const name = item.name || item.menu_item_name || 'Unknown Item';
              const quantity = item.quantity || 1;
              const price = item.price || 0;
              const itemTotal = price * quantity;
              
              return (
                <tr key={index}>
                  <td>{name}</td>
                  <td>{quantity}</td>
                  <td>${price.toFixed(2)}</td>
                  <td>${itemTotal.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan="3">Total</td>
              <td>${total.toFixed(2)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
      
      {isConfirmed ? (
        <div className="confirmation-message">
          <p>Thank you for your order!</p>
          {!order.delivery_address && (
            <p>Your order will be ready for pickup in approximately 30 minutes.</p>
          )}
        </div>
      ) : (
        <p className="order-instructions">
          Continue chatting with our AI assistant to complete your order.
        </p>
      )}
    </div>
  );
};

export default OrderSummary;