from business.models import Notification


def create_notification(
    user,
    notification_type,
    title,
    message,
    ride=None,
):
    if not user:
        return None

    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        ride=ride,
    )


def notify_ride_requested(ride):
    """
    Notify the assigned driver when a ride is requested.
    """
    if not ride.driver:
        return None

    return create_notification(
        user=ride.driver.user,
        notification_type="RIDE_REQUESTED",
        title="New Ride Request",
        message="You have received a new ride request.",
        ride=ride,
    )


def notify_ride_accepted(ride):
    """
    Notify passenger when driver accepts.
    """
    return create_notification(
        user=ride.passenger,
        notification_type="RIDE_ACCEPTED",
        title="Ride Accepted",
        message="Your ride has been accepted by the driver.",
        ride=ride,
    )


def notify_driver_arriving(ride):
    """
    Notify passenger when driver is arriving.
    """
    return create_notification(
        user=ride.passenger,
        notification_type="DRIVER_ARRIVING",
        title="Driver Arriving",
        message="Your driver is on the way.",
        ride=ride,
    )


def notify_ride_started(ride):
    """
    Notify passenger when ride starts.
    """
    return create_notification(
        user=ride.passenger,
        notification_type="RIDE_STARTED",
        title="Ride Started",
        message="Your ride has started.",
        ride=ride,
    )


def notify_ride_completed(ride):
    """
    Notify passenger when ride is completed.
    """
    return create_notification(
        user=ride.passenger,
        notification_type="RIDE_COMPLETED",
        title="Ride Completed",
        message="Your ride has been completed successfully.",
        ride=ride,
    )


def notify_ride_cancelled(ride, cancelled_by=None):
    """
    Notify the other party when a ride is cancelled.
    """

    if cancelled_by == ride.passenger:

        if ride.driver:
            return create_notification(
                user=ride.driver.user,
                notification_type="RIDE_CANCELLED",
                title="Ride Cancelled",
                message="The passenger cancelled the ride.",
                ride=ride,
            )

        return None

    if ride.driver and cancelled_by == ride.driver.user:

        return create_notification(
            user=ride.passenger,
            notification_type="RIDE_CANCELLED",
            title="Ride Cancelled",
            message="The driver cancelled the ride.",
            ride=ride,
        )

    return create_notification(
        user=ride.passenger,
        notification_type="RIDE_CANCELLED",
        title="Ride Cancelled",
        message="Your ride has been cancelled.",
        ride=ride,
    )