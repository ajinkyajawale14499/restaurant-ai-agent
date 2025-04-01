import React, { useState } from 'react';
import './App.css';
import Chat from './components/Chat';

const App: React.FC = () => {
  const [showDebug, setShowDebug] = useState(false);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Green Garden Restaurant</h1>
        <p>AI-Powered Restaurant Assistant</p>
        <button 
          onClick={() => setShowDebug(!showDebug)} 
          className="debug-toggle"
        >
          {showDebug ? 'Hide Debug' : 'Show Debug'}
        </button>
      </header>
      <main>
        <Chat />
      </main>
      <footer>
        <p>&copy; 2025 Green Garden Restaurant. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default App; 