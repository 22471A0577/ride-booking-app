from django.db import transaction

from business.models import (
    DriverProfile,
    Ride,
    RideStatus,
    Vehicle,
)


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


ACTIVE_RIDE_STATUSES = [
    RideStatus.REQUESTED,
    RideStatus.ACCEPTED,
    RideStatus.DRIVER_ARRIVING,
    RideStatus.STARTED,
]


def change_ride_status(ride, new_status):
    """
    Change ride status only when the transition is allowed.
    """

    current_status = ride.status

    allowed_statuses = ALLOWED_TRANSITIONS.get(
        current_status,
        []
    )

    if new_status not in allowed_statuses:
        raise ValueError(
            f"Cannot change ride status "
            f"from {current_status} to {new_status}."
        )

    ride.status = new_status

    ride.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return ride


@transaction.atomic
def accept_ride(ride_id, driver):
    """
    Safely accept a ride.

    transaction.atomic() ensures all database operations
    succeed or fail together.

    select_for_update() locks the ride row so that two
    drivers cannot accept the same ride simultaneously.
    """

    # Lock the ride row
    ride = (
    Ride.objects
    .select_for_update()
    .get(pk=ride_id)
)

    # Ride must still be available
    if ride.status != RideStatus.REQUESTED:
        raise ValueError(
            f"Ride cannot be accepted because "
            f"its current status is {ride.status}."
        )

    # Driver must be available
    if not driver.is_available:
        raise ValueError(
            "Driver is not available."
        )

    # Driver cannot have another active ride
    active_ride = Ride.objects.filter(
        driver=driver,
        status__in=ACTIVE_RIDE_STATUSES,
    ).exclude(
        pk=ride.pk
    ).exists()

    if active_ride:
        raise ValueError(
            "Driver already has an active ride."
        )

    # Get driver's active vehicle
    vehicle = Vehicle.objects.filter(
        driver=driver,
        is_active=True,
    ).first()

    if not vehicle:
        raise ValueError(
            "Driver does not have an active vehicle."
        )

    # Assign driver and vehicle
    ride.driver = driver
    ride.vehicle = vehicle

    # Change status
    ride.status = RideStatus.ACCEPTED

    ride.save(
        update_fields=[
            "driver",
            "vehicle",
            "status",
            "updated_at",
        ]
    )

    return ride


@transaction.atomic
def cancel_ride(ride, user):
    """
    Cancel a ride.

    Only the passenger can cancel.
    Cancellation is allowed only from REQUESTED or ACCEPTED.
    """

    if ride.passenger != user:
        raise PermissionError(
            "Only the passenger can cancel this ride."
        )

    if ride.status not in [
        RideStatus.REQUESTED,
        RideStatus.ACCEPTED,
    ]:
        raise ValueError(
            f"Ride cannot be cancelled because "
            f"its current status is {ride.status}."
        )

    ride.status = RideStatus.CANCELLED

    ride.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return ride