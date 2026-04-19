"""
Feature engineering pipeline.
Replicates the exact preprocessing and augmentation used during training.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config import CDH_BASE, HDH_BASE, US_HOLIDAYS_MD

def generate_time_features(df):
    """Generate sin/cos time features and holiday/weekend flags."""
    df = df.copy()
    ts = pd.to_datetime(df['Timestamp'])
    
    # Base components
    df['Hour'] = ts.dt.hour
    df['DayOfWeek'] = ts.dt.dayofweek
    df['Month'] = ts.dt.month
    df['Weekend'] = (df['DayOfWeek'] >= 5).astype(int)
    
    # Cyclical encoding
    df['Hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 24)
    df['Hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 24)
    df['Day_sin']  = np.sin(2 * np.pi * df['DayOfWeek'] / 7)
    df['Day_cos']  = np.cos(2 * np.pi * df['DayOfWeek'] / 7)
    df['Month_sin'] = np.sin(2 * np.pi * (df['Month'] - 1) / 12)
    df['Month_cos'] = np.cos(2 * np.pi * (df['Month'] - 1) / 12)
    
    # Holiday flag
    df['Holiday'] = 0
    for m, d in US_HOLIDAYS_MD:
        df.loc[(ts.dt.month == m) & (ts.dt.day == d), 'Holiday'] = 1
        
    return df

def generate_cdh_hdh(df):
    """Generate Cooling and Heating Degree Hours for all 5 cities."""
    df = df.copy()
    cities = ["Boston", "Hartford", "Providence", "Portland", "Burlington"]
    
    for city in cities:
        temp_col = f"Temp_{city}"
        df[f"CDH_{city}"] = np.maximum(0, df[temp_col] - CDH_BASE)
        df[f"HDH_{city}"] = np.maximum(0, HDH_BASE - df[temp_col])
        
    return df

def engineer_xgb_features(X_window, load_idx):
    """
    Extract summary statistics from a 168h input window for XGBoost.
    X_window: shape (168, n_features)
    Returns: 1D array of features
    """
    f = []
    load = X_window[:, load_idx]
    
    # Load statistics (Same as baseline_model.ipynb)
    f.extend([
        load.mean(), 
        load.std(), 
        load.min(), 
        load.max(),
        load[-1],          # Last value
        load[0],           # First value
        load[-1] - load[0], # Weekly delta
        load[-24:].mean(), # Last day mean
        load[-48:].mean()  # Last 2 days mean
    ])
    
    # Other features: mean + last value (2 per column)
    for j in range(X_window.shape[1]):
        if j != load_idx:
            f.extend([X_window[:, j].mean(), X_window[-1, j]])
            
    return np.array(f, dtype=np.float32)

def prepare_inference_data(historical_df, weather_forecast_dict, feature_cols):
    """
    Combines 168h of history with 168h of weather forecast.
    historical_df: last 168h of actual data (including load)
    weather_forecast_dict: 168h of future weather city->DF
    Returns: full future DF with skeleton for features
    """
    # 1. Create future range
    last_ts = pd.to_datetime(historical_df['Timestamp'].iloc[-1])
    future_ts = [last_ts + timedelta(hours=i+1) for i in range(168)]
    
    future_df = pd.DataFrame({'Timestamp': future_ts})
    
    # 2. Merge weather forecasts
    for city, w_df in weather_forecast_dict.items():
        future_df = pd.concat([future_df, w_df.reset_index(drop=True)], axis=1)
        
    # 3. Add time features
    future_df = generate_time_features(future_df)
    
    # 4. Add CDH/HDH
    future_df = generate_cdh_hdh(future_df)
    
    # 5. Add rolling placeholders (XGBoost doesn't use raw rolling, but DL might need column count)
    # Replicate training: rolling_24 and rolling_168 were in the preprocessed CSV
    future_df['rolling_24'] = historical_df['load'].tail(24).mean()
    future_df['rolling_168'] = historical_df['load'].mean()
    
    # 6. Add load placeholder (to be filled by prediction)
    future_df['load'] = 0.0
    
    # Ensure correct column order
    return future_df[feature_cols]
