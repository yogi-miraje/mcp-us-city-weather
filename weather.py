from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
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

async def geocode_city(city: str) -> tuple[float, float] | None:
    """
    Convert a city name to latitude and longitude coordinates.
    
    Args:
        city: The name of the city (e.g., "San Francisco, CA")
        
    Returns:
        A tuple of (latitude, longitude) or None if geocoding failed
    """
    # Using the OpenStreetMap Nominatim API for geocoding
    url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1"
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {"User-Agent": USER_AGENT}
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                return (lat, lon)
            return None
        except Exception:
            return None

async def get_points_url(city: str) -> str:
    """
    Generate the NWS API points URL for a given city.
    
    Args:
        city: The name of the city (e.g., "San Francisco, CA")
        
    Returns:
        The formatted NWS API points URL or an error message
    """
    # First, geocode the city to get coordinates
    coordinates = await geocode_city(city)
    if not coordinates:
        return f"Could not find coordinates for city: {city}"
    
    latitude, longitude = coordinates
    
    # Format coordinates properly for the API request
    lat_str = str(round(latitude, 4)).strip()
    lon_str = str(round(longitude, 4)).strip()
    
    # Generate the points URL
    points_url = f"{NWS_API_BASE}/points/{lat_str},{lon_str}"
    return points_url

async def get_forecast_url(grid_id: str, grid_x: int, grid_y: int) -> str:
    """
    Generate the NWS API forecast URL for given grid information.
    
    Args:
        grid_id: The NWS grid ID (e.g., "MTR")
        grid_x: The X coordinate in the grid
        grid_y: The Y coordinate in the grid
        
    Returns:
        The formatted NWS API forecast URL
    """
    # Generate the forecast URL
    forecast_url = f"{NWS_API_BASE}/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast"
    return forecast_url

async def extract_grid_info(points_url: str) -> tuple[str, int, int] | None:
    """
    Extract grid information from a NWS API points URL.
    
    Args:
        points_url: The NWS API points URL
        
    Returns:
        A tuple of (grid_id, grid_x, grid_y) or None if grid info is missing
    """
    try:
        # Make the request to the points URL
        points_data = await make_nws_request(points_url)
        if not points_data:
            raise ValueError("Failed to retrieve points data")
            
        properties = points_data.get("properties", {})
        grid_id = properties.get("gridId")
        grid_x = properties.get("gridX")
        grid_y = properties.get("gridY")
        
        if not all([grid_id, grid_x, grid_y]):
            raise ValueError("Grid information is missing")
        
        return (grid_id, grid_x, grid_y)
    except Exception as e:
        raise ValueError(f"extract_grid_info: {str(e)}")

@mcp.tool()
async def get_weather(city: str) -> str:
    """
    Get weather information for a city.
    
    Args:
        city: The name of the city (e.g., "San Francisco, CA")
        
    Returns:
        A formatted string with weather information
    """
    try:
        # Get the points URL for the city
        points_url = await get_points_url(city)
        
        # Check if we got an error message instead of a URL
        if points_url.startswith("Could not find coordinates"):
            return points_url
        
        # Geocode the city to get coordinates (for display purposes)
        coordinates = await geocode_city(city)
        if not coordinates:
            return f"Could not find coordinates for city: {city}"
        
        latitude, longitude = coordinates
        
        # Extract grid information directly from the points URL
        grid_info = await extract_grid_info(points_url)
        if not grid_info:
            return f"Could not determine weather grid for this location. Please check your city name or try a different city."
        
        grid_id, grid_x, grid_y = grid_info
        
        # Get forecast data
        forecast_url = await get_forecast_url(grid_id, grid_x, grid_y)
        forecast_data = await make_nws_request(forecast_url)
        
        if not forecast_data:
            return f"Failed to retrieve forecast data from URL: {forecast_url}"
        
        # Format the forecast information
        periods = forecast_data.get("properties", {}).get("periods", [])
        if not periods:
            return "No forecast periods available in the API response."
        
        # Get the current period
        current = periods[0]
        
        # Get location information from the points data
        points_data = await make_nws_request(points_url)
        if points_data:
            properties = points_data.get("properties", {})
            location_city = properties.get('relativeLocation', {}).get('properties', {}).get('city', 'Unknown')
            location_state = properties.get('relativeLocation', {}).get('properties', {}).get('state', 'Unknown')
            location_display = f"{location_city}, {location_state}" if location_city != "Unknown" else city
        else:
            location_display = city
        
        # Format the response
        return f"""
Weather for {location_display}:
Coordinates: {latitude}, {longitude}
Forecast: {current.get('name', 'Unknown')}
Temperature: {current.get('temperature', 'Unknown')}°{current.get('temperatureUnit', 'F')}
Conditions: {current.get('shortForecast', 'Unknown')}
Wind: {current.get('windSpeed', 'Unknown')} {current.get('windDirection', '')}
Details: {current.get('detailedForecast', 'No detailed forecast available')}
"""
    except Exception as e:
        return f"Unexpected error in get_weather: {str(e)}"
