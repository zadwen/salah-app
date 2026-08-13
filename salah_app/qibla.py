"""Great-circle bearing from a location to the Kaaba (Qibla direction)."""
import math

from .constants import KAABA_LAT, KAABA_LON


def bearing_to_kaaba(lat, lon):
    """Return initial compass bearing (0-360, 0=North, clockwise) from
    (lat, lon) toward the Kaaba in Makkah."""
    lat1 = math.radians(lat)
    lat2 = math.radians(KAABA_LAT)
    dlon = math.radians(KAABA_LON - lon)

    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def great_circle_distance_km(lat, lon):
    """Haversine distance in km from (lat, lon) to the Kaaba."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat, lon, KAABA_LAT, KAABA_LON])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(min(1, math.sqrt(a)))
    return R * c
