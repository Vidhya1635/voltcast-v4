"""
Weather data fetcher using Open-Meteo API (free, no API key required).
Provides forecast and historical weather for New England cities.
"""
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config import WEATHER_CITIES, SEASONAL_TEMP, SEASONAL_HUMIDITY, SEASONAL_WIND


def fetch_weather_forecast(start_date, hours=168):
    """
    Fetch hourly weather forecast for all 5 cities.
    Returns dict of city -> DataFrame with columns: Temp, Humidity, Precip, Wind, Code, Solar, Wind100
    Falls back to seasonal averages if API fails.
    """
    end_date = start_date + timedelta(hours=hours - 1)
    weather_data = {}

    for city, coords in WEATHER_CITIES.items():
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": coords["lat"],
                "longitude": coords["lon"],
                "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code,shortwave_radiation,wind_speed_100m",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "timezone": "America/New_York",
            }
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            hourly = data["hourly"]
            df = pd.DataFrame({
                f"Temp_{city}":     hourly["temperature_2m"][:hours],
                f"Humidity_{city}": hourly["relative_humidity_2m"][:hours],
                f"Precip_{city}":   hourly["precipitation"][:hours],
                f"Wind_{city}":     hourly["wind_speed_10m"][:hours],
                f"Code_{city}":     hourly["weather_code"][:hours],
                f"Solar_{city}":    hourly["shortwave_radiation"][:hours],
                f"Wind100_{city}":  hourly["wind_speed_100m"][:hours],
            })
            # Check if we got back valid data
            if df.isna().all().any():
                print(f"  ⚠️  {city} weather API returned nulls. Using seasonal fallback.")
                weather_data[city] = _seasonal_fallback(city, start_date, hours)
            else:
                weather_data[city] = df
                print(f"  ✅ {city}: {len(df)} hours fetched")

        except Exception as e:
            print(f"  ⚠️  {city} weather API failed: {e}. Using seasonal fallback.")
            weather_data[city] = _seasonal_fallback(city, start_date, hours)

    return weather_data


def fetch_historical_weather(start_date, hours=168):
    """
    Fetch historical hourly weather for all 5 cities.
    Uses Open-Meteo historical API.
    Returns dict of city -> DataFrame with columns: Temp, Humidity, Precip, Wind, Code, Solar, Wind100
    """
    end_date = start_date + timedelta(hours=hours - 1)
    weather_data = {}

    for city, coords in WEATHER_CITIES.items():
        try:
            url = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                "latitude": coords["lat"],
                "longitude": coords["lon"],
                "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code,shortwave_radiation,wind_speed_100m",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "timezone": "America/New_York",
            }
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            hourly = data["hourly"]
            df = pd.DataFrame({
                f"Temp_{city}":     hourly["temperature_2m"][:hours],
                f"Humidity_{city}": hourly["relative_humidity_2m"][:hours],
                f"Precip_{city}":   hourly["precipitation"][:hours],
                f"Wind_{city}":     hourly["wind_speed_10m"][:hours],
                f"Code_{city}":     hourly["weather_code"][:hours],
                f"Solar_{city}":    hourly["shortwave_radiation"][:hours],
                f"Wind100_{city}":  hourly["wind_speed_100m"][:hours],
            })
            weather_data[city] = df
            print(f"  ✅ {city}: {len(df)} hours (historical)")

        except Exception as e:
            print(f"  ⚠️  {city} historical API failed: {e}. Using seasonal fallback.")
            weather_data[city] = _seasonal_fallback(city, start_date, hours)

    return weather_data


def _seasonal_fallback(city, start_date, hours):
    """Generate seasonal average weather when API fails."""
    timestamps = [start_date + timedelta(hours=h) for h in range(hours)]
    temps, humids, winds = [], [], []

    for ts in timestamps:
        month = ts.month
        hour = ts.hour
        # Add diurnal temperature variation (±5°C)
        diurnal = 5.0 * np.sin(2 * np.pi * (hour - 6) / 24)
        temps.append(SEASONAL_TEMP[month] + diurnal)
        humids.append(SEASONAL_HUMIDITY[month])
        winds.append(SEASONAL_WIND[month])

    return pd.DataFrame({
        f"Temp_{city}":     temps,
        f"Humidity_{city}": humids,
        f"Precip_{city}":   [0.0] * hours,
        f"Wind_{city}":     winds,
        f"Code_{city}":     [0] * hours,
        f"Solar_{city}":    [0.0] * hours,
        f"Wind100_{city}":  [winds[i] * 1.2 for i in range(hours)], # simple estimate
    })
