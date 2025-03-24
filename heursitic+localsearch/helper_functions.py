import math

# ================== Helper Functions ==================

def compute_distance(lat1, lng1, lat2, lng2):
    """Compute Haversine distance between two points (in km)."""
    R = 6378.137
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    lng1_rad = math.radians(lng1)
    lng2_rad = math.radians(lng2)
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def travel_time(distance_km):
    """Return travel time in minutes given distance in km."""
    return distance_km * 4.0  # since 1/0.25 = 4

def service_time(num_packages):
    """Return service time in minutes given number of packages."""
    return 3.0 * math.sqrt(num_packages) + 5.0

def time_to_minutes(t_str):
    """
    Convert a time string "HH:MM" to minutes from 08:00.
    For example, "11:00" becomes 180 (i.e. (11*60 - 8*60)).
    """
    hour, minute = map(int, t_str.split(":"))
    return (hour * 60 + minute) - (8 * 60)