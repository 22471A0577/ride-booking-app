from django.test import TestCase

from business.models import (
    User,
    DriverProfile,
    Vehicle,
    VehicleType,
    Location,
    Ride,
    RideStatus,
)

from business.services.ride_service import accept_ride


class RideAcceptanceTests(TestCase):

    def setUp(self):

        # Passenger
        self.passenger = User.objects.create_user(
            email="passenger@test.com",
            password="Test@12345",
            role="USER",
        )

        # Driver
        self.driver_user = User.objects.create_user(
            email="driver@test.com",
            password="Test@12345",
            role="DRIVER",
        )

        self.driver = DriverProfile.objects.create(
            user=self.driver_user,
            license_number="DL-TEST-001",
            phone_number="9999999999",
            availability_status="ONLINE",
        )

        # Vehicle type
        self.vehicle_type = VehicleType.objects.create(
            name="Test Car",
            description="Test vehicle",
        )

        # Driver vehicle
        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            vehicle_type=self.vehicle_type,
            vehicle_number="TEST-001",
            model_name="Test Model",
            color="White",
            is_active=True,
        )

        # Locations
        self.pickup = Location.objects.create(
            address="Pickup Location",
            latitude="16.306700",
            longitude="80.436500",
        )

        self.drop = Location.objects.create(
            address="Drop Location",
            latitude="16.320000",
            longitude="80.450000",
        )

        # Ride
        self.ride = Ride.objects.create(
            passenger=self.passenger,
            ride_type=self.vehicle_type,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=RideStatus.REQUESTED,
        )

    def test_driver_can_accept_ride(self):

        ride = accept_ride(
            self.ride.id,
            self.driver,
        )

        self.assertEqual(
            ride.status,
            RideStatus.ACCEPTED,
        )

        self.assertEqual(
            ride.driver,
            self.driver,
        )

        self.assertEqual(
            ride.vehicle,
            self.vehicle,
        )

    def test_already_accepted_ride_cannot_be_accepted_again(self):

        accept_ride(
            self.ride.id,
            self.driver,
        )

        with self.assertRaises(ValueError):
            accept_ride(
                self.ride.id,
                self.driver,
            )

    def test_unavailable_driver_cannot_accept(self):

        self.driver.availability_status = "OFFLINE"
        self.driver.save(update_fields=["availability_status"])

        with self.assertRaises(ValueError):
            accept_ride(
                self.ride.id,
                self.driver,
            )

    def test_driver_without_vehicle_cannot_accept(self):

        self.vehicle.delete()

        with self.assertRaises(ValueError):
            accept_ride(
                self.ride.id,
                self.driver,
            )

    def test_driver_with_active_ride_cannot_accept_another_ride(self):

        first_ride = self.ride

        accept_ride(
            first_ride.id,
            self.driver,
        )

        second_ride = Ride.objects.create(
            passenger=self.passenger,
            ride_type=self.vehicle_type,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=RideStatus.REQUESTED,
        )

        with self.assertRaises(ValueError):
            accept_ride(
                second_ride.id,
                self.driver,
            )

