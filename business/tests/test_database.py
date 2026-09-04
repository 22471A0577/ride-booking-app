from django.test import TransactionTestCase
from django.db import IntegrityError, transaction

from business.models import (
    User,
    DriverProfile,
    VehicleType,
    Vehicle,
    Location,
    Ride,
    RideStatus,
)


class DatabaseTests(TransactionTestCase):

    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(
            email="database@test.com",
            password="Test@12345",
            role="USER",
        )

        self.driver_user = User.objects.create_user(
            email="driver_database@test.com",
            password="Test@12345",
            role="DRIVER",
        )

        self.driver = DriverProfile.objects.create(
            user=self.driver_user,
            license_number="DL-DATABASE-001",
            phone_number="9888888888",
            availability_status=(
                DriverProfile.AvailabilityStatus.ONLINE
            ),
        )

        self.vehicle_type = VehicleType.objects.create(
            name="Database Test Car",
            description="Database constraint test vehicle",
        )

        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            vehicle_type=self.vehicle_type,
            vehicle_number="DATABASE-001",
            model_name="Test Model",
            color="Black",
            is_active=True,
        )

        self.pickup = Location.objects.create(
            address="Database Pickup",
            latitude="16.306700",
            longitude="80.436500",
        )

        self.drop = Location.objects.create(
            address="Database Drop",
            latitude="16.320000",
            longitude="80.450000",
        )

    # ========================================================
    # UNIQUE FIELD CONSTRAINTS
    # ========================================================

    def test_user_email_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email="database@test.com",
                password="Test@12345",
                role="USER",
            )

    def test_driver_license_number_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            DriverProfile.objects.create(
                user=User.objects.create_user(
                    email="driver2@test.com",
                    password="Test@12345",
                    role="DRIVER",
                ),
                license_number="DL-DATABASE-001",
                phone_number="9777777777",
                availability_status=(
                    DriverProfile.AvailabilityStatus.OFFLINE
                ),
            )

    def test_driver_phone_number_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            DriverProfile.objects.create(
                user=User.objects.create_user(
                    email="driver3@test.com",
                    password="Test@12345",
                    role="DRIVER",
                ),
                license_number="DL-DATABASE-003",
                phone_number="9888888888",
                availability_status=(
                    DriverProfile.AvailabilityStatus.OFFLINE
                ),
            )

    def test_vehicle_number_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            Vehicle.objects.create(
                driver=self.driver,
                vehicle_type=self.vehicle_type,
                vehicle_number="DATABASE-001",
                model_name="Another Model",
                color="White",
                is_active=True,
            )

    def test_vehicle_type_name_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            VehicleType.objects.create(
                name="Database Test Car",
                description="Duplicate vehicle type",
            )

    # ========================================================
    # ONE-TO-ONE CONSTRAINT
    # ========================================================

    def test_driver_can_have_only_one_driver_profile(self):
        with self.assertRaises(IntegrityError):
            DriverProfile.objects.create(
                user=self.driver_user,
                license_number="DL-DATABASE-004",
                phone_number="9666666666",
                availability_status=(
                    DriverProfile.AvailabilityStatus.OFFLINE
                ),
            )

    # ========================================================
    # FOREIGN KEY RELATIONSHIPS
    # ========================================================

    def test_vehicle_requires_valid_driver(self):
        invalid_driver_id = (
            "00000000-0000-0000-0000-000000000001"
        )

        with self.assertRaises(IntegrityError):
            Vehicle.objects.create(
                driver_id=invalid_driver_id,
                vehicle_type=self.vehicle_type,
                vehicle_number="INVALID-DRIVER-001",
                model_name="Invalid",
                color="Black",
                is_active=True,
            )

    def test_ride_requires_valid_passenger(self):
        invalid_passenger_id = (
            "00000000-0000-0000-0000-000000000001"
        )

        with self.assertRaises(IntegrityError):
            Ride.objects.create(
                passenger_id=invalid_passenger_id,
                ride_type=self.vehicle_type,
                pickup_location=self.pickup,
                drop_location=self.drop,
                status=RideStatus.REQUESTED,
            )

    # ========================================================
    # REQUIRED MODEL FIELDS
    # ========================================================

    def test_location_requires_latitude(self):
        location = Location(
            address="Missing Latitude",
            longitude="80.436500",
        )

        with self.assertRaises(IntegrityError):
            location.save()

    def test_location_requires_longitude(self):
        location = Location(
            address="Missing Longitude",
            latitude="16.306700",
        )

        with self.assertRaises(IntegrityError):
            location.save()

    # ========================================================
    # RIDE REQUIRED RELATIONSHIPS
    # ========================================================

    def test_ride_requires_ride_type(self):
        ride = Ride(
            passenger=self.user,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=RideStatus.REQUESTED,
        )

        with self.assertRaises(IntegrityError):
            ride.save()

    def test_ride_requires_pickup_location(self):
        ride = Ride(
            passenger=self.user,
            ride_type=self.vehicle_type,
            drop_location=self.drop,
            status=RideStatus.REQUESTED,
        )

        with self.assertRaises(IntegrityError):
            ride.save()

    def test_ride_requires_drop_location(self):
        ride = Ride(
            passenger=self.user,
            ride_type=self.vehicle_type,
            pickup_location=self.pickup,
            status=RideStatus.REQUESTED,
        )

        with self.assertRaises(IntegrityError):
            ride.save()

    # ========================================================
    # VALID RIDE RELATIONSHIPS
    # ========================================================

    def test_ride_can_reference_driver_and_vehicle(self):
        ride = Ride.objects.create(
            passenger=self.user,
            driver=self.driver,
            vehicle=self.vehicle,
            ride_type=self.vehicle_type,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=RideStatus.REQUESTED,
        )

        self.assertEqual(
            ride.passenger,
            self.user,
        )

        self.assertEqual(
            ride.driver,
            self.driver,
        )

        self.assertEqual(
            ride.vehicle,
            self.vehicle,
        )

        self.assertEqual(
            ride.ride_type,
            self.vehicle_type,
        )

    # ========================================================
    # OPTIONAL DRIVER / VEHICLE RELATIONSHIPS
    # ========================================================

    def test_ride_can_exist_without_driver_or_vehicle(self):
        ride = Ride.objects.create(
            passenger=self.user,
            driver=None,
            vehicle=None,
            ride_type=self.vehicle_type,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=RideStatus.REQUESTED,
        )

        self.assertIsNone(ride.driver)
        self.assertIsNone(ride.vehicle)
        