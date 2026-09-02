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
        notification_type="RIDE_REQUEST",
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


# =========================================================
# NOTIFICATION QUERY SERVICES
# =========================================================

def get_user_notifications(user):
    """
    Return only notifications belonging to the authenticated user.
    """

    return (
        Notification.objects
        .filter(user=user)
        .select_related("ride")
        .order_by("-id")
    )


def get_notification_for_user(notification_id, user):
    """
    Return a notification only if it belongs to the authenticated user.

    This prevents IDOR / broken access control.
    """

    return (
        Notification.objects
        .filter(
            id=notification_id,
            user=user,
        )
        .select_related("ride")
        .first()
    )

def mark_notification_as_read(notification_id, user):
    """
    Mark a notification as read only if it belongs
    to the authenticated user.
    """

    if not user or not user.is_authenticated:
        return None

    notification = (
        Notification.objects
        .filter(
            id=notification_id,
            user=user,
        )
        .first()
    )

    if not notification:
        return None

    notification.is_read = True
    notification.save(update_fields=["is_read"])

    return notification
def mark_all_notifications_as_read(user):
    """
    Mark all notifications belonging to the authenticated user as read.

    Notifications belonging to other users are never modified.
    """

    return (
        Notification.objects
        .filter(
            user=user,
            is_read=False,
        )
        .update(is_read=True)
    )
