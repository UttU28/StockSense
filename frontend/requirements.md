## Packages
framer-motion | Smooth layout animations and interactions
react-hook-form | Form state management
@hookform/resolvers | Zod resolver for react-hook-form

## Notes
- Dark mode default design
- Using standard dialog/modal pattern for creation
- Framer motion used for list entry animations

## Running with Stock Gita backend

**Two steps:**

1. **Start the backend** (from project root, in one terminal):
   - **Windows:** `run_backend.bat`  
     or: `set PYTHONPATH=.` then `python stock_gita_engine_charts/api_bridge.py`
   - **Mac/Linux:** `./run_backend.sh`  
     or: `PYTHONPATH=. python stock_gita_engine_charts/api_bridge.py`
   - Backend runs at **http://localhost:8000**

2. **Start the frontend** (in a second terminal):
   - `cd frontend`
   - `npm run dev`
   - Open the URL shown (e.g. **http://localhost:5173**), then go to **Open Chat** or **/chat**

The frontend proxies `/v1` and `/api` to the backend. For production, set `VITE_API_URL` to your backend URL before `npm run build`.
