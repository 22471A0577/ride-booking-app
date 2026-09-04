import logging

from django.db import transaction

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from business.tasks import create_notification
from business.models import Ride, RideStatus, Vehicle


logger = logging.getLogger(__name__)


# ============================================================
# ALLOWED RIDE STATUS TRANSITIONS
# ============================================================

ALLOWED_TRANSITIONS = {
    RideStatus.REQUESTED: [
        RideStatus.ACCEPTED,
        RideStatus.CANCELLED,
    ],

    RideStatus.ACCEPTED: [
        RideStatus.DRIVER_ARRIVING,
        RideStatus.CANCELLED,
    ],

    RideStatus.DRIVER_ARRIVING: [
        RideStatus.STARTED,
    ],

    RideStatus.STARTED: [
        RideStatus.COMPLETED,
    ],

    RideStatus.COMPLETED: [],

    RideStatus.CANCELLED: [],
}


# ============================================================
# ACTIVE RIDE STATUSES
# ============================================================

ACTIVE_RIDE_STATUSES = [
    RideStatus.REQUESTED,
    RideStatus.ACCEPTED,
    RideStatus.DRIVER_ARRIVING,
    RideStatus.STARTED,
]


# ============================================================
# SEND RIDE STATUS UPDATE
# ============================================================

def send_ride_status_update(ride_id, status_value):
    """
    Send ride status update to all WebSocket clients
    connected to this ride.
    """

    channel_layer = get_channel_layer()

    if channel_layer is None:
        logger.error(
            "Channel layer is not configured"
        )
        return

    group_name = f"ride_{ride_id}"

    logger.info(
        "Sending ride status update | ride_id=%s | status=%s",
        ride_id,
        status_value,
    )

    try:
        async_to_sync(
            channel_layer.group_send
        )(
            group_name,
            {
                "type": "ride_status_update",
                "status": str(status_value),
                "message": (
                    f"Ride status changed to {status_value}"
                ),
            },
        )

        logger.info(
            "Ride status update sent | ride_id=%s | status=%s",
            ride_id,
            status_value,
        )

    except Exception:
        logger.exception(
            "WebSocket status update failed | ride_id=%s",
            ride_id,
        )


# ============================================================
# CHANGE RIDE STATUS
# ============================================================

@transaction.atomic
def change_ride_status(ride, new_status):
    """
    Safely change ride status.

    Responsibilities:

    1. Validate status transition.
    2. Update ride status.
    3. Register WebSocket notification after DB commit.
    4. Register background notification after DB commit.

    User/role authorization belongs in the API view.
    """

    current_status = ride.status

    logger.info(
        "Changing ride status | ride_id=%s | "
        "from=%s | to=%s",
        ride.id,
        current_status,
        new_status,
    )

    # --------------------------------------------------------
    # Validate transition
    # --------------------------------------------------------

    allowed_statuses = ALLOWED_TRANSITIONS.get(
        current_status,
        [],
    )

    if new_status not in allowed_statuses:

        logger.warning(
            "Invalid ride status transition | ride_id=%s | "
            "from=%s | to=%s",
            ride.id,
            current_status,
            new_status,
        )

        raise ValueError(
            f"Cannot change ride status "
            f"from {current_status} to {new_status}."
        )

    # --------------------------------------------------------
    # Change status
    # --------------------------------------------------------

    ride.status = new_status

    ride.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    logger.info(
        "Ride status updated | ride_id=%s | status=%s",
        ride.id,
        ride.status,
    )

    # --------------------------------------------------------
    # Convert IDs/status to strings
    # --------------------------------------------------------

    ride_id_string = str(ride.id)

    status_string = str(ride.status)

    passenger_id_string = str(
        ride.passenger_id
    )

    # --------------------------------------------------------
    # WebSocket notification
    # --------------------------------------------------------

    transaction.on_commit(
        lambda: send_ride_status_update(
            ride_id_string,
            status_string,
        )
    )

    # --------------------------------------------------------
    # DRIVER ARRIVING notification
    # --------------------------------------------------------

    if new_status == RideStatus.DRIVER_ARRIVING:

        transaction.on_commit(
            lambda: create_notification.delay(
                user_id=passenger_id_string,
                notification_type="DRIVER_ARRIVING",
                title="Driver Arriving",
                message="Your driver is arriving.",
                ride_id=ride_id_string,
            )
        )

    # --------------------------------------------------------
    # RIDE STARTED notification
    # --------------------------------------------------------

    elif new_status == RideStatus.STARTED:

        transaction.on_commit(
            lambda: create_notification.delay(
                user_id=passenger_id_string,
                notification_type="RIDE_STARTED",
                title="Ride Started",
                message="Your ride has started.",
                ride_id=ride_id_string,
            )
        )

    # --------------------------------------------------------
    # RIDE COMPLETED notification
    # --------------------------------------------------------

    elif new_status == RideStatus.COMPLETED:

        transaction.on_commit(
            lambda: create_notification.delay(
                user_id=passenger_id_string,
                notification_type="RIDE_COMPLETED",
                title="Ride Completed",
                message=(
                    "Your ride has been completed "
                    "successfully."
                ),
                ride_id=ride_id_string,
            )
        )

    logger.info(
        "Ride status update and notification tasks registered "
        "| ride_id=%s | status=%s",
        ride.id,
        ride.status,
    )

    # IMPORTANT:
    # Return the updated ride.
    return ride


