import time

from django.test import TestCase
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from business.models import (
    User,
    DriverProfile,
    VehicleType,
    Vehicle,
    Location,
    Ride,
    RideStatus,
    DriverLocation,
    Notification,
)


class APIPerformanceTests(TestCase):

    def setUp(self):

        self.client = APIClient()

        # ====================================================
        # USERS
        # ====================================================

        self.passenger = User.objects.create_user(
            email="performance_passenger@test.com",
            password="Test@12345",
            role="USER",
        )

        self.driver_user = User.objects.create_user(
            email="performance_driver@test.com",
            password="Test@12345",
            role="DRIVER",
        )

        self.admin = User.objects.create_user(
            email="performance_admin@test.com",
            password="Test@12345",
            role="ADMIN",
        )

        # ====================================================
        # DRIVER
        # ====================================================

        self.driver = DriverProfile.objects.create(
            user=self.driver_user,
            license_number="PERF-LICENSE-001",
            phone_number="9888888888",
            availability_status=(
                DriverProfile.AvailabilityStatus.ONLINE
            ),
        )

        # ====================================================
        # VEHICLE TYPE
        # ====================================================

        self.vehicle_type = VehicleType.objects.create(
            name="Performance Test Car",
            description="Performance testing vehicle",
        )

        # ====================================================
        # VEHICLE
        # ====================================================

        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            vehicle_type=self.vehicle_type,
            vehicle_number="PERF-VEHICLE-001",
            model_name="Performance Model",
            color="Black",
            is_active=True,
        )

        # ====================================================
        # LOCATIONS
        # ====================================================

        self.pickup = Location.objects.create(
            address="Performance Pickup",
            latitude="16.306700",
            longitude="80.436500",
        )

        self.drop = Location.objects.create(
            address="Performance Drop",
            latitude="16.320000",
            longitude="80.450000",
        )

        # ====================================================
        # RIDES
        # ====================================================

        self.completed_ride = Ride.objects.create(
            passenger=self.passenger,
            driver=self.driver,
            vehicle=self.vehicle,
            ride_type=self.vehicle_type,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=RideStatus.COMPLETED,
            fare="150.00",
        )

        self.cancelled_ride = Ride.objects.create(
            passenger=self.passenger,
            driver=self.driver,
            vehicle=self.vehicle,
            ride_type=self.vehicle_type,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=RideStatus.CANCELLED,
            fare="100.00",
        )

        # ====================================================
        # ACTIVE RIDE
        # ====================================================

        self.active_ride = Ride.objects.create(
            passenger=self.passenger,
            driver=self.driver,
            vehicle=self.vehicle,
            ride_type=self.vehicle_type,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=RideStatus.ACCEPTED,
            fare="120.00",
        )

        # ====================================================
        # DRIVER LOCATION
        # ====================================================

        DriverLocation.objects.create(
            driver=self.driver,
            latitude="16.307000",
            longitude="80.437000",
        )

        # ====================================================
        # NOTIFICATION
        # ====================================================

        Notification.objects.create(
            user=self.passenger,
            ride=self.completed_ride,
            notification_type="RIDE_COMPLETED",
            title="Ride Completed",
            message="Your ride has been completed.",
            event_key=(
                f"{self.passenger.id}:"
                f"{self.completed_ride.id}:"
                "RIDE_COMPLETED"
            ),
        )

    # ========================================================
    # HELPER
    # ========================================================

    def measure_request(self, method, url, data=None):

        start = time.perf_counter()

        with CaptureQueriesContext(connection) as queries:

            if method == "GET":
                response = self.client.get(url)

            elif method == "POST":
                response = self.client.post(
                    url,
                    data=data,
                    format="json",
                )

            else:
                raise ValueError(
                    f"Unsupported HTTP method: {method}"
                )

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        return response, len(queries), elapsed_ms

    # ========================================================
    # LOGIN
    # ========================================================

    def test_login_performance(self):

        response, query_count, elapsed_ms = (
            self.measure_request(
                "POST",
                "/api/v1/login/",
                {
                    "email": (
                        "performance_passenger@test.com"
                    ),
                    "password": "Test@12345",
                },
            )
        )

        print("\n========================================")
        print("LOGIN PERFORMANCE")
        print("========================================")
        print(
            f"Status Code: {response.status_code}"
        )
        print(
            f"DB Queries: {query_count}"
        )
        print(
            f"Response Time: {elapsed_ms:.3f} ms"
        )
        print("========================================")

        self.assertEqual(
            response.status_code,
            200,
        )

    # ========================================================
    # RIDE DETAILS
    # ========================================================

    def test_ride_detail_performance(self):

        self.client.force_authenticate(
            user=self.passenger
        )

        response, query_count, elapsed_ms = (
            self.measure_request(
                "GET",
                f"/api/v1/rides/{self.completed_ride.id}/",
            )
        )

        print("\n========================================")
        print("RIDE DETAIL PERFORMANCE")
        print("========================================")
        print(
            f"Status Code: {response.status_code}"
        )
        print(
            f"DB Queries: {query_count}"
        )
        print(
            f"Response Time: {elapsed_ms:.3f} ms"
        )
        print("========================================")

        self.assertEqual(
            response.status_code,
            200,
        )

    # ========================================================
    # RIDE HISTORY
    # ========================================================

    def test_ride_history_performance(self):

        self.client.force_authenticate(
            user=self.passenger
        )

        response, query_count, elapsed_ms = (
            self.measure_request(
                "GET",
                "/api/v1/rides/history/",
            )
        )

        print("\n========================================")
        print("RIDE HISTORY PERFORMANCE")
        print("========================================")
        print(
            f"Status Code: {response.status_code}"
        )
        print(
            f"DB Queries: {query_count}"
        )
        print(
            f"Response Time: {elapsed_ms:.3f} ms"
        )
        print("========================================")

        self.assertEqual(
            response.status_code,
            200,
        )

    # ========================================================
    # ACTIVE RIDES
    # ========================================================

    def test_active_rides_performance(self):

        self.client.force_authenticate(
            user=self.passenger
        )

        response, query_count, elapsed_ms = (
            self.measure_request(
                "GET",
                "/api/v1/rides/active/",
            )
        )

        print("\n========================================")
        print("ACTIVE RIDES PERFORMANCE")
        print("========================================")
        print(
            f"Status Code: {response.status_code}"
        )
        print(
            f"DB Queries: {query_count}"
        )
        print(
            f"Response Time: {elapsed_ms:.3f} ms"
        )
        print("========================================")

        self.assertEqual(
            response.status_code,
            200,
        )

    # ========================================================
    # DRIVER LOCATION
    # ========================================================

    def test_driver_location_performance(self):

        self.client.force_authenticate(
            user=self.driver_user
        )

        response, query_count, elapsed_ms = (
            self.measure_request(
                "POST",
                "/api/v1/drivers/location/",
                {
                    "latitude": 16.308000,
                    "longitude": 80.438000,
                },
            )
        )

        print("\n========================================")
        print("DRIVER LOCATION PERFORMANCE")
        print("========================================")
        print(
            f"Status Code: {response.status_code}"
        )
        print(
            f"DB Queries: {query_count}"
        )
        print(
            f"Response Time: {elapsed_ms:.3f} ms"
        )
        print("========================================")

        self.assertIn(
            response.status_code,
            [200, 201],
        )

    # ========================================================
    # NEARBY DRIVERS
    # ========================================================

    def test_nearby_drivers_performance(self):

        self.client.force_authenticate(
            user=self.passenger
        )

        response, query_count, elapsed_ms = (
            self.measure_request(
                "GET",
                "/api/v1/drivers/nearby/"
                "?latitude=16.307000"
                "&longitude=80.437000"
                "&radius=10",
            )
        )

        print("\n========================================")
        print("NEARBY DRIVERS PERFORMANCE")
        print("========================================")
        print(
            f"Status Code: {response.status_code}"
        )
        print(
            f"DB Queries: {query_count}"
        )
        print(
            f"Response Time: {elapsed_ms:.3f} ms"
        )
        print("========================================")

        self.assertEqual(
            response.status_code,
            200,
        )

    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    def test_notifications_performance(self):

        self.client.force_authenticate(
            user=self.passenger
        )

        response, query_count, elapsed_ms = (
            self.measure_request(
                "GET",
                "/api/v1/notifications/",
            )
        )

        print("\n========================================")
        print("NOTIFICATIONS PERFORMANCE")
        print("========================================")
        print(
            f"Status Code: {response.status_code}"
        )
        print(
            f"DB Queries: {query_count}"
        )
        print(
            f"Response Time: {elapsed_ms:.3f} ms"
        )
        print("========================================")

        self.assertEqual(
            response.status_code,
            200,
        )