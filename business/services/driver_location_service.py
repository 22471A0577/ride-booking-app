from math import radians, sin, cos, sqrt, atan2

from django.core.cache import cache
from django.db import transaction

from business.models import DriverLocation


EARTH_RADIUS_KM = 6371.0


def calculate_distance_km(
    latitude1,
    longitude1,
    latitude2,
    longitude2,
):
    """
    Calculate distance between two coordinates
    using the Haversine formula.
    """

    latitude1 = radians(float(latitude1))
    longitude1 = radians(float(longitude1))

    latitude2 = radians(float(latitude2))
    longitude2 = radians(float(longitude2))

    delta_latitude = latitude2 - latitude1
    delta_longitude = longitude2 - longitude1

    a = (
        sin(delta_latitude / 2) ** 2
        + cos(latitude1)
        * cos(latitude2)
        * sin(delta_longitude / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return EARTH_RADIUS_KM * c


@transaction.atomic
def update_driver_location(
    driver,
    latitude,
    longitude,
):
    """
    Create or update the driver's latest GPS location.
    """

    location, created = DriverLocation.objects.update_or_create(
        driver=driver,
        defaults={
            "latitude": latitude,
            "longitude": longitude,
        },
    )

    # Invalidate cached nearby-driver results
    cache.clear()

    return location, created
def get_nearby_drivers(
    latitude,
    longitude,
    radius_km,
):
    """
    Find online drivers within the requested radius.

    Uses Redis caching to avoid repeated database queries.
    """

    cache_key = (
        f"nearby_drivers:"
        f"{round(float(latitude), 4)}:"
        f"{round(float(longitude), 4)}:"
        f"{round(float(radius_km), 2)}"
    )

    cached_drivers = cache.get(cache_key)

    if cached_drivers is not None:
        print("CACHE HIT:", cache_key)
        return cached_drivers

    print("CACHE MISS:", cache_key)

    drivers = (
        DriverLocation.objects
        .select_related(
            "driver",
            "driver__user",
        )
        .filter(
            driver__availability_status="ONLINE",
        )
    )

    nearby_drivers = []

    for location in drivers:

        distance = calculate_distance_km(
            latitude,
            longitude,
            location.latitude,
            location.longitude,
        )

        if distance <= float(radius_km):

            nearby_drivers.append(
                {
                    "driver_id": str(location.driver.id),
                    "user_id": str(location.driver.user_id),
                    "distance_km": round(distance, 2),
                    "latitude": float(location.latitude),
                    "longitude": float(location.longitude),
                }
            )

    nearby_drivers.sort(
        key=lambda driver: driver["distance_km"]
    )

    cache.set(
        cache_key,
        nearby_drivers,
        timeout=30,
    )

    print("CACHE STORED:", cache_key)

    return nearby_drivers