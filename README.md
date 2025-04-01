### Backend Setup
```
Navigate to the backend directory:
cd restaurant-ai-agent/backend

Create a virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Run the Flask application:
python app.py
The backend will start on http://localhost:5000

```

### Project structure
```
restaurant-ai-agent/
├── backend/
│   ├── app.py                  # Main Flask application
│   ├── models.py               # Database models
│   ├── database.py             # Database setup
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── intent_classifier.py  # Identifies user intents
│   │   ├── order_handler.py    # Handles food orders
│   │   ├── booking_handler.py  # Handles table bookings
│   │   └── response_generator.py # Generates chatbot responses
│   ├── config.py               # Configuration settings
│   ├── data/
│   │   ├── menu.json           # Restaurant menu
│   │   └── tables.json         # Table availability
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.js         # Chat interface
│   │   │   ├── OrderSummary.js # Order summary component
│   │   │   └── BookingSummary.js # Booking summary component
│   │   ├── App.js              # Main React component
│   │   ├── index.js            # Entry point
│   │   └── styles/             # CSS styles
│   ├── package.json
│   └── README.md
└── README.md                   # Project documentation
```

### Frontend Setup
```
Navigate to the frontend directory:

cd restaurant-ai-agent/frontend

Install dependencies:
npm install

Start the development server:
npm start
The frontend will start on http://localhost:5173/

```
