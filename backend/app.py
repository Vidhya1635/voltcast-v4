"""
Flask backend API for Electricity Load Forecasting.
"""
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

import database as db
import weather
import features
import model_v4
import config
import market
from model_v4 import model_manager
from config import PREPROCESSED_CSV, MODEL_DIR

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Initialization (Lazy) ───────────────────────────────────────────
history_df_full = None

def get_history_data():
    global history_df_full
    if history_df_full is None:
        import gc
        print("🕒 Loading historical dataset (Memory Optimized)...")
        # Load with specific dtypes to save 50% memory
        history_df_full = pd.read_csv(PREPROCESSED_CSV)
        
        # Optimize types: int64/float64 -> int32/float32
        for col in history_df_full.select_dtypes(include=['float64']).columns:
            history_df_full[col] = history_df_full[col].astype('float32')
        for col in history_df_full.select_dtypes(include=['int64']).columns:
            history_df_full[col] = history_df_full[col].astype('int32')
            
        history_df_full['Timestamp'] = pd.to_datetime(history_df_full['Timestamp'])
        gc.collect() 
        print(f"✅ Data loaded. Memory usage: ~{history_df_full.memory_usage().sum() / 1e6:.1f} MB")
    return history_df_full

# Initialize database
db.init_db()

# Model manager is global, but we will call .load() inside functions
# instead of at startup to save memory on boot.

# ── Endpoints ────────────────────────────────────────────────────────

@app.route('/api/forecast', methods=['POST'])
def run_manual_forecast():
    """Manual forecast with date picker."""
    data = request.get_json() or {}
    if 'start_date' not in data:
        return jsonify({"error": "Missing start_date"}), 400
    try:
        req_start = datetime.strptime(data['start_date'], "%Y-%m-%d %H:%M")
        return run_forecast_logic(req_start, temp_offset=float(data.get('temp_offset', 0)))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/live-forecast', methods=['GET'])
def live_forecast():
    """Automatic forecast for 'Now'."""
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    # Note: If 'now' is outside our data range (e.g. 2026), 
    # run_forecast_logic will handle the fallback to 2025 automatically.
    return run_forecast_logic(now)

