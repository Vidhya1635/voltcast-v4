"""
Market and Renewable Energy logic for ISO-NE region.
Estimates real-time prices and green energy generation.
"""
import numpy as np

def estimate_iso_ne_price(load_mw, hour_of_day, is_weekend):
    """
    Simulates ISO-NE Locational Marginal Price (LMP).
    Prices generally correlate with load and follow a daily pattern.
    """
    # Base price between $20 and $50
    base_price = 35.0
    
    # Load factor: Exponential increase as load hits peaks
    # (Threshold around 18GW where prices often spike)
    load_factor = (load_mw / 15000) ** 2.5
    
    # Time of day factor (Peakers are expensive)
    if 7 <= hour_of_day <= 10 or 17 <= hour_of_day <= 21:
        peak_premium = 1.2
    else:
        peak_premium = 0.9
        
    price = base_price * load_factor * peak_premium
    
    # Add some random market volatility (±10%)
    volatility = np.random.uniform(0.9, 1.1)
    
    return round(price * volatility, 2)

def estimate_renewables(weather_forecast):
    """
    weather_forecast: dict of city -> DataFrame with Solar and Wind100 columns.
    Estimates Solar and Wind generation in MW for the ISO-NE region.
    Rough capacity estimates used for demonstration.
    """
    # Approximate solar capacity in New England (weighted by city) ~6000 MW
    # Approximate wind capacity ~1500 MW
    
    cities = list(weather_forecast.keys())
    hours = len(weather_forecast[cities[0]])
    
    solar_total = np.zeros(hours)
    wind_total = np.zeros(hours)
    
    for city in cities:
        df = weather_forecast[city]
        
        # Solar: 0-1000 W/m2 usually. We proxy 1 W/m2 -> X MW across region
        # Solar radiation is usually 'shortwave_radiation' in W/m2
        solar_total += df[f'Solar_{city}'].values * 1.5 # 1000 W/m2 -> 1500 MW contribution per city
        
        # Wind: Power curve is cubic with wind speed (v^3)
        # Wind100 is speed at 100m in km/h. Let's convert to m/s for standard power curves
        v = df[f'Wind100_{city}'].values / 3.6
        wind_potential = (v / 12.0) ** 3 # Rated speed around 12 m/s
        wind_potential = np.clip(wind_potential, 0, 1.2) # Max capacity factor
        wind_total += wind_potential * 300 # 300 MW per city capacity
        
    return solar_total, wind_total
