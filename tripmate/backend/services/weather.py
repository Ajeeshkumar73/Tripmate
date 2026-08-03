import requests
from datetime import datetime, timedelta


BASE_URL = "https://api.open-meteo.com/v1"

WMO_CODES = {
    0: ("Clear Sky", "☀️"), 1: ("Mainly Clear", "🌤️"), 2: ("Partly Cloudy", "⛅"),
    3: ("Overcast", "☁️"), 45: ("Foggy", "🌫️"), 48: ("Rime Fog", "🌫️"),
    51: ("Light Drizzle", "🌦️"), 53: ("Drizzle", "🌦️"), 55: ("Heavy Drizzle", "🌧️"),
    61: ("Slight Rain", "🌧️"), 63: ("Rain", "🌧️"), 65: ("Heavy Rain", "🌧️"),
    71: ("Slight Snow", "🌨️"), 73: ("Snow", "❄️"), 75: ("Heavy Snow", "❄️"),
    77: ("Snow Grains", "🌨️"), 80: ("Slight Showers", "🌦️"), 81: ("Showers", "🌧️"),
    82: ("Violent Showers", "⛈️"), 85: ("Slight Snow Showers", "🌨️"),
    86: ("Heavy Snow Showers", "❄️"), 95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm w/ Hail", "⛈️"), 99: ("Thunderstorm w/ Heavy Hail", "⛈️"),
}


def _wmo_description(code):
    return WMO_CODES.get(code, ("Unknown", "🌡️"))


def get_current_weather(lat: float, lon: float) -> dict:
    """Fetch current weather conditions."""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "precipitation", "weather_code", "wind_speed_10m", "wind_direction_10m",
                "uv_index", "visibility"
            ],
            "timezone": "auto"
        }
        resp = requests.get(f"{BASE_URL}/forecast", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})
        code = current.get("weather_code", 0)
        desc, emoji = _wmo_description(code)
        return {
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation": current.get("precipitation"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "uv_index": current.get("uv_index"),
            "visibility": current.get("visibility"),
            "weather_code": code,
            "description": desc,
            "emoji": emoji,
            "timezone": data.get("timezone"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_forecast(lat: float, lon: float, days: int = 7) -> dict:
    """Fetch multi-day weather forecast."""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": [
                "temperature_2m_max", "temperature_2m_min", "precipitation_sum",
                "weather_code", "wind_speed_10m_max", "uv_index_max",
                "precipitation_probability_max", "sunrise", "sunset"
            ],
            "timezone": "auto",
            "forecast_days": days,
        }
        resp = requests.get(f"{BASE_URL}/forecast", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})

        days_list = []
        dates = daily.get("time", [])
        for i, date in enumerate(dates):
            code = daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0
            desc, emoji = _wmo_description(code)
            days_list.append({
                "date": date,
                "temp_max": daily.get("temperature_2m_max", [None])[i],
                "temp_min": daily.get("temperature_2m_min", [None])[i],
                "precipitation": daily.get("precipitation_sum", [0])[i],
                "rain_probability": daily.get("precipitation_probability_max", [0])[i],
                "wind_speed": daily.get("wind_speed_10m_max", [0])[i],
                "uv_index": daily.get("uv_index_max", [0])[i],
                "weather_code": code,
                "description": desc,
                "emoji": emoji,
                "sunrise": daily.get("sunrise", [None])[i],
                "sunset": daily.get("sunset", [None])[i],
            })
        return {"days": days_list, "timezone": data.get("timezone")}
    except Exception as e:
        return {"error": str(e), "days": []}


def get_hourly_forecast(lat: float, lon: float) -> dict:
    """Fetch 24-hour hourly weather forecast."""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": [
                "temperature_2m", "relative_humidity_2m", "precipitation_probability",
                "precipitation", "weather_code", "wind_speed_10m", "visibility",
                "uv_index"
            ],
            "timezone": "auto",
            "forecast_days": 1,
        }
        resp = requests.get(f"{BASE_URL}/forecast", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        hourly = data.get("hourly", {})

        hours = []
        times = hourly.get("time", [])
        for i, time_str in enumerate(times[:24]):
            code = hourly.get("weather_code", [0])[i] if i < len(hourly.get("weather_code", [])) else 0
            desc, emoji = _wmo_description(code)
            hours.append({
                "time": time_str,
                "temperature": hourly.get("temperature_2m", [None])[i],
                "humidity": hourly.get("relative_humidity_2m", [None])[i],
                "rain_probability": hourly.get("precipitation_probability", [0])[i],
                "precipitation": hourly.get("precipitation", [0])[i],
                "wind_speed": hourly.get("wind_speed_10m", [0])[i],
                "weather_code": code,
                "description": desc,
                "emoji": emoji,
            })
        return {"hours": hours, "timezone": data.get("timezone")}
    except Exception as e:
        return {"error": str(e), "hours": []}


def get_air_quality(lat: float, lon: float) -> dict:
    """Fetch air quality data."""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide",
                        "ozone", "european_aqi"],
            "timezone": "auto"
        }
        resp = requests.get("https://air-quality-api.open-meteo.com/v1/air-quality",
                            params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})
        aqi = current.get("european_aqi", 0)

        if aqi <= 20:
            aqi_label, aqi_color = "Good", "#22c55e"
        elif aqi <= 40:
            aqi_label, aqi_color = "Fair", "#84cc16"
        elif aqi <= 60:
            aqi_label, aqi_color = "Moderate", "#eab308"
        elif aqi <= 80:
            aqi_label, aqi_color = "Poor", "#f97316"
        else:
            aqi_label, aqi_color = "Very Poor", "#ef4444"

        return {
            "aqi": aqi,
            "aqi_label": aqi_label,
            "aqi_color": aqi_color,
            "pm10": current.get("pm10"),
            "pm2_5": current.get("pm2_5"),
            "nitrogen_dioxide": current.get("nitrogen_dioxide"),
            "ozone": current.get("ozone"),
        }
    except Exception as e:
        return {"error": str(e)}
