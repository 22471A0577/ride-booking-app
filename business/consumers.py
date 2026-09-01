import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Ride


class RideConsumer(AsyncWebsocketConsumer):

    # =========================================================
    # CONNECT
    # =========================================================

    async def connect(self):

        print("\n========================================")
        print("=== WEBSOCKET CONNECT START ===")
        print("========================================")

        try:

            # -------------------------------------------------
            # Get ride ID from URL
            # -------------------------------------------------

            self.ride_id = self.scope[
                "url_route"
            ]["kwargs"]["ride_id"]

            print(
                "Ride ID:",
                self.ride_id
            )

            # -------------------------------------------------
            # Get authenticated user
            # -------------------------------------------------

            self.user = self.scope.get(
                "user"
            )

            print(
                "User:",
                self.user
            )

            # -------------------------------------------------
            # Authentication check
            # -------------------------------------------------

            if self.user is None:

                print(
                    "❌ USER IS NONE"
                )

                await self.close(
                    code=4001
                )

                return

            if not self.user.is_authenticated:

                print(
                    "❌ USER NOT AUTHENTICATED"
                )

                await self.close(
                    code=4001
                )

                return

            print(
                "=== USER AUTHENTICATED ==="
            )

            print(
                "User ID:",
                self.user.id
            )

            print(
                "User email:",
                self.user.email
            )

            print(
                "User role:",
                self.user.role
            )

            # -------------------------------------------------
            # Check ride authorization
            # -------------------------------------------------

            ride_access = await self.check_ride_access()

            if not ride_access:

                print(
                    "❌ USER NOT AUTHORIZED FOR THIS RIDE"
                )

                await self.close(
                    code=4003
                )

                return

            print(
                "=== RIDE AUTHORIZATION SUCCESS ==="
            )

            # -------------------------------------------------
            # Create group
            # -------------------------------------------------

            self.room_group_name = (
                f"ride_{self.ride_id}"
            )

            print(
                "Room group:",
                self.room_group_name
            )

            # -------------------------------------------------
            # Add WebSocket to group
            # -------------------------------------------------

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            print(
                "=== GROUP ADD SUCCESS ==="
            )

            # -------------------------------------------------
            # Accept connection
            # -------------------------------------------------

            await self.accept()

            print(
                "=== WEBSOCKET ACCEPTED ==="
            )

            # -------------------------------------------------
            # Send connection response
            # -------------------------------------------------

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "connection",
                        "message": (
                            "WebSocket connected successfully."
                        ),
                        "ride_id": str(
                            self.ride_id
                        ),
                    }
                )
            )

            print(
                "=== INITIAL MESSAGE SENT ==="
            )

            print(
                "=== WAITING FOR CLIENT MESSAGE ==="
            )

        except Exception as e:

            print(
                "\n❌ ERROR IN CONNECT"
            )

            print(
                "Error type:",
                type(e).__name__
            )

            print(
                "Error:",
                str(e)
            )

            try:

                await self.close(
                    code=4000
                )

            except Exception:
                pass

    # =========================================================
    # RIDE ACCESS CHECK
    # =========================================================

    @database_sync_to_async
    def check_ride_access(self):

        try:

            ride = Ride.objects.select_related(
                "passenger",
                "driver__user",
            ).get(
                pk=self.ride_id
            )

        except Ride.DoesNotExist:

            print(
                "❌ RIDE DOES NOT EXIST"
            )

            return False

        # -----------------------------------------------------
        # ADMIN
        # -----------------------------------------------------

        if self.user.role == "ADMIN":

            print(
                "✅ ADMIN ACCESS"
            )

            return True

        # -----------------------------------------------------
        # PASSENGER
        # -----------------------------------------------------

        if ride.passenger_id == self.user.id:

            print(
                "✅ PASSENGER ACCESS"
            )

            return True

        # -----------------------------------------------------
        # ASSIGNED DRIVER
        # -----------------------------------------------------

        if (
            ride.driver
            and ride.driver.user_id == self.user.id
        ):

            print(
                "✅ ASSIGNED DRIVER ACCESS"
            )

            return True

        # -----------------------------------------------------
        # NO ACCESS
        # -----------------------------------------------------

        print(
            "❌ ACCESS DENIED"
        )

        return False

    # =========================================================
    # DISCONNECT
    # =========================================================

    async def disconnect(
        self,
        close_code
    ):

        print("\n========================================")
        print("=== WEBSOCKET DISCONNECT ===")
        print(
            "Close code:",
            close_code
        )
        print("========================================")

        if hasattr(
            self,
            "room_group_name"
        ):

            try:

                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )

                print(
                    "=== GROUP DISCARD SUCCESS ==="
                )

            except Exception as e:

                print(
                    "❌ GROUP DISCARD ERROR:",
                    str(e)
                )

    # =========================================================
    # RECEIVE MESSAGE
    # =========================================================

    async def receive(
        self,
        text_data=None,
        bytes_data=None
    ):

        print("\n========================================")
        print("=== MESSAGE RECEIVED ===")
        print(
            "Text data:",
            text_data
        )
        print("========================================")

        # -----------------------------------------------------
        # Empty message
        # -----------------------------------------------------

        if not text_data:

            print(
                "❌ EMPTY MESSAGE"
            )

            return

        # -----------------------------------------------------
        # Parse JSON
        # -----------------------------------------------------

        try:

            data = json.loads(
                text_data
            )

        except json.JSONDecodeError:

            print(
                "❌ INVALID JSON"
            )

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "message": (
                            "Invalid JSON message."
                        ),
                    }
                )
            )

            return

        print(
            "Parsed data:",
            data
        )

        message_type = data.get(
            "type"
        )

        print(
            "Message type:",
            message_type
        )

        # =====================================================
        # PING
        # =====================================================

        if message_type == "ping":

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "pong",
                        "message": (
                            "WebSocket is working."
                        ),
                        "ride_id": str(
                            self.ride_id
                        ),
                    }
                )
            )

            return

        # =====================================================
        # DRIVER LOCATION
        # =====================================================

        if message_type == "driver_location":

            # -------------------------------------------------
            # Only drivers can send location
            # -------------------------------------------------

            if self.user.role != "DRIVER":

                print(
                    "❌ NON-DRIVER TRIED TO SEND LOCATION"
                )

                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "error",
                            "message": (
                                "Only drivers can "
                                "send driver location."
                            ),
                        }
                    )
                )

                return

            # -------------------------------------------------
            # IMPORTANT FIX
            # -------------------------------------------------

            driver_id = str(self.user.id)

            latitude = data.get(
                "latitude"
            )

            longitude = data.get(
                "longitude"
            )

            print(
                "Driver ID:",
                driver_id
            )

            print(
                "Latitude:",
                latitude
            )

            print(
                "Longitude:",
                longitude
            )

            # -------------------------------------------------
            # Validate coordinates
            # -------------------------------------------------

            if latitude is None or longitude is None:

                print(
                    "❌ LOCATION COORDINATES MISSING"
                )

                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "error",
                            "message": (
                                "Latitude and longitude "
                                "are required."
                            ),
                        }
                    )
                )

                return

            # -------------------------------------------------
            # Broadcast driver location
            # -------------------------------------------------

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "driver_location_update",
                    "driver_id": driver_id,
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )

            print(
                "=== DRIVER LOCATION BROADCASTED ==="
            )

            return

        # =====================================================
        # UNKNOWN MESSAGE
        # =====================================================

        print(
            "❌ UNKNOWN MESSAGE TYPE:",
            message_type
        )

        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": (
                        f"Unknown message type: "
                        f"{message_type}"
                    ),
                }
            )
        )

    # =========================================================
    # DRIVER LOCATION EVENT
    # =========================================================

    async def driver_location_update(
        self,
        event
    ):

        print(
            "=== DRIVER LOCATION EVENT ==="
        )

        print(
            "Driver ID:",
            event.get("driver_id")
        )

        print(
            "Latitude:",
            event.get("latitude")
        )

        print(
            "Longitude:",
            event.get("longitude")
        )

        await self.send(
            text_data=json.dumps(
                {
                    "type": "driver_location_update",
                    "driver_id": event.get(
                        "driver_id"
                    ),
                    "latitude": event.get(
                        "latitude"
                    ),
                    "longitude": event.get(
                        "longitude"
                    ),
                }
            )
        )

        print(
            "=== DRIVER LOCATION SENT TO CLIENT ==="
        )

    # =========================================================
    # RIDE STATUS EVENT
    # =========================================================

    async def ride_status_update(
        self,
        event
    ):

        print(
            "=== RIDE STATUS EVENT ==="
        )

        print(
            "Status:",
            event.get("status")
        )

        print(
            "Message:",
            event.get("message")
        )

        await self.send(
            text_data=json.dumps(
                {
                    "type": "ride_status_update",
                    "status": event.get(
                        "status"
                    ),
                    "message": event.get(
                        "message"
                    ),
                }
            )
        )

        print(
            "=== RIDE STATUS SENT TO CLIENT ==="
        )