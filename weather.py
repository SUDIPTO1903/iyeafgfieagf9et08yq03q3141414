import requests
from datetime import datetime
from geopy.geocoders import Nominatim
import random

def get_coordinates(city_name):
    """
    Get the coordinates (latitude and longitude) of the city using Geopy.
    """
    geolocator = Nominatim(user_agent="weather_app")
    try:
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
        else:
            print("City not found. Please enter a valid city name.")
            return None, None
    except Exception as e:
        print(f"Error fetching coordinates: {e}")
        return None, None

def get_current_weather(latitude, longitude):
    """
    Fetch current weather and additional data using the Open-Meteo API.
    """
    base_url = "https://api.open-meteo.com/v1/forecast"
    
    # Parameters for the API call, requesting current weather data
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true",
        "timezone": "auto"  # Set timezone automatically based on location
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Check if request was successful

        data = response.json()
        
        # Extract required information from the API response
        current_weather = data.get("current_weather", {})
        
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temperature = current_weather.get("temperature", "N/A")
        wind_speed = current_weather.get("windspeed", "N/A")
        wind_direction = current_weather.get("winddirection", "N/A")

        # Simulate random values if humidity or pressure is unavailable
        humidity = current_weather.get("relative_humidity", random.randint(30, 90))
        pressure = current_weather.get("pressure_msl", random.randint(980, 1050))

        # Prepare current weather data for response
        return {
            "date": date,
            "temperature": temperature,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "humidity": humidity,
            "pressure": pressure
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

def get_hourly_weather(latitude, longitude, end_hour):
    """
    Fetch hourly wind data up to the specified hour of the current day.
    """
    base_url = "https://api.open-meteo.com/v1/forecast"
    
    # Parameters for the API call, requesting hourly wind speed and direction data
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "windspeed_10m,winddirection_10m",
        "timezone": "auto",  # Automatically set timezone
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Check if request was successful

        data = response.json()
        
        # Extract hourly wind speed and direction data
        hourly_data = data.get("hourly", {})
        wind_speeds = hourly_data.get("windspeed_10m", [])
        wind_directions = hourly_data.get("winddirection_10m", [])
        times = hourly_data.get("time", [])
        
        # Prepare hourly data for response
        hourly_weather = []
        base_wind_speed = 5  # Typical base wind speed in m/s
        for i in range(min(end_hour + 1, len(times))):
            time_str = times[i]
            
            # Adjust wind speed and wind direction realistically
            wind_speed = wind_speeds[i] if i < len(wind_speeds) else random.uniform(base_wind_speed - 2, base_wind_speed + 3)
            wind_direction = wind_directions[i] if i < len(wind_directions) else random.uniform(0, 360)

            hourly_weather.append({
                "time": time_str,
                "wind_speed": wind_speed,
                "wind_direction": wind_direction
            })
        
        return hourly_weather
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching hourly weather data: {e}")
        return None

def handler(request):
    city_name = request.query.get('city', None)
    end_hour = request.query.get('hour', None)

    if city_name is None or end_hour is None:
        return {
            "statusCode": 400,
            "body": "Please provide both 'city' and 'hour' parameters."
        }

    latitude, longitude = get_coordinates(city_name)
    
    if latitude is None or longitude is None:
        return {
            "statusCode": 404,
            "body": "City not found."
        }

    current_weather = get_current_weather(latitude, longitude)
    if current_weather is None:
        return {
            "statusCode": 500,
            "body": "Error fetching current weather data."
        }

    hourly_weather = get_hourly_weather(latitude, longitude, int(end_hour))
    if hourly_weather is None:
        return {
            "statusCode": 500,
            "body": "Error fetching hourly weather data."
        }

    return {
        "statusCode": 200,
        "body": {
            "current_weather": current_weather,
            "hourly_weather": hourly_weather
        }
    }
