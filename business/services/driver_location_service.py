
import logging
from math import radians, sin, cos, sqrt, atan2

from django.core.cache import cache
from django.db import transaction

from business.models import DriverLocation


logger = logging.getLogger(__name__)


EARTH_RADIUS_KM = 6371.0
NEARBY_CACHE_TIMEOUT = 30


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
        sqrt(1 - a),
    )

    return EARTH_RADIUS_KM * c


def _get_bounding_box(
    latitude,
    longitude,
    radius_km,
):
    """
    Calculate an approximate latitude/longitude bounding box.

    This is used to reduce the number of database rows that
    need exact Haversine distance calculations.
    """

    latitude = float(latitude)
    longitude = float(longitude)
    radius_km = float(radius_km)

    latitude_delta = radius_km / 111.0

    # Avoid division by zero close to the poles.
    cosine_latitude = cos(radians(latitude))

    if abs(cosine_latitude) < 0.000001:
        longitude_delta = 180.0
    else:
        longitude_delta = radius_km / (
            111.0 * abs(cosine_latitude)
        )

    min_latitude = max(
        -90.0,
        latitude - latitude_delta,
    )

    max_latitude = min(
        90.0,
        latitude + latitude_delta,
    )

    min_longitude = longitude - longitude_delta
    max_longitude = longitude + longitude_delta

    return (
        min_latitude,
        max_latitude,
        min_longitude,
        max_longitude,
    )


def _invalidate_nearby_driver_cache():
    """
    Invalidate only nearby-driver cache entries.

    django-redis supports delete_pattern(), allowing us to
    avoid clearing unrelated application cache entries.
    """

    delete_pattern = getattr(
        cache,
        "delete_pattern",
        None,
    )

    if delete_pattern:

        delete_pattern(
            "nearby_drivers:*"
        )

        logger.info(
            "Nearby driver cache invalidated"
        )


@transaction.atomic
def update_driver_location(
    driver,
    latitude,
    longitude,
):
    """
    Create or update the driver's latest GPS location.

    Only nearby-driver cache entries are invalidated.
    Other application caches remain untouched.
    """

    location, created = (
        DriverLocation.objects.update_or_create(
            driver=driver,
            defaults={
                "latitude": latitude,
                "longitude": longitude,
            },
        )
    )

    logger.info(
        "Driver location updated | "
        "driver_id=%s | created=%s",
        driver.id,
        created,
    )

    _invalidate_nearby_driver_cache()

    return location, created


def get_nearby_drivers(
    latitude,
    longitude,
    radius_km,
):
    """
    Find online drivers within the requested radius.

    Uses Redis caching and a database bounding-box filter
    before applying the exact Haversine calculation.
    """

    latitude = float(latitude)
    longitude = float(longitude)
    radius_km = float(radius_km)

    cache_key = (
        f"nearby_drivers:"
        f"{round(latitude, 4)}:"
        f"{round(longitude, 4)}:"
        f"{round(radius_km, 2)}"
    )

    cached_drivers = cache.get(
        cache_key
    )

    if cached_drivers is not None:

        logger.info(
            "Nearby drivers cache hit | "
            "cache_key=%s",
            cache_key,
        )

        return cached_drivers

    logger.info(
        "Nearby drivers cache miss | "
        "cache_key=%s",
        cache_key,
    )

    (
        min_latitude,
        max_latitude,
        min_longitude,
        max_longitude,
    ) = _get_bounding_box(
        latitude,
        longitude,
        radius_km,
    )

    drivers = (
        DriverLocation.objects
        .select_related(
            "driver",
            "driver__user",
        )
        .filter(
            driver__availability_status="ONLINE",
            latitude__gte=min_latitude,
            latitude__lte=max_latitude,
        )
    )

    # Handle the normal longitude case and the
    # International Date Line case separately.
    if min_longitude >= -180.0 and max_longitude <= 180.0:

        drivers = drivers.filter(
            longitude__gte=min_longitude,
            longitude__lte=max_longitude,
        )

    else:

        normalized_min = (
            min_longitude + 360.0
        ) % 360.0 - 180.0

        normalized_max = (
            max_longitude + 360.0
        ) % 360.0 - 180.0

        if min_longitude < -180.0:

            drivers = drivers.filter(
                longitude__gte=min_longitude + 360.0
            ) | drivers.filter(
                longitude__lte=max_longitude
            )

        elif max_longitude > 180.0:

            drivers = drivers.filter(
                longitude__gte=min_longitude
            ) | drivers.filter(
                longitude__lte=max_longitude - 360.0
            )

        else:

            drivers = drivers.filter(
                longitude__gte=normalized_min,
                longitude__lte=normalized_max,
            )

    nearby_drivers = []

    for location in drivers:

        distance = calculate_distance_km(
            latitude,
            longitude,
            location.latitude,
            location.longitude,
        )

        if distance <= radius_km:

            nearby_drivers.append(
                {
                    "driver_id": str(
                        location.driver.id
                    ),
                    "user_id": str(
                        location.driver.user_id
                    ),
                    "distance_km": round(
                        distance,
                        2,
                    ),
                    "latitude": float(
                        location.latitude
                    ),
                    "longitude": float(
                        location.longitude
                    ),
                }
            )

    nearby_drivers.sort(
        key=lambda driver: driver["distance_km"]
    )

    cache.set(
        cache_key,
        nearby_drivers,
        timeout=NEARBY_CACHE_TIMEOUT,
    )

    logger.info(
        "Nearby drivers cache stored | "
        "cache_key=%s | driver_count=%s",
        cache_key,
        len(nearby_drivers),
    )

    return nearby_drivers
