from django.test import TestCase
from rest_framework.exceptions import ValidationError

from business.models import (
    User,
    VehicleType,
    Location,
    Ride,
)
from business.serializers import RideSerializer


class RideCreationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="passenger@test.com",
            password="Test@12345",
            role="USER",
        )

        self.vehicle_type = VehicleType.objects.create(
            name="Test Car",
            description="Test vehicle",
        )

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

    def test_user_can_create_ride(self):

        data = {
            "ride_type": self.vehicle_type.id,
            "pickup_location": self.pickup.id,
            "drop_location": self.drop.id,
        }

        serializer = RideSerializer(
            data=data,
            context={
                "request": type(
                    "Request",
                    (),
                    {"user": self.user}
                )()
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        ride = serializer.save(
            passenger=self.user
        )

        self.assertEqual(
            ride.passenger,
            self.user
        )

        self.assertEqual(
            ride.status,
            "REQUESTED"
        )

    def test_pickup_and_drop_cannot_be_same(self):

        data = {
            "ride_type": self.vehicle_type.id,
            "pickup_location": self.pickup.id,
            "drop_location": self.pickup.id,
        }

        serializer = RideSerializer(
            data=data,
            context={
                "request": type(
                    "Request",
                    (),
                    {"user": self.user}
                )()
            }
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "drop_location",
            serializer.errors
        )

    def test_user_cannot_create_second_active_ride(self):

        Ride.objects.create(
            passenger=self.user,
            ride_type=self.vehicle_type,
            pickup_location=self.pickup,
            drop_location=self.drop,
        )

        data = {
            "ride_type": self.vehicle_type.id,
            "pickup_location": self.pickup.id,
            "drop_location": self.drop.id,
        }

        serializer = RideSerializer(
            data=data,
            context={
                "request": type(
                    "Request",
                    (),
                    {"user": self.user}
                )()
            }
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn(
            "passenger",
            serializer.errors
        )
    def test_ride_requires_ride_type(self):

        data = {
            "pickup_location": self.pickup.id,
            "drop_location": self.drop.id,
        }

        serializer = RideSerializer(
            data=data,
            context={
                "request": type(
                    "Request",
                    (),
                    {"user": self.user}
                )()
            }
        )

        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "ride_type",
            serializer.errors
        )


    def test_ride_requires_pickup_location(self):

        data = {
            "ride_type": self.vehicle_type.id,
            "drop_location": self.drop.id,
        }

        serializer = RideSerializer(
            data=data,
            context={
                "request": type(
                    "Request",
                    (),
                    {"user": self.user}
                )()
            }
        )

        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "pickup_location",
            serializer.errors
        )


    def test_ride_requires_drop_location(self):

        data = {
            "ride_type": self.vehicle_type.id,
            "pickup_location": self.pickup.id,
        }

        serializer = RideSerializer(
            data=data,
            context={
                "request": type(
                    "Request",
                    (),
                    {"user": self.user}
                )()
            }
        )

        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "drop_location",
            serializer.errors
        )


    def test_invalid_vehicle_type_rejected(self):

        data = {
            "ride_type": 999999,
            "pickup_location": self.pickup.id,
            "drop_location": self.drop.id,
        }

        serializer = RideSerializer(
            data=data,
            context={
                "request": type(
                    "Request",
                    (),
                    {"user": self.user}
                )()
            }
        )

        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "ride_type",
            serializer.errors
        )