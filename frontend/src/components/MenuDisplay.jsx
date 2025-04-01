import React, { useState } from 'react';
import './MenuDisplay.css';

const MenuDisplay = ({ menuItems, onSelectItem }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');

  // Categories would ideally come from the backend, but for simplicity we'll derive them
  const categories = [
    'all',
    ...new Set(menuItems.map(item => {
      // Simple categorization based on item name
      if (item.name.toLowerCase().includes('pizza') || item.name.toLowerCase().includes('bread')) return 'pizza';
      if (item.name.toLowerCase().includes('salad')) return 'salad';
      if (item.name.toLowerCase().includes('soup')) return 'soup';
      if (item.name.toLowerCase().includes('pasta') || item.name.toLowerCase().includes('noodle') || item.name.toLowerCase().includes('lasagna') || item.name.toLowerCase().includes('ravioli') || item.name.toLowerCase().includes('gnocchi')) return 'pasta';
      if (item.name.toLowerCase().includes('sandwich') || item.name.toLowerCase().includes('wrap') || item.name.toLowerCase().includes('taco')) return 'sandwiches';
      if (item.name.toLowerCase().includes('curry') || item.name.toLowerCase().includes('masala') || item.name.toLowerCase().includes('biryani')) return 'indian';
      if (item.name.toLowerCase().includes('pad thai') || item.name.toLowerCase().includes('tempura') || item.name.toLowerCase().includes('sushi')) return 'asian';
      return 'other';
    }))
  ];

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleCategoryChange = (category) => {
    setCategoryFilter(category);
  };

  const handleSelectItem = (item) => {
    onSelectItem(`I would like to order ${item.name}`);
  };

  const filteredItems = menuItems.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (categoryFilter === 'all') {
      return matchesSearch;
    }
    
    const itemCategory = (() => {
      if (item.name.toLowerCase().includes('pizza') || item.name.toLowerCase().includes('bread')) return 'pizza';
      if (item.name.toLowerCase().includes('salad')) return 'salad';
      if (item.name.toLowerCase().includes('soup')) return 'soup';
      if (item.name.toLowerCase().includes('pasta') || item.name.toLowerCase().includes('noodle') || item.name.toLowerCase().includes('lasagna') || item.name.toLowerCase().includes('ravioli') || item.name.toLowerCase().includes('gnocchi')) return 'pasta';
      if (item.name.toLowerCase().includes('sandwich') || item.name.toLowerCase().includes('wrap') || item.name.toLowerCase().includes('taco')) return 'sandwiches';
      if (item.name.toLowerCase().includes('curry') || item.name.toLowerCase().includes('masala') || item.name.toLowerCase().includes('biryani')) return 'indian';
      if (item.name.toLowerCase().includes('pad thai') || item.name.toLowerCase().includes('tempura') || item.name.toLowerCase().includes('sushi')) return 'asian';
      return 'other';
    })();
    
    return matchesSearch && itemCategory === categoryFilter;
  });

  return (
    <div className="menu-display">
      <h2>Menu</h2>
      
      <div className="menu-filters">
        <input
          type="text"
          className="menu-search"
          placeholder="Search menu..."
          value={searchTerm}
          onChange={handleSearchChange}
        />
        
        <div className="category-filters">
          {categories.map(category => (
            <button
              key={category}
              className={`category-button ${categoryFilter === category ? 'active' : ''}`}
              onClick={() => handleCategoryChange(category)}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>
      </div>
      
      <div className="menu-items-list">
        {filteredItems.length === 0 ? (
          <p className="no-items">No items found matching your criteria.</p>
        ) : (
          filteredItems.map(item => (
            <div key={item.id} className="menu-item" onClick={() => handleSelectItem(item)}>
              <div className="menu-item-content">
                <div className="menu-item-name">{item.name}</div>
                <div className="menu-item-price">${item.price.toFixed(2)}</div>
              </div>
              <button className="order-button">Order</button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default MenuDisplay;