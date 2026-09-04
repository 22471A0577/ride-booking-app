from django.test import TestCase
from django.core.cache import cache

from business.models import (
    User,
    DriverProfile,
    VehicleType,
    Vehicle,
    Location,
    Ride,
    RideStatus,
    DriverLocation,
)

from business.services.driver_service import (
    get_available_driver_vehicle,
    set_driver_availability,
)

from business.services.driver_location_service import (
    calculate_distance_km,
    get_nearby_drivers,
)


class BusinessLogicTests(TestCase):

    def setUp(self):
        # Clear cache so every test starts with a clean state.
        cache.clear()

        self.user = User.objects.create_user(
            email="driver@test.com",
            password="Test@12345",
            role="DRIVER",
        )

        self.driver = DriverProfile.objects.create(
            user=self.user,
            license_number="DL-BUSINESS-001",
            phone_number="9999999999",
            availability_status=DriverProfile.AvailabilityStatus.ONLINE,
        )

        self.vehicle_type = VehicleType.objects.create(
            name="Business Test Car",
            description="Business logic test vehicle",
        )

        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            vehicle_type=self.vehicle_type,
            vehicle_number="BUSINESS-001",
            model_name="Test Model",
            color="White",
            is_active=True,
        )

    # ========================================================
    # DRIVER AVAILABILITY
    # ========================================================

    def test_available_driver_returns_active_vehicle(self):
        vehicle = get_available_driver_vehicle(self.driver)

        self.assertEqual(
            vehicle,
            self.vehicle,
        )

    def test_unavailable_driver_rejected(self):
        self.driver.availability_status = (
            DriverProfile.AvailabilityStatus.OFFLINE
        )

        self.driver.save(
            update_fields=["availability_status"]
        )

        with self.assertRaises(ValueError):
            get_available_driver_vehicle(self.driver)

    def test_driver_with_active_ride_rejected(self):
        passenger = User.objects.create_user(
            email="passenger@test.com",
            password="Test@12345",
            role="USER",
        )

        pickup = Location.objects.create(
            address="Pickup",
            latitude="16.306700",
            longitude="80.436500",
        )

        drop = Location.objects.create(
            address="Drop",
            latitude="16.320000",
            longitude="80.450000",
        )

        Ride.objects.create(
            passenger=passenger,
            driver=self.driver,
            vehicle=self.vehicle,
            ride_type=self.vehicle_type,
            pickup_location=pickup,
            drop_location=drop,
            status=RideStatus.ACCEPTED,
        )

        with self.assertRaises(ValueError):
            get_available_driver_vehicle(self.driver)

    def test_set_driver_availability_offline(self):
        set_driver_availability(
            self.driver,
            False,
        )

        self.driver.refresh_from_db()

        self.assertEqual(
            self.driver.availability_status,
            DriverProfile.AvailabilityStatus.OFFLINE,
        )

    # ========================================================
    # HAVERSINE DISTANCE
    # ========================================================

    def test_distance_between_same_coordinates_is_zero(self):
        distance = calculate_distance_km(
            16.3067,
            80.4365,
            16.3067,
            80.4365,
        )

        self.assertAlmostEqual(
            distance,
            0,
            places=5,
        )

    def test_distance_calculation_returns_positive_value(self):
        distance = calculate_distance_km(
            16.3067,
            80.4365,
            16.3200,
            80.4500,
        )

        self.assertGreater(
            distance,
            0,
        )

    # ========================================================
    # NEARBY DRIVER SELECTION
    # ========================================================

    def test_nearby_driver_is_returned_within_radius(self):
        DriverLocation.objects.create(
            driver=self.driver,
            latitude="16.306700",
            longitude="80.436500",
        )

        result = get_nearby_drivers(
            latitude=16.3067,
            longitude=80.4365,
            radius_km=5,
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["driver_id"],
            str(self.driver.id),
        )

    def test_driver_outside_radius_is_not_returned(self):
        DriverLocation.objects.create(
            driver=self.driver,
            latitude="17.410000",
            longitude="78.510000",
        )

        result = get_nearby_drivers(
            latitude=16.3067,
            longitude=80.4365,
            radius_km=5,
        )

        self.assertEqual(
            result,
            [],
        )

    def test_offline_driver_is_not_returned(self):
        self.driver.availability_status = (
            DriverProfile.AvailabilityStatus.OFFLINE
        )

        self.driver.save(
            update_fields=["availability_status"]
        )

        DriverLocation.objects.create(
            driver=self.driver,
            latitude="16.306700",
            longitude="80.436500",
        )

        result = get_nearby_drivers(
            latitude=16.3067,
            longitude=80.4365,
            radius_km=5,
        )

        self.assertEqual(
            result,
            [],
        )