# ============================================================
# ACCEPT RIDE
# ============================================================

@transaction.atomic
def accept_ride(ride_id, driver):
    """
    Safely accept a ride.

    Business rules:

    1. Lock the ride row.
    2. Ride must be REQUESTED.
    3. Passenger cannot also be the driver.
    4. Driver must be ONLINE.
    5. Driver cannot have another active ride.
    6. Driver must have an active vehicle.
    7. Assign driver and vehicle.
    8. Change status to ACCEPTED.
    9. Send WebSocket update after commit.
    10. Notify passenger after commit.
    """

    logger.info(
        "Accept ride requested | ride_id=%s | driver_id=%s",
        ride_id,
        driver.id,
    )

    # --------------------------------------------------------
    # Lock ride row
    # --------------------------------------------------------

    ride = (
        Ride.objects
        .select_for_update()
        .get(
            pk=ride_id
        )
    )

    logger.info(
        "Ride retrieved for acceptance | ride_id=%s | status=%s",
        ride.id,
        ride.status,
    )

    # --------------------------------------------------------
    # Passenger cannot be the driver
    # --------------------------------------------------------

    if ride.passenger_id == driver.user_id:

        logger.warning(
            "Ride acceptance rejected because passenger "
            "and driver are the same user | ride_id=%s | "
            "driver_id=%s",
            ride.id,
            driver.id,
        )

        raise ValueError(
            "Passenger cannot be the same user as the driver."
        )

    # --------------------------------------------------------
    # Ride must be REQUESTED
    # --------------------------------------------------------

    if ride.status != RideStatus.REQUESTED:

        logger.warning(
            "Ride acceptance rejected due to invalid status "
            "| ride_id=%s | status=%s",
            ride.id,
            ride.status,
        )

        raise ValueError(
            f"Ride cannot be accepted because "
            f"its current status is {ride.status}."
        )

    # --------------------------------------------------------
    # Driver availability
    # --------------------------------------------------------

    if driver.availability_status != "ONLINE":

        logger.warning(
            "Ride acceptance rejected because driver is "
            "not available | ride_id=%s | driver_id=%s",
            ride.id,
            driver.id,
        )

        raise ValueError(
            "Driver is not available."
        )

    # --------------------------------------------------------
    # Driver cannot have another active ride
    # --------------------------------------------------------

    active_ride = (
        Ride.objects
        .filter(
            driver=driver,
            status__in=ACTIVE_RIDE_STATUSES,
        )
        .exclude(
            pk=ride.pk,
        )
        .exists()
    )

    if active_ride:

        logger.warning(
            "Ride acceptance rejected because driver "
            "already has an active ride | ride_id=%s | "
            "driver_id=%s",
            ride.id,
            driver.id,
        )

        raise ValueError(
            "Driver already has an active ride."
        )

    # --------------------------------------------------------
    # Get active vehicle
    # --------------------------------------------------------

    vehicle = (
        Vehicle.objects
        .filter(
            driver=driver,
            is_active=True,
        )
        .select_related(
            "vehicle_type",
        )
        .first()
    )

    if not vehicle:

        logger.warning(
            "Ride acceptance rejected because driver "
            "has no active vehicle | ride_id=%s | "
            "driver_id=%s",
            ride.id,
            driver.id,
        )

        raise ValueError(
            "Driver does not have an active vehicle."
        )

    # --------------------------------------------------------
    # Assign driver
    # --------------------------------------------------------

    ride.driver = driver

    # --------------------------------------------------------
    # Assign vehicle
    # --------------------------------------------------------

    ride.vehicle = vehicle

    # --------------------------------------------------------
    # Change status
    # --------------------------------------------------------

    ride.status = RideStatus.ACCEPTED

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    ride.save(
        update_fields=[
            "driver",
            "vehicle",
            "status",
            "updated_at",
        ],
    )

    logger.info(
        "Ride accepted successfully | ride_id=%s | "
        "driver_id=%s | status=%s",
        ride.id,
        driver.id,
        ride.status,
    )

    # --------------------------------------------------------
    # IDs for background tasks
    # --------------------------------------------------------

    ride_id_string = str(ride.id)

    status_string = str(ride.status)

    passenger_id_string = str(
        ride.passenger_id
    )

    # --------------------------------------------------------
    # WebSocket update
    # --------------------------------------------------------

    transaction.on_commit(
        lambda: send_ride_status_update(
            ride_id_string,
            status_string,
        )
    )

    # --------------------------------------------------------
    # Notify passenger
    # --------------------------------------------------------

    transaction.on_commit(
        lambda: create_notification.delay(
            user_id=passenger_id_string,
            notification_type="RIDE_ACCEPTED",
            title="Ride Accepted",
            message=(
                "Your ride has been accepted "
                "by a driver."
            ),
            ride_id=ride_id_string,
        )
    )

    logger.info(
        "Ride acceptance notifications registered "
        "| ride_id=%s | driver_id=%s",
        ride.id,
        driver.id,
    )

    return ride


