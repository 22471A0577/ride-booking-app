import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Ride


logger = logging.getLogger(__name__)


class RideConsumer(AsyncWebsocketConsumer):

    # =========================================================
    # CONNECT
    # =========================================================

    async def connect(self):

        logger.info(
            "WebSocket connection attempt started"
        )

        try:

            # -------------------------------------------------
            # Get ride ID from URL
            # -------------------------------------------------

            self.ride_id = self.scope[
                "url_route"
            ]["kwargs"]["ride_id"]

            logger.info(
                "WebSocket connection requested | ride_id=%s",
                self.ride_id,
            )

            # -------------------------------------------------
            # Get authenticated user
            # -------------------------------------------------

            self.user = self.scope.get(
                "user"
            )

            # -------------------------------------------------
            # Authentication check
            # -------------------------------------------------

            if self.user is None:

                logger.warning(
                    "WebSocket connection rejected | "
                    "reason=missing_user | ride_id=%s",
                    self.ride_id,
                )

                await self.close(
                    code=4001
                )

                return

            if not self.user.is_authenticated:

                logger.warning(
                    "WebSocket connection rejected | "
                    "reason=unauthenticated_user | ride_id=%s",
                    self.ride_id,
                )

                await self.close(
                    code=4001
                )

                return

            logger.info(
                "WebSocket user authenticated | "
                "user_id=%s | role=%s | ride_id=%s",
                self.user.id,
                getattr(self.user, "role", "UNKNOWN"),
                self.ride_id,
            )

            # -------------------------------------------------
            # Check ride authorization
            # -------------------------------------------------

            ride_access = await self.check_ride_access()

            if not ride_access:

                logger.warning(
                    "WebSocket ride access denied | "
                    "user_id=%s | ride_id=%s",
                    self.user.id,
                    self.ride_id,
                )

                await self.close(
                    code=4003
                )

                return

            logger.info(
                "WebSocket ride authorization successful | "
                "user_id=%s | ride_id=%s",
                self.user.id,
                self.ride_id,
            )

            # -------------------------------------------------
            # Create group
            # -------------------------------------------------

            self.room_group_name = (
                f"ride_{self.ride_id}"
            )

            logger.info(
                "WebSocket group created | "
                "ride_id=%s",
                self.ride_id,
            )

            # -------------------------------------------------
            # Add WebSocket to group
            # -------------------------------------------------

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            logger.info(
                "WebSocket client added to ride group | "
                "ride_id=%s",
                self.ride_id,
            )

            # -------------------------------------------------
            # Accept connection
            # -------------------------------------------------

            await self.accept()

            logger.info(
                "WebSocket connection accepted | "
                "ride_id=%s | user_id=%s",
                self.ride_id,
                self.user.id,
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

            logger.info(
                "Initial WebSocket connection message sent | "
                "ride_id=%s",
                self.ride_id,
            )

        except Exception:

            logger.exception(
                "WebSocket connection failed | "
                "ride_id=%s",
                getattr(
                    self,
                    "ride_id",
                    "unknown",
                ),
            )

            try:

                await self.close(
                    code=4000
                )

            except Exception:

                logger.exception(
                    "Failed to close WebSocket after "
                    "connection error | ride_id=%s",
                    getattr(
                        self,
                        "ride_id",
                        "unknown",
                    ),
                )

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

            logger.warning(
                "WebSocket ride access failed | "
                "reason=ride_not_found | ride_id=%s | "
                "user_id=%s",
                self.ride_id,
                self.user.id,
            )

            return False

        # -----------------------------------------------------
        # ADMIN
        # -----------------------------------------------------

        if self.user.role == "ADMIN":

            logger.info(
                "WebSocket ride access granted | "
                "role=ADMIN | user_id=%s | ride_id=%s",
                self.user.id,
                self.ride_id,
            )

            return True

        # -----------------------------------------------------
        # PASSENGER
        # -----------------------------------------------------

        if ride.passenger_id == self.user.id:

            logger.info(
                "WebSocket ride access granted | "
                "role=PASSENGER | user_id=%s | ride_id=%s",
                self.user.id,
                self.ride_id,
            )

            return True

        # -----------------------------------------------------
        # ASSIGNED DRIVER
        # -----------------------------------------------------

        if (
            ride.driver
            and ride.driver.user_id == self.user.id
        ):

            logger.info(
                "WebSocket ride access granted | "
                "role=DRIVER | user_id=%s | ride_id=%s",
                self.user.id,
                self.ride_id,
            )

            return True

        # -----------------------------------------------------
        # NO ACCESS
        # -----------------------------------------------------

        logger.warning(
            "WebSocket ride access denied | "
            "user_id=%s | ride_id=%s",
            self.user.id,
            self.ride_id,
        )

        return False

    # =========================================================
    # DISCONNECT
    # =========================================================

    async def disconnect(
        self,
        close_code
    ):

        logger.info(
            "WebSocket disconnected | "
            "ride_id=%s | close_code=%s",
            getattr(
                self,
                "ride_id",
                "unknown",
            ),
            close_code,
        )

        if hasattr(
            self,
            "room_group_name"
        ):

            try:

                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )

                logger.info(
                    "WebSocket client removed from ride group | "
                    "ride_id=%s",
                    getattr(
                        self,
                        "ride_id",
                        "unknown",
                    ),
                )

            except Exception:

                logger.exception(
                    "WebSocket group discard failed | "
                    "ride_id=%s",
                    getattr(
                        self,
                        "ride_id",
                        "unknown",
                    ),
                )

    # =========================================================
    # RECEIVE MESSAGE
    # =========================================================

    async def receive(
        self,
        text_data=None,
        bytes_data=None
    ):

        ride_id = getattr(
            self,
            "ride_id",
            "unknown",
        )

        user_id = getattr(
            getattr(
                self,
                "user",
                None,
            ),
            "id",
            "unknown",
        )

        logger.info(
            "WebSocket message received | "
            "ride_id=%s | user_id=%s",
            ride_id,
            user_id,
        )

        # -----------------------------------------------------
        # Empty message
        # -----------------------------------------------------

        if not text_data:

            logger.warning(
                "Empty WebSocket message received | "
                "ride_id=%s | user_id=%s",
                ride_id,
                user_id,
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

            logger.warning(
                "Invalid JSON received through WebSocket | "
                "ride_id=%s | user_id=%s",
                ride_id,
                user_id,
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

        message_type = data.get(
            "type"
        )

        logger.info(
            "WebSocket message parsed | "
            "ride_id=%s | user_id=%s | message_type=%s",
            ride_id,
            user_id,
            message_type,
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

            logger.info(
                "WebSocket ping handled | "
                "ride_id=%s | user_id=%s",
                ride_id,
                user_id,
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

                logger.warning(
                    "Unauthorized driver location attempt | "
                    "user_id=%s | ride_id=%s | role=%s",
                    self.user.id,
                    self.ride_id,
                    getattr(
                        self.user,
                        "role",
                        "UNKNOWN",
                    ),
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
            # Get driver ID and coordinates
            # -------------------------------------------------

            driver_id = str(
                self.user.id
            )

            latitude = data.get(
                "latitude"
            )

            longitude = data.get(
                "longitude"
            )

            # -------------------------------------------------
            # Validate coordinates
            # -------------------------------------------------

            if latitude is None or longitude is None:

                logger.warning(
                    "Driver location rejected because "
                    "coordinates are missing | "
                    "driver_id=%s | ride_id=%s",
                    driver_id,
                    self.ride_id,
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

            try:

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "driver_location_update",
                        "driver_id": driver_id,
                        "latitude": latitude,
                        "longitude": longitude,
                    }
                )

                logger.info(
                    "Driver location broadcasted | "
                    "driver_id=%s | ride_id=%s",
                    driver_id,
                    self.ride_id,
                )

            except Exception:

                logger.exception(
                    "Driver location broadcast failed | "
                    "driver_id=%s | ride_id=%s",
                    driver_id,
                    self.ride_id,
                )

                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "error",
                            "message": (
                                "Unable to broadcast "
                                "driver location."
                            ),
                        }
                    )
                )

            return

        # =====================================================
        # UNKNOWN MESSAGE TYPE
        # =====================================================

        logger.warning(
            "Unknown WebSocket message type | "
            "ride_id=%s | user_id=%s | message_type=%s",
            ride_id,
            user_id,
            message_type,
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

        logger.info(
            "Driver location event received | "
            "ride_id=%s | driver_id=%s",
            getattr(
                self,
                "ride_id",
                "unknown",
            ),
            event.get("driver_id"),
        )

        try:

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

            logger.info(
                "Driver location sent to WebSocket client | "
                "ride_id=%s",
                getattr(
                    self,
                    "ride_id",
                    "unknown",
                ),
            )

        except Exception:

            logger.exception(
                "Failed to send driver location "
                "to WebSocket client | ride_id=%s",
                getattr(
                    self,
                    "ride_id",
                    "unknown",
                ),
            )

    # =========================================================
    # RIDE STATUS EVENT
    # =========================================================

    async def ride_status_update(
        self,
        event
    ):

        logger.info(
            "Ride status event received | "
            "ride_id=%s | status=%s",
            getattr(
                self,
                "ride_id",
                "unknown",
            ),
            event.get("status"),
        )

        try:

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

            logger.info(
                "Ride status sent to WebSocket client | "
                "ride_id=%s | status=%s",
                getattr(
                    self,
                    "ride_id",
                    "unknown",
                ),
                event.get("status"),
            )

        except Exception:

            logger.exception(
                "Failed to send ride status "
                "to WebSocket client | ride_id=%s",
                getattr(
                    self,
                    "ride_id",
                    "unknown",
                ),
            )

