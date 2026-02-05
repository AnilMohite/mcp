from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# initialize the MCP server
mcp = FastMCP("weather_service")

# Constants
API_BASE_URL = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    
    headers = {
        "User-Agent": USER_AGENT, 
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""

    props = feature["properties"]
    return f"""
        Event: {props.get("event", "Unknown")}
        Area: {props.get("areaDesc", "Unknown")}
        Severity: {props.get("severity", "Unknown")}
        Description: {props.get("description", "No description available")}
        Instructions: {props.get("instruction", "No specific instructions provided")}
        """

@mcp.tool()
async def get_weather_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two letter state code (e.g. 'CA' for California)
    """
    url = f"{API_BASE_URL}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "No alerts found or unable to fetch alerts"
    
    if not data["features"]:
        return "No active weather alerts for the specified state."
    
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n----\n".join(alerts)


@mcp.tool()
async def get_forecast(lat: float, lon: float) -> str:
    """Get the weather forecast for a specific latitude and longitude.

    Args:
        lat: Latitude of the location
        lon: Longitude of the location
    """
    url = f"{API_BASE_URL}/points/{lat},{lon}/forecast"
    data = await make_nws_request(url)

    if not data or "properties" not in data or "forecast" not in data["properties"]:
        return "Unable to fetch forecast data."
    
    # Get the forecast URL from the points response
    forecast_url = data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch forecast data."
    
     # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:3]:
        forecast = f"""
            {period["name"]}:
            Temperature: {period["temperature"]}°{period["temperatureUnit"]}
            Wind: {period["windSpeed"]} {period["windDirection"]}
            Forecast: {period["detailedForecast"]}
        """
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def get_indian_forecast(lat: float, lon: float) -> str:
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()
    return str(data)

@mcp.tool()
async def my_tool(input_string: str) -> str:
    return f"This is a test tool that returns the input string: {input_string}"

def main():
    # Initialize and run the server
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()