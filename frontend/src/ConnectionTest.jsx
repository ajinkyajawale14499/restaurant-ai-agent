import React, { useState, useEffect } from 'react';
import apiService from '../apiService';

const ConnectionTest = () => {
  const [status, setStatus] = useState('Checking connection...');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const testConnection = async () => {
      try {
        // First test the health endpoint
        const healthResponse = await apiService.health.check();
        
        if (healthResponse.status === 200) {
          setStatus('Connected to backend! Health check successful.');
          
          // Try to get the menu as a second test
          try {
            const menuResponse = await apiService.menu.getMenu();
            if (menuResponse.data && menuResponse.data.menu) {
              setStatus(prev => prev + ` Retrieved ${menuResponse.data.menu.length} menu items.`);
            }
          } catch (menuError) {
            console.error('Menu retrieval error:', menuError);
            // Still consider connected even if menu retrieval fails
          }
        } else {
          setStatus(`Unexpected response from backend: ${healthResponse.status}`);
        }
      } catch (e) {
        console.error('Connection test error:', e);
        setError(e);
        setStatus('Failed to connect to backend.');
      } finally {
        setLoading(false);
      }
    };

    testConnection();
  }, []);

  return (
    <div className="connection-test">
      <h3>Backend Connection Status</h3>
      <div className={`status ${loading ? 'loading' : error ? 'error' : 'success'}`}>
        {status}
      </div>
      
      {error && (
        <div className="error-details">
          <p>Error details:</p>
          <pre>{error.message}</pre>
          {error.response && (
            <div>
              <p>Response: {error.response.status}</p>
              <pre>{JSON.stringify(error.response.data, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
      
      <style jsx>{`
        .connection-test {
          margin: 20px 0;
          padding: 15px;
          border-radius: 8px;
          background-color: #f5f5f5;
          text-align: center;
        }
        
        .status {
          margin: 10px 0;
          padding: 10px;
          border-radius: 4px;
        }
        
        .loading {
          background-color: #fff8e1;
          color: #856404;
        }
        
        .error {
          background-color: #f8d7da;
          color: #721c24;
        }
        
        .success {
          background-color: #d4edda;
          color: #155724;
        }
        
        .error-details {
          margin-top: 15px;
          text-align: left;
          background-color: #f8f9fa;
          padding: 10px;
          border-radius: 4px;
          overflow: auto;
        }
        
        pre {
          white-space: pre-wrap;
          word-break: break-all;
        }
      `}</style>
    </div>
  );
};

export default ConnectionTest;