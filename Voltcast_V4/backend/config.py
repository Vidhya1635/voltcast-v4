"""
Configuration for the Flask backend.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# ── Paths ──────────────────────────────────────────────────────────────
MODEL_DIR        = os.path.join(PROJECT_DIR, "models")
DATA_DIR         = os.path.join(PROJECT_DIR, "data")
DB_DIR           = os.path.join(PROJECT_DIR, "database")
PREPROCESSED_CSV = os.path.join(DATA_DIR, "preprocessed_load_data.csv")

# ── Model artifacts ────────────────────────────────────────────────────
XGB_MODEL_PATH      = os.path.join(MODEL_DIR, "xgb_model.pkl")
FEATURE_SCALER_PATH = os.path.join(MODEL_DIR, "feature_scaler.pkl")
TARGET_SCALER_PATH  = os.path.join(MODEL_DIR, "target_scaler.pkl")
CONFIG_PATH         = os.path.join(MODEL_DIR, "config.pkl")

DL_MODEL_PATHS = [
    os.path.join(MODEL_DIR, "v4", "res_model_0_s42.pt"),
    os.path.join(MODEL_DIR, "v4", "res_model_1_s123.pt"),
    os.path.join(MODEL_DIR, "v4", "res_model_2_s456.pt"),
]

# V4 hybrid blend alpha (from training)
BLEND_ALPHA = 0.85

# ── Weather cities (New England) ───────────────────────────────────────
WEATHER_CITIES = {
    "Boston":      {"lat": 42.36, "lon": -71.06},
    "Hartford":    {"lat": 41.76, "lon": -72.68},
    "Providence":  {"lat": 41.82, "lon": -71.41},
    "Portland":    {"lat": 43.66, "lon": -70.26},
    "Burlington":  {"lat": 44.47, "lon": -73.21},
}

# ── Feature engineering constants ──────────────────────────────────────
INPUT_LEN  = 168   # 7 days input
OUTPUT_LEN = 168   # 7 days forecast
CDH_BASE   = 18.0  # Cooling degree-hour base (°C)
HDH_BASE   = 18.0  # Heating degree-hour base (°C)

# ── Seasonal averages (fallback when weather API fails) ────────────────
SEASONAL_TEMP = {
    1: -5.0, 2: -3.5, 3: 2.0, 4: 8.5, 5: 14.5, 6: 20.0,
    7: 23.0, 8: 22.0, 9: 17.5, 10: 11.0, 11: 5.0, 12: -1.5
}
SEASONAL_HUMIDITY = {
    1: 65, 2: 63, 3: 62, 4: 60, 5: 63, 6: 65,
    7: 68, 8: 70, 9: 72, 10: 68, 11: 70, 12: 68
}
SEASONAL_WIND = {
    1: 15.0, 2: 15.0, 3: 14.5, 4: 14.0, 5: 12.5, 6: 11.5,
    7: 10.5, 8: 10.0, 9: 11.0, 10: 12.5, 11: 14.0, 12: 15.0
}

# ── US Federal Holidays (approximate) ─────────────────────────────────
US_HOLIDAYS_MD = [
    (1, 1), (1, 20), (2, 17), (5, 26), (7, 4), (9, 1),
    (10, 13), (11, 11), (11, 27), (12, 25)
]
