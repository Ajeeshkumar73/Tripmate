import requests


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Mapping of POI type to Overpass tags
POI_TAGS = {
    "tourist_attraction": '[tourism~"attraction|museum|viewpoint|artwork|gallery|theme_park|zoo"]',
    "hotel": '[tourism~"hotel|motel|guest_house|hostel|resort"]',
    "hostel": '[tourism="hostel"]',
    "restaurant": '[amenity="restaurant"]',
    "cafe": '[amenity="cafe"]',
    "hospital": '[amenity="hospital"]',
    "pharmacy": '[amenity="pharmacy"]',
    "police": '[amenity="police"]',
    "atm": '[amenity="atm"]',
    "fuel": '[amenity="fuel"]',
    "parking": '[amenity="parking"]',
    "railway_station": '[railway="station"]',
    "bus_station": '[amenity~"bus_station|bus_stop"]',
    "airport": '[aeroway="aerodrome"]',
    "toilet": '[amenity="toilets"]',
    "ev_charging": '[amenity="charging_station"]',
    "supermarket": '[shop~"supermarket|convenience"]',
}

# Icon mapping for frontend display
POI_ICONS = {
    "tourist_attraction": {"icon": "landscape", "color": "#95d3ba"},
    "hotel": {"icon": "hotel", "color": "#bec6e0"},
    "hostel": {"icon": "meeting_room", "color": "#a8cfbc"},
    "restaurant": {"icon": "restaurant", "color": "#ffb4ab"},
    "cafe": {"icon": "local_cafe", "color": "#f9c784"},
    "hospital": {"icon": "local_hospital", "color": "#ef4444"},
    "pharmacy": {"icon": "medication", "color": "#f97316"},
    "police": {"icon": "local_police", "color": "#3b82f6"},
    "atm": {"icon": "atm", "color": "#22c55e"},
    "fuel": {"icon": "local_gas_station", "color": "#a855f7"},
    "parking": {"icon": "local_parking", "color": "#6366f1"},
    "railway_station": {"icon": "train", "color": "#14b8a6"},
    "bus_station": {"icon": "directions_bus", "color": "#f59e0b"},
    "airport": {"icon": "flight", "color": "#06b6d4"},
    "toilet": {"icon": "wc", "color": "#89938d"},
    "ev_charging": {"icon": "ev_station", "color": "#84cc16"},
    "supermarket": {"icon": "shopping_cart", "color": "#ec4899"},
}


def get_nearby_pois(lat: float, lon: float, poi_type: str, radius: int = 2000) -> list:
    """Query Overpass API for nearby points of interest."""
    tag_filter = POI_TAGS.get(poi_type, '[amenity]')
    icon_info = POI_ICONS.get(poi_type, {"icon": "place", "color": "#95d3ba"})

    query = f"""
    [out:json][timeout:25];
    (
      node{tag_filter}(around:{radius},{lat},{lon});
      way{tag_filter}(around:{radius},{lat},{lon});
      relation{tag_filter}(around:{radius},{lat},{lon});
    );
    out center 50;
    """

    try:
        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=30,
            headers={"User-Agent": "TripMateAI/1.0"}
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for element in data.get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name") or tags.get("name:en") or poi_type.replace("_", " ").title()

            # Get coordinates
            if element.get("type") == "node":
                elem_lat = element.get("lat")
                elem_lon = element.get("lon")
            else:
                center = element.get("center", {})
                elem_lat = center.get("lat")
                elem_lon = center.get("lon")

            if not elem_lat or not elem_lon:
                continue

            # Calculate distance
            import math
            dlat = math.radians(elem_lat - lat)
            dlon = math.radians(elem_lon - lon)
            a = (math.sin(dlat/2)**2 +
                 math.cos(math.radians(lat)) * math.cos(math.radians(elem_lat)) *
                 math.sin(dlon/2)**2)
            dist_km = round(6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)), 2)

            results.append({
                "name": name,
                "lat": elem_lat,
                "lon": elem_lon,
                "distance_km": dist_km,
                "type": poi_type,
                "icon": icon_info["icon"],
                "color": icon_info["color"],
                "phone": tags.get("phone") or tags.get("contact:phone", ""),
                "website": tags.get("website") or tags.get("contact:website", ""),
                "opening_hours": tags.get("opening_hours", ""),
                "rating": tags.get("stars", ""),
                "address": _build_address(tags),
            })

        # Sort by distance
        results.sort(key=lambda x: x["distance_km"])
        return results[:30]

    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Overpass error for {poi_type}: {e}")
        return []


def _build_address(tags: dict) -> str:
    parts = []
    for key in ["addr:housenumber", "addr:street", "addr:city", "addr:state"]:
        if tags.get(key):
            parts.append(tags[key])
    return ", ".join(parts)


def get_multiple_poi_types(lat: float, lon: float, poi_types: list, radius: int = 2000) -> dict:
    """Get multiple POI types in one call."""
    results = {}
    for poi_type in poi_types:
        results[poi_type] = get_nearby_pois(lat, lon, poi_type, radius)
    return results
