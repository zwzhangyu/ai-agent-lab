import os

import requests
from dotenv import load_dotenv

from tools.base_tool import BaseTool


class WeatherTool(BaseTool):
    """Fetches current weather data for a given city using OpenWeatherMap API."""

    def __init__(self):
        super().__init__()
        self.name = "weather"
        self.description = "Fetches current weather conditions for a specified city."
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def run(self, query):
        if not query or not query.strip():
            return "Error: City name cannot be empty."

        if not self.api_key:
            return "Error: OPENWEATHER_API_KEY not configured."

        url = f"{self.base_url}?q={query}&appid={self.api_key}&units=metric"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                return f"Error: Unable to fetch weather data. Server responded with {response.status_code}: {response.json().get('message', 'Unknown error')}"

            data = response.json()
            if "main" not in data or "weather" not in data:
                return f"Could not find weather data for '{query}'. Please check the city name."

            temperature = data["main"]["temp"]
            description = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            return (
                f"The temperature in {query} is {temperature}°C. "
                f"The weather is {description}. "
                f"The humidity is {humidity}%. "
                f"The wind speed is {wind_speed} m/s."
            )

        except requests.exceptions.RequestException as req_err:
            return f"Request failed: {str(req_err)}"
