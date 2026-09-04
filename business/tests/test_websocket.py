from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from django.test import TransactionTestCase
from django.contrib.auth.models import AnonymousUser

from business.consumers import RideConsumer
from business.models import (
    User,
    DriverProfile,
    VehicleType,
    Vehicle,
    Location,
    Ride,
    RideStatus,
)


class WebSocketTests(TransactionTestCase):

    def setUp(self):
        self.passenger = User.objects.create_user(
            email="ws_passenger@test.com",
            password="Test@12345",
            role="USER",
        )

        self.driver_user = User.objects.create_user(
            email="ws_driver@test.com",
            password="Test@12345",
            role="DRIVER",
        )

        self.driver = DriverProfile.objects.create(
            user=self.driver_user,
            license_number="WS-LICENSE-001",
            phone_number="9777777777",
            availability_status=(
                DriverProfile.AvailabilityStatus.ONLINE
            ),
        )

        self.vehicle_type = VehicleType.objects.create(
            name="WebSocket Test Car",
            description="WebSocket testing vehicle",
        )

        self.vehicle = Vehicle.objects.create(
            driver=self.driver,
            vehicle_type=self.vehicle_type,
            vehicle_number="WS-VEHICLE-001",
            model_name="Test Model",
            color="Black",
            is_active=True,
        )

        self.pickup = Location.objects.create(
            address="WebSocket Pickup",
            latitude="16.306700",
            longitude="80.436500",
        )

        self.drop = Location.objects.create(
            address="WebSocket Drop",
            latitude="16.320000",
            longitude="80.450000",
        )

        self.ride = Ride.objects.create(
            passenger=self.passenger,
            driver=self.driver,
            vehicle=self.vehicle,
            ride_type=self.vehicle_type,
            pickup_location=self.pickup,
            drop_location=self.drop,
            status=RideStatus.ACCEPTED,
            fare="150.00",
        )

    def create_communicator(self, user):
        communicator = WebsocketCommunicator(
            RideConsumer.as_asgi(),
            f"/ws/rides/{self.ride.id}/",
        )

        communicator.scope["url_route"] = {
            "kwargs": {
                "ride_id": str(self.ride.id),
            }
        }

        communicator.scope["user"] = user

        return communicator

    async def test_authenticated_user_can_connect(self):
        communicator = self.create_communicator(
            self.passenger
        )

        connected, _ = await communicator.connect()

        self.assertTrue(connected)

        response = await communicator.receive_json_from()

        self.assertEqual(
            response["type"],
            "connection",
        )

        self.assertEqual(
            response["ride_id"],
            str(self.ride.id),
        )

        await communicator.disconnect()

    async def test_anonymous_user_is_rejected(self):
        communicator = self.create_communicator(
            AnonymousUser()
        )

        connected, close_code = await communicator.connect()

        self.assertFalse(connected)

        self.assertEqual(
            close_code,
            4001,
        )

    async def test_ping_returns_pong(self):
        communicator = self.create_communicator(
            self.passenger
        )

        connected, _ = await communicator.connect()

        self.assertTrue(connected)

        await communicator.receive_json_from()

        await communicator.send_json_to({
            "type": "ping"
        })

        response = await communicator.receive_json_from()

        self.assertEqual(
            response["type"],
            "pong",
        )

        self.assertEqual(
            response["message"],
            "WebSocket is working.",
        )

        self.assertEqual(
            response["ride_id"],
            str(self.ride.id),
        )

        await communicator.disconnect()

    async def test_ride_status_event_is_sent(self):
        communicator = self.create_communicator(
            self.passenger
        )

        connected, _ = await communicator.connect()

        self.assertTrue(connected)

        await communicator.receive_json_from()

        channel_layer = get_channel_layer()

        await channel_layer.group_send(
            f"ride_{self.ride.id}",
            {
                "type": "ride_status_update",
                "status": "STARTED",
                "message": "Ride has started.",
            },
        )

        response = await communicator.receive_json_from()

        self.assertEqual(
            response["type"],
            "ride_status_update",
        )

        self.assertEqual(
            response["status"],
            "STARTED",
        )

        self.assertEqual(
            response["message"],
            "Ride has started.",
        )

        await communicator.disconnect()

    async def test_driver_location_event_is_sent(self):
        communicator = self.create_communicator(
            self.driver_user
        )

        connected, _ = await communicator.connect()

        self.assertTrue(connected)

        await communicator.receive_json_from()

        await communicator.send_json_to({
            "type": "driver_location",
            "latitude": 16.307000,
            "longitude": 80.437000,
        })

        response = await communicator.receive_json_from()

        self.assertEqual(
            response["type"],
            "driver_location_update",
        )

        self.assertEqual(
            response["latitude"],
            16.307000,
        )

        self.assertEqual(
            response["longitude"],
            80.437000,
        )

        await communicator.disconnect()

    async def test_passenger_cannot_send_driver_location(self):
        communicator = self.create_communicator(
            self.passenger
        )

        connected, _ = await communicator.connect()

        self.assertTrue(connected)

        await communicator.receive_json_from()

        await communicator.send_json_to({
            "type": "driver_location",
            "latitude": 16.307000,
            "longitude": 80.437000,
        })

        response = await communicator.receive_json_from()

        self.assertEqual(
            response["type"],
            "error",
        )

        self.assertIn(
            "Only drivers can send driver location",
            response["message"],
        )

        await communicator.disconnect()