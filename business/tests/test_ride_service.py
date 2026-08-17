from django.test import TestCase

from business.models import (
    User,
    Ride,
    RideStatus,
    VehicleType,
    Location,
)

from business.services.ride_service import change_ride_status


class RideStatusTransitionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="passenger@test.com",
            password="Test@12345",
            role="USER",
        )

        self.vehicle_type = VehicleType.objects.create(
            name="Test Car",
            description="Test vehicle type",
        )

        self.pickup = Location.objects.create(
            address="Pickup Location",
            latitude="16.3067",
            longitude="80.4365",
        )

        self.drop = Location.objects.create(
            address="Drop Location",
            latitude="16.3200",
            longitude="80.4500",
        )

        self.ride = Ride.objects.create(
            passenger=self.user,
            ride_type=self.vehicle_type,
            pickup_location=self.pickup,
            drop_location=self.drop,
        )

    def test_requested_to_accepted(self):
        ride = change_ride_status(
            self.ride,
            RideStatus.ACCEPTED,
        )

        self.assertEqual(
            ride.status,
            RideStatus.ACCEPTED,
        )

    def test_requested_to_cancelled(self):
        ride = change_ride_status(
            self.ride,
            RideStatus.CANCELLED,
        )

        self.assertEqual(
            ride.status,
            RideStatus.CANCELLED,
        )

    def test_invalid_completed_to_started(self):
        self.ride.status = RideStatus.COMPLETED
        self.ride.save()

        with self.assertRaises(ValueError):
            change_ride_status(
                self.ride,
                RideStatus.STARTED,
            )

    def test_invalid_cancelled_to_accepted(self):
        self.ride.status = RideStatus.CANCELLED
        self.ride.save()

        with self.assertRaises(ValueError):
            change_ride_status(
                self.ride,
                RideStatus.ACCEPTED,
            )