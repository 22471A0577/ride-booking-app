from django.test import TestCase
from rest_framework.test import APIClient

from business.models import (
    User,
    DriverProfile,
    Vehicle,
    VehicleType,
    Location,
    Ride,
    RideStatus,
)


class RideAPITests(TestCase):

    def setUp(self):

        self.client = APIClient()

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

    def create_ride(self):
        return Ride.objects.create(
            passenger=self.passenger,
            ride_type=self.vehicle_type,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=RideStatus.REQUESTED,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_create_ride_api(self):

        self.authenticate(self.passenger)

        response = self.client.post(
            "/api/v1/rides/",
            {
                "ride_type": self.vehicle_type.id,
                "pickup_location": self.pickup.id,
                "drop_location": self.drop.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        ride = Ride.objects.get(
            passenger=self.passenger
        )

        self.assertEqual(
            ride.status,
            RideStatus.REQUESTED,
        )

        self.assertEqual(
            ride.passenger,
            self.passenger,
        )
    def test_ride_history_pagination(self):

        # Create 25 completed rides so they appear in ride history.
        for _ in range(25):
            ride = self.create_ride()

            ride.status = RideStatus.COMPLETED

            ride.save(
                update_fields=["status"]
            )

        self.authenticate(self.passenger)

        response = self.client.get(
            "/api/v1/rides/history/?page=1"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        # Pagination metadata
        self.assertIn("count", data)
        self.assertIn("next", data)
        self.assertIn("previous", data)
        self.assertIn("results", data)

        # Default page size = 20
        self.assertEqual(
            len(data["results"]),
            20,
        )

        # Total historical rides = 25
        self.assertEqual(
            data["count"],
            25,
        )

        # Page 2 must exist
        self.assertIsNotNone(
            data["next"]
        )
    def test_driver_can_accept_ride_api(self):

        ride = self.create_ride()

        self.authenticate(self.driver_user)

        response = self.client.post(
            f"/api/v1/rides/{ride.id}/accept/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        ride.refresh_from_db()

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

    def test_driver_can_start_ride_api(self):

        ride = self.create_ride()
        ride.driver = self.driver
        ride.vehicle = self.vehicle
        ride.status = RideStatus.DRIVER_ARRIVING
        ride.save(
                update_fields=[
                    "driver",
                    "vehicle",
                    "status",
                ]
            )
        
        self.authenticate(self.driver_user)
        
        response = self.client.patch(
                f"/api/v1/rides/{ride.id}/status/",
                {
                    "status": RideStatus.STARTED,
                },
                format="json",
            )
        
        self.assertEqual(response.status_code, 200)
        
        ride.refresh_from_db()
        
        self.assertEqual(
                ride.status,
                RideStatus.STARTED,
            )

    
    def test_driver_can_complete_ride_api(self):

        ride = self.create_ride()

        ride.driver = self.driver
        ride.vehicle = self.vehicle
        ride.status = RideStatus.STARTED
        ride.save(
            update_fields=[
                "driver",
                "vehicle",
                "status",
            ]
        )

        self.authenticate(self.driver_user)

        response = self.client.patch(
            f"/api/v1/rides/{ride.id}/status/",
            {
                "status": RideStatus.COMPLETED,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        ride.refresh_from_db()

        self.assertEqual(
            ride.status,
            RideStatus.COMPLETED,
        )

    def test_passenger_can_cancel_ride_api(self):

        ride = self.create_ride()

        self.authenticate(self.passenger)

        response = self.client.post(
            f"/api/v1/rides/{ride.id}/cancel/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        ride.refresh_from_db()

        self.assertEqual(
            ride.status,
            RideStatus.CANCELLED,
        )

    def test_invalid_status_transition_rejected(self):

        ride = self.create_ride()

        ride.driver = self.driver
        ride.vehicle = self.vehicle
        ride.status = RideStatus.ACCEPTED
        ride.save(
            update_fields=[
                "driver",
                "vehicle",
                "status",
            ]
        )

        self.authenticate(self.driver_user)

        response = self.client.patch(
            f"/api/v1/rides/{ride.id}/status/",
            {
                "status": RideStatus.COMPLETED,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        ride.refresh_from_db()

        self.assertEqual(
            ride.status,
            RideStatus.ACCEPTED,
        )