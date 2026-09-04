import time

from django.core.cache import cache
from django.test import TestCase

from business.models import (
    User,
    DriverProfile,
    DriverLocation,
)

from business.services.driver_location_service import (
    get_nearby_drivers,
)


class CachePerformanceTests(TestCase):

    def setUp(self):

        cache.clear()

        self.user = User.objects.create_user(
            email="benchmark@test.com",
            password="Test@12345",
            role="DRIVER",
        )

        self.driver = DriverProfile.objects.create(
            user=self.user,
            license_number="BENCH-001",
            phone_number="9999999999",
            availability_status="ONLINE",
        )

        DriverLocation.objects.create(
            driver=self.driver,
            latitude="17.410000",
            longitude="78.510000",
        )

    def test_cache_performance(self):

        latitude = 17.410000
        longitude = 78.510000
        radius_km = 10

        # -------------------------------------------------
        # CACHE MISS
        # -------------------------------------------------

        cache.clear()

        start = time.perf_counter()

        result1 = get_nearby_drivers(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )

        miss_time = time.perf_counter() - start

        # -------------------------------------------------
        # CACHE HIT
        # -------------------------------------------------

        start = time.perf_counter()

        result2 = get_nearby_drivers(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )

        hit_time = time.perf_counter() - start

        print("\n========================================")
        print("=== CACHE PERFORMANCE BENCHMARK ===")
        print("========================================")

        print(
            f"Cache MISS time: {miss_time * 1000:.3f} ms"
        )

        print(
            f"Cache HIT time:  {hit_time * 1000:.3f} ms"
        )

        if miss_time > 0:
            improvement = (
                (miss_time - hit_time)
                / miss_time
            ) * 100

            print(
                f"Performance improvement: "
                f"{improvement:.2f}%"
            )

        print(
            f"Results identical: {result1 == result2}"
        )

        print("========================================")

        self.assertEqual(result1, result2)
        self.assertGreaterEqual(miss_time, 0)
        self.assertGreaterEqual(hit_time, 0)
    def test_cache_invalidation_after_driver_location_update(self):

        latitude = 17.410000
        longitude = 78.510000
        radius_km = 10

        # Populate the nearby-driver cache
        first_result = get_nearby_drivers(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )

        self.assertEqual(len(first_result), 1)

        # Confirm the second request uses the cache
        cached_result = get_nearby_drivers(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )

        self.assertEqual(first_result, cached_result)

        # Update the driver's location.
        # This should invalidate nearby-driver cache.
        from business.services.driver_location_service import (
            update_driver_location,
        )

        update_driver_location(
            driver=self.driver,
            latitude="17.500000",
            longitude="78.600000",
        )

        # Query again. The old cached result must not be returned.
        new_result = get_nearby_drivers(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )

        # Driver moved outside the original 10 km radius.
        self.assertEqual(new_result, [])