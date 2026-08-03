import logging
import requests

logger = logging.getLogger(__name__)


def get_coordinates(place):
    """Geocode a place name using Nominatim. Returns dict with latitude/longitude or None."""
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": place,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }

    headers = {
        "User-Agent": "TripMateAI/1.0"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            return None

        return {
            "latitude": float(data[0]["lat"]),
            "longitude": float(data[0]["lon"]),
            "display_name": data[0].get("display_name", place),
        }
    except Exception as e:
        logger.warning(f"Geocode error for '{place}': {e}")
        return None