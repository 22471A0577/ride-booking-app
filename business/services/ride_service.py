from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from business.tasks import create_notification
from business.models import Ride, RideStatus, Vehicle


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
        print("❌ Channel layer is not configured")
        return

    group_name = f"ride_{ride_id}"

    print("\n========================================")
    print("=== SENDING RIDE STATUS UPDATE ===")
    print("========================================")
    print("Group:", group_name)
    print("Status:", status_value)

    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "ride_status_update",
                "status": str(status_value),
                "message": (
                    f"Ride status changed to {status_value}"
                ),
            },
        )

        print("=== RIDE STATUS UPDATE SENT ===")

    except Exception as e:
        print("❌ WEBSOCKET STATUS UPDATE ERROR")
        print("Error type:", type(e).__name__)
        print("Error:", str(e))


# ============================================================
# CHANGE RIDE STATUS
# ============================================================

@transaction.atomic
def change_ride_status(ride, new_status):
    """
    Safely change ride status.

    Performs:

    1. Status transition validation
    2. Database update
    3. WebSocket notification after commit
    4. Background notification after commit
    """

    print("\n========================================")
    print("=== CHANGE RIDE STATUS START ===")
    print("========================================")

    current_status = ride.status

    print("Ride ID:", ride.id)
    print("Current Status:", current_status)
    print("New Status:", new_status)
# ========================================================
# PASSENGER OWNERSHIP
# ========================================================

    if request.user.role == "USER":

        if ride.passenger_id != request.user.id:

            return Response(
            {
                "success": False,
                "message": (
                    "You are not the passenger "
                    "of this ride."
                ),
                "data": None,
            },
            status=status.HTTP_403_FORBIDDEN,
        )    

    # --------------------------------------------------------
    # Validate transition
    # --------------------------------------------------------

    allowed_statuses = ALLOWED_TRANSITIONS.get(
        current_status,
        [],
    )

    if new_status not in allowed_statuses:
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

    print("=== RIDE STATUS UPDATED IN DATABASE ===")
    print("Ride ID:", ride.id)
    print("Status:", ride.status)

    ride_id_string = str(ride.id)
    status_string = str(ride.status)
    passenger_id_string = str(ride.passenger_id)

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
    # Background notifications
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

    elif new_status == RideStatus.COMPLETED:

        transaction.on_commit(
            lambda: create_notification.delay(
                user_id=passenger_id_string,
                notification_type="RIDE_COMPLETED",
                title="Ride Completed",
                message="Your ride has been completed successfully.",
                ride_id=ride_id_string,
            )
        )

    print("=== WEBSOCKET UPDATE REGISTERED ===")
    print("=== NOTIFICATION TASK REGISTERED ===")

    return ride


# ============================================================
# ACCEPT RIDE
# ============================================================

@transaction.atomic
def accept_ride(ride_id, driver):
    """
    Safely accept a ride.

    Prevents two drivers from accepting
    the same ride simultaneously.
    """

    print("\n========================================")
    print("=== ACCEPT RIDE START ===")
    print("========================================")

    print("Ride ID:", ride_id)
    print("Driver:", driver)

    # --------------------------------------------------------
    # Lock ride row
    # --------------------------------------------------------

    ride = (
        Ride.objects
        .select_for_update()
        .get(pk=ride_id)
    )

    print("Current ride status:", ride.status)
# --------------------------------------------------------
# Passenger cannot be the driver
# --------------------------------------------------------

    if ride.passenger_id == driver.user_id:
      raise ValueError(
        "Passenger cannot be the same user as the driver."
    )

    # --------------------------------------------------------
    # Ride must be REQUESTED
    # --------------------------------------------------------

    if ride.status != RideStatus.REQUESTED:
        raise ValueError(
            f"Ride cannot be accepted because "
            f"its current status is {ride.status}."
        )

    # --------------------------------------------------------
    # Driver availability
    # --------------------------------------------------------

    if driver.availability_status != "ONLINE":
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
        .first()
    )

    if not vehicle:
        raise ValueError(
            "Driver does not have an active vehicle."
        )

    # --------------------------------------------------------
    # Assign driver and vehicle
    # --------------------------------------------------------

    ride.driver = driver
    ride.vehicle = vehicle
    ride.status = RideStatus.ACCEPTED

    ride.save(
        update_fields=[
            "driver",
            "vehicle",
            "status",
            "updated_at",
        ],
    )

    print("=== RIDE ACCEPTED IN DATABASE ===")
    print("Ride ID:", ride.id)
    print("Driver ID:", driver.id)
    print("Status:", ride.status)
    print("Vehicle:", vehicle)

    ride_id_string = str(ride.id)
    status_string = str(ride.status)
    passenger_id_string = str(ride.passenger_id)

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
            message="Your ride has been accepted by a driver.",
            ride_id=ride_id_string,
        )
    )

    print("=== WEBSOCKET UPDATE REGISTERED ===")
    print("=== NOTIFICATION TASK REGISTERED ===")

    return ride


# ============================================================
# CANCEL RIDE
# ============================================================

@transaction.atomic
def cancel_ride(ride, user):
    """
    Cancel a ride.

    Current business rule:
        Only passenger can cancel.

    Allowed:
        REQUESTED
        ACCEPTED
    """

    print("\n========================================")
    print("=== CANCEL RIDE START ===")
    print("========================================")

    print("Ride ID:", ride.id)
    print("Passenger:", ride.passenger)
    print("User:", user)
    print("Current Status:", ride.status)

    # --------------------------------------------------------
    # Check passenger
    # --------------------------------------------------------

    if ride.passenger != user:
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
        raise ValueError(
            f"Ride cannot be cancelled because "
            f"its current status is {ride.status}."
        )

    # --------------------------------------------------------
    # Change status
    # --------------------------------------------------------

    ride.status = RideStatus.CANCELLED

    ride.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    print("=== RIDE CANCELLED IN DATABASE ===")
    print("Ride ID:", ride.id)
    print("Status:", ride.status)

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
    # Notify driver if one is assigned
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
                message="The passenger cancelled the ride.",
                ride_id=ride_id_string,
            )
        )

    print("=== WEBSOCKET UPDATE REGISTERED ===")
    print("=== NOTIFICATION TASK REGISTERED ===")

    return ride