# ============================================================
# CANCEL RIDE
# ============================================================

@transaction.atomic
def cancel_ride(ride, user):
    """
    Cancel a ride.

    Business rules:

    1. Only passenger can cancel.
    2. Ride can only be cancelled while REQUESTED.
    3. Ride can only be cancelled while ACCEPTED.
    4. Change status to CANCELLED.
    5. Send WebSocket update after commit.
    6. Notify assigned driver after commit.
    """

    logger.info(
        "Ride cancellation requested | ride_id=%s | "
        "user_id=%s | current_status=%s",
        ride.id,
        user.id,
        ride.status,
    )

    # --------------------------------------------------------
    # Check passenger ownership
    # --------------------------------------------------------

    if ride.passenger_id != user.id:

        logger.warning(
            "Ride cancellation rejected due to ownership "
            "mismatch | ride_id=%s | user_id=%s",
            ride.id,
            user.id,
        )

        raise PermissionError(
            "Only the passenger can cancel this ride."
        )

    # --------------------------------------------------------
    # Check status
    # --------------------------------------------------------

    if ride.status not in [
        RideStatus.REQUESTED,
        RideStatus.ACCEPTED,
    ]:

        logger.warning(
            "Ride cancellation rejected due to invalid "
            "status | ride_id=%s | status=%s",
            ride.id,
            ride.status,
        )

        raise ValueError(
            f"Ride cannot be cancelled because "
            f"its current status is {ride.status}."
        )

    # --------------------------------------------------------
    # Change status
    # --------------------------------------------------------

    ride.status = RideStatus.CANCELLED

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    ride.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    logger.info(
        "Ride cancelled successfully | ride_id=%s | status=%s",
        ride.id,
        ride.status,
    )

    # --------------------------------------------------------
    # Convert IDs to strings
    # --------------------------------------------------------

    ride_id_string = str(ride.id)

    status_string = str(ride.status)

    # --------------------------------------------------------
    # WebSocket update
    # --------------------------------------------------------

    transaction.on_commit(
        lambda: send_ride_status_update(
            ride_id_string,
            status_string,
        )
    )

    # --------------------------------------------------------
    # Notify assigned driver
    # --------------------------------------------------------

    if ride.driver:

        driver_user_id_string = str(
            ride.driver.user_id
        )

        transaction.on_commit(
            lambda: create_notification.delay(
                user_id=driver_user_id_string,
                notification_type="RIDE_CANCELLED",
                title="Ride Cancelled",
                message=(
                    "The passenger cancelled "
                    "the ride."
                ),
                ride_id=ride_id_string,
            )
        )

    logger.info(
        "Ride cancellation notifications registered "
        "| ride_id=%s",
        ride.id,
    )

    return ride