def run_forecast_logic(req_start, temp_offset=0):
    """Core forecasting engine used by both endpoints."""
    # 1. Validation & Windowing
    history_df = get_history_data()
    input_start = req_start - timedelta(hours=168)
    history_window = history_df[
        (history_df['Timestamp'] >= input_start) & 
        (history_df['Timestamp'] < req_start)
    ].copy()
    
    # 1b. Fallback for future dates (like 2026)
    if len(history_window) < 168:
        latest_year = history_df['Timestamp'].dt.year.max()
        try:
            fallback_start = req_start.replace(year=latest_year)
            input_start = fallback_start - timedelta(hours=168)
            history_window = history_df[
                (history_df['Timestamp'] >= input_start) & 
                (history_df['Timestamp'] < fallback_start)
            ].copy()
            if len(history_window) == 168:
                req_start = fallback_start
            else:
                history_window = history_df.tail(168).copy()
                req_start = history_window['Timestamp'].iloc[-1] + timedelta(hours=1)
        except:
            history_window = history_df.tail(168).copy()
            req_start = history_window['Timestamp'].iloc[-1] + timedelta(hours=1)

    # 2. Setup DB Request
    req_id = db.save_forecast_request(
        req_start.isoformat(), 
        (req_start + timedelta(hours=167)).isoformat(),
        input_start.isoformat(),
        req_start.isoformat()
    )

    try:
        # Load models lazily if not already done
        model_manager.load()
        
        # 3. Weather & What-If
        weather_forecast = weather.fetch_weather_forecast(req_start, hours=168)
        if temp_offset != 0:
            for city in weather_forecast:
                weather_forecast[city][f'Temp_{city}'] += temp_offset

        # 4. Prediction
        input_cols = model_manager.config['FEATURE_COLS']
        future_df = features.prepare_inference_data(history_window, weather_forecast, input_cols)
        preds = model_manager.predict(future_df)
        
        # 5. Market & Renewables
        solar_mw, wind_mw = market.estimate_renewables(weather_forecast)
        
        # 6. Formatting
        final_results = []
        primary_city = list(weather_forecast.keys())[0]
        weather_codes = weather_forecast[primary_city][f'Code_{primary_city}'].values
        
        for i in range(168):
            ts = req_start + timedelta(hours=i)
            load = float(preds["prediction"][i])
            is_we = bool(future_df['Weekend'].iloc[i] == 1)
            price = market.estimate_iso_ne_price(load, ts.hour, is_we)
            
            final_results.append({
                "hour_offset": i,
                "timestamp": ts.isoformat(),
                "predicted_load": load,
                "xgb_load": float(preds["xgb_base"][i]),
                "dl_residual": float(preds["residual_correction"][i]),
                "weather_code": int(weather_codes[i]),
                "price": price,
                "solar_mw": float(solar_mw[i]),
                "wind_mw": float(wind_mw[i]),
                "net_load": float(load - solar_mw[i] - wind_mw[i])
            })
            
        db.save_forecast_results(req_id, final_results)
        
        # 7. Contextual data
        ground_truth = history_df[
            (history_df['Timestamp'] >= req_start) & 
            (history_df['Timestamp'] < req_start + timedelta(hours=168))
        ].copy()
        if not ground_truth.empty:
            ground_truth['Timestamp'] = ground_truth['Timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')
            gt_data = ground_truth[['Timestamp', 'load']].to_dict(orient='records')
        else:
            gt_data = []

        prev_week = history_window[['Timestamp', 'load']].copy()
        prev_week['Timestamp'] = prev_week['Timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        
        # 8. Summary & Alerts
        peak_load = max(preds["prediction"])
        avg_xgb = float(np.mean(preds["xgb_base"]))
        alerts = []
        if float(peak_load) > 21000.0:
            alerts.append({"type": "CRITICAL", "message": f"Peak Demand Alert: {peak_load:,.0f} MW predicted."})
        elif float(peak_load) > 18500.0:
            alerts.append({"type": "WARNING", "message": "High usage period detected."})

        # Season logic
        m = req_start.month
        if m in [12, 1, 2]: season = "Winter"
        elif m in [3, 4, 5]: season = "Spring"
        elif m in [6, 7, 8]: season = "Summer"
        else: season = "Autumn"

        return jsonify({
            "request_id": req_id,
            "forecast": final_results,
            "ground_truth": gt_data,
            "previous_week": prev_week.to_dict(orient='records'),
            "summary": {
                "peak_load": float(peak_load),
                "peak_time": final_results[preds["prediction"].index(peak_load)]["timestamp"],
                "avg_load": float(np.mean(preds["prediction"])),
                "xgb_avg": avg_xgb,
                "avg_price": float(np.mean([f['price'] for f in final_results])),
                "renewable_mw": float(np.mean(solar_mw + wind_mw)),
                "is_holiday": bool(future_df['Holiday'].iloc[0]),
                "season": season,
                "alerts": alerts,
                "temp_offset": temp_offset
            }
        })
    except Exception as e:
        db.update_request_error(req_id, str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get all past forecast requests."""
    return jsonify(db.get_all_requests())


@app.route('/api/history/<int:request_id>', methods=['GET'])
def get_history_detail(request_id):
    """Get specific forecast with its data points."""
    data = db.get_request_with_results(request_id)
    if not data:
        return jsonify({"error": "Request not found"}), 404
    return jsonify(data)


@app.route('/api/history/<int:request_id>', methods=['DELETE'])
def delete_history_entry(request_id):
    """Delete a specific forecast request."""
    try:
        db.delete_request(request_id)
        return jsonify({"status": "deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/models', methods=['GET'])
def get_model_comparison():
    """Return model comparison metrics from training (JSON)."""
    try:
        path = os.path.join(MODEL_DIR, "v4", "all_model_comparison_v4.json")
        with open(path, 'r') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/evaluation', methods=['GET'])
def get_evaluation():
    """Return detailed V4 metrics."""
    try:
        path = os.path.join(MODEL_DIR, "v4", "dl_metrics_v4.json")
        with open(path, 'r') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/live-evaluation', methods=['GET'])
def get_live_evaluation():
    """Evaluate stored forecasts against real historic loads."""
    all_requests = db.get_all_requests()
    results = []
    
    # We'll calculate performance of the latest 10 requests that have ground truth
    combined_actuals = []
    combined_preds = []
    history_df = get_history_data()
    
    for req in all_requests[:10]:
        details = db.get_request_with_results(req['id'])
        for r in details['results']:
            ts = pd.to_datetime(r['timestamp'])
            # Match with history_df
            actual = history_df[history_df['Timestamp'] == ts]
            if not actual.empty:
                combined_actuals.append(actual['load'].values[0])
                combined_preds.append(r['predicted_load'])
    
    if not combined_actuals:
        return jsonify({"status": "no_data", "message": "Not enough historical data to evaluate live."})
    
    y_true = np.array(combined_actuals)
    y_pred = np.array(combined_preds)
    
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred)**2)))
    mape = float(np.mean(np.abs((y_true - y_pred) / y_true))) * 100
    
    return jsonify({
        "status": "success",
        "sample_size": len(combined_actuals),
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "last_updated": datetime.now().isoformat()
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    # Proactively trigger lazy loading if not done
    # This helps pre-heat the server when the frontend first opens
    try:
        if model_manager.loaded:
            ready = True
        else:
            # We don't wait for it to finish in health check to avoid blocking
            # but we can trigger the load. Note: In a free tier, 
            # this might still be slow, but it gets the process started.
            from threading import Thread
            def warm_up():
                get_history_data()
                model_manager.load()
            Thread(target=warm_up).start()
            ready = False
            
        return jsonify({
            "status": "healthy", 
            "model_ready": ready,
            "warming_up": not ready
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
