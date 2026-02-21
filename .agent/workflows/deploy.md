---
description: Deploy the V4 hybrid forecasting model with Flask backend and Vue frontend
---

## Architecture

### Backend (Flask API)
- Load V4 hybrid model (XGBoost + 3 DL residual models) + scalers at startup
- Feature engineering pipeline (replicates training exactly)
- SQLite database for forecast requests and results
- Weather API integration (Open-Meteo, free, no API key)
- Endpoints: /api/forecast, /api/history, /api/models, /api/evaluation

### Frontend (Vue 3 SPA)
- Page 1: Forecast Dashboard (date picker → 168h forecast chart)
- Page 2: History (past forecasts with charts + CSV download)
- Page 3: Model Evaluation Comparison
- Page 4: Model Training History
- Uses ECharts for premium charts

### Database (SQLite)
- Table: forecast_requests (id, start_date, end_date, created_at, status)
- Table: forecasted_results (id, request_id, hour_offset, timestamp, predicted_load, xgb_load)
