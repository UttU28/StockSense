# GS Trading System Frontend

React + TypeScript frontend for the GS Trading System API.

## Features

- **Stock Analysis**: Get detailed technical analysis, entry signals, and position sizing
- **Backtesting**: Test strategies on historical data with performance metrics
- **Market Scanner**: Scan multiple stocks for trading opportunities
- **Real-time Data**: Fetch live stock prices and indicators
- **Beautiful UI**: Modern dark theme with smooth animations

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure API URL

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8001
```

Or the API URL will default to `http://localhost:8001` if not set.

### 3. Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the next available port).

### 4. Make Sure Backend is Running

Before using the frontend, ensure the FastAPI backend is running:

```bash
# In the root gs_system directory
python app.py
```

The backend should be running at `http://localhost:8001`.

## Usage

### Analyze Tab

1. Enter a stock symbol (e.g., AAPL, TSLA)
2. Set your account size
3. Click "Analyze" to get:
   - Technical indicators (RSI, MACD, ATR, etc.)
   - Market bias and confidence
   - Entry signals and tier rating
   - Position sizing recommendations
   - Stop loss and take profit levels

### Backtest Tab

1. Enter a stock symbol
2. Set account size and number of days to backtest
3. Click "Backtest" to see:
   - Total trades executed
   - Win rate percentage
   - Total profit/loss
   - Final equity
   - Detailed trade log with entry/exit dates

### Scan Tab

1. Enter comma-separated symbols (or leave empty for default watchlist)
2. Set account size
3. Click "Scan" to find:
   - Trading opportunities sorted by confidence
   - Entry signals for multiple stocks
   - Position sizing for each opportunity

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── hooks/          # Custom React hooks
│   ├── lib/            # Utilities and API client
│   ├── pages/           # Page components
│   └── App.tsx          # Main app component
├── public/              # Static assets
└── package.json         # Dependencies
```

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Technologies Used

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI component library
- **Recharts** - Chart library
- **Framer Motion** - Animations
- **Wouter** - Routing

## API Integration

The frontend communicates with the FastAPI backend through the `api.ts` service file. All API calls are typed and handle errors gracefully.

See `src/lib/api.ts` for the API client implementation.

