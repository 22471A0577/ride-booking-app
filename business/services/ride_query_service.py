from django.db import models
from django.db.models import Avg, Count, Max, Min, Sum
from django.utils import timezone

from business.models import Ride, RideStatus


# ============================================================
# COMMON RIDE QUERYSET
# ============================================================

def base_ride_queryset():
    """
    Common optimized queryset used by ride history
    and other ride queries.
    """

    return (
        Ride.objects
        .select_related(
            "passenger",
            "driver__user",
            "vehicle",
            "ride_type",
            "pickup_location",
            "drop_location",
        )
        .order_by("-requested_at")
    )


# ============================================================
# RIDE HISTORY
# ============================================================

def get_ride_history_for_user(user):
    """
    Get ride history for the logged-in user.

    USER:
        Returns rides where the user is the passenger.

    DRIVER:
        Returns rides assigned to the driver.

    ADMIN:
        Returns all rides.

    History includes:
        - COMPLETED
        - CANCELLED
    """

    queryset = base_ride_queryset().filter(
        status__in=[
            RideStatus.COMPLETED,
            RideStatus.CANCELLED,
        ]
    )

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if user.role == "ADMIN":
        return queryset

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    if user.role == "USER":
        return queryset.filter(
            passenger=user
        )

    # --------------------------------------------------------
    # DRIVER
    # --------------------------------------------------------

    if user.role == "DRIVER":
        return queryset.filter(
            driver__user=user
        )

    # --------------------------------------------------------
    # UNKNOWN ROLE
    # --------------------------------------------------------

    return Ride.objects.none()


# ============================================================
# ACTIVE RIDES
# ============================================================

def get_active_rides_for_user(user):
    """
    Get all active rides belonging to the logged-in user.

    USER:
        Returns rides where passenger = user.

    DRIVER:
        Returns rides assigned to that driver.

    ADMIN:
        Returns all active rides.
    """

    queryset = base_ride_queryset().filter(
        status__in=[
            RideStatus.REQUESTED,
            RideStatus.ACCEPTED,
            RideStatus.DRIVER_ARRIVING,
            RideStatus.STARTED,
        ]
    )

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if user.role == "ADMIN":
        return queryset

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    if user.role == "USER":
        return queryset.filter(
            passenger=user
        )

    # --------------------------------------------------------
    # DRIVER
    # --------------------------------------------------------

    if user.role == "DRIVER":
        return queryset.filter(
            driver__user=user
        )

    return Ride.objects.none()


# ============================================================
# COMPLETED RIDES
# ============================================================

def get_completed_rides_for_user(user):
    """
    Get completed rides for the logged-in user.
    """

    queryset = base_ride_queryset().filter(
        status=RideStatus.COMPLETED
    )

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if user.role == "ADMIN":
        return queryset

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    if user.role == "USER":
        return queryset.filter(
            passenger=user
        )

    # --------------------------------------------------------
    # DRIVER
    # --------------------------------------------------------

    if user.role == "DRIVER":
        return queryset.filter(
            driver__user=user
        )

    return Ride.objects.none()


# ============================================================
# CANCELLED RIDES
# ============================================================

def get_cancelled_rides_for_user(user):
    """
    Get cancelled rides for the logged-in user.
    """

    queryset = base_ride_queryset().filter(
        status=RideStatus.CANCELLED
    )

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if user.role == "ADMIN":
        return queryset

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    if user.role == "USER":
        return queryset.filter(
            passenger=user
        )

    # --------------------------------------------------------
    # DRIVER
    # --------------------------------------------------------

    if user.role == "DRIVER":
        return queryset.filter(
            driver__user=user
        )

    return Ride.objects.none()


# ============================================================
# DRIVER RIDE HISTORY
# ============================================================

def get_driver_ride_history(user):
    """
    Get all rides assigned to the logged-in driver.

    Only DRIVER users can access this query.
    """

    if user.role != "DRIVER":
        return Ride.objects.none()

    return (
        base_ride_queryset()
        .filter(
            driver__user=user
        )
        .order_by("-requested_at")
    )


# ============================================================
# DAILY RIDE COUNT
# ============================================================

def get_daily_ride_count(user):
    """
    Count rides created today.
    """

    today = timezone.localdate()

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    if user.role == "USER":

        return Ride.objects.filter(
            passenger=user,
            requested_at__date=today,
        ).count()

    # --------------------------------------------------------
    # DRIVER
    # --------------------------------------------------------

    if user.role == "DRIVER":

        return Ride.objects.filter(
            driver__user=user,
            requested_at__date=today,
        ).count()

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if user.role == "ADMIN":

        return Ride.objects.filter(
            requested_at__date=today,
        ).count()

    return 0


# ============================================================
# TOTAL COMPLETED RIDES
# ============================================================

def get_total_completed_rides(user):
    """
    Count total completed rides.
    """

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    if user.role == "USER":

        return Ride.objects.filter(
            passenger=user,
            status=RideStatus.COMPLETED,
        ).count()

    # --------------------------------------------------------
    # DRIVER
    # --------------------------------------------------------

    if user.role == "DRIVER":

        return Ride.objects.filter(
            driver__user=user,
            status=RideStatus.COMPLETED,
        ).count()

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if user.role == "ADMIN":

        return Ride.objects.filter(
            status=RideStatus.COMPLETED,
        ).count()

    return 0


# ============================================================
# DRIVER EARNINGS
# ============================================================

def get_total_driver_earnings(user):
    """
    Calculate total earnings from completed rides.
    """

    if user.role != "DRIVER":
        return 0

    result = (
        Ride.objects
        .filter(
            driver__user=user,
            status=RideStatus.COMPLETED,
        )
        .aggregate(
            total_earnings=Sum("fare")
        )
    )

    return result["total_earnings"] or 0


# ============================================================
# RIDE STATISTICS
# ============================================================

def get_ride_statistics(user):
    """
    Return ride statistics for the current user.

    Statistics:
        - total rides
        - completed rides
        - cancelled rides
        - average fare
        - maximum fare
        - minimum fare
    """

    queryset = Ride.objects.all()

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    if user.role == "USER":

        queryset = queryset.filter(
            passenger=user
        )

    # --------------------------------------------------------
    # DRIVER
    # --------------------------------------------------------

    elif user.role == "DRIVER":

        queryset = queryset.filter(
            driver__user=user
        )

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    elif user.role == "ADMIN":

        pass

    # --------------------------------------------------------
    # UNKNOWN ROLE
    # --------------------------------------------------------

    else:

        return {
            "total_rides": 0,
            "completed_rides": 0,
            "cancelled_rides": 0,
            "average_fare": None,
            "maximum_fare": None,
            "minimum_fare": None,
        }

    return queryset.aggregate(
        total_rides=Count("id"),

        completed_rides=Count(
            "id",
            filter=models.Q(
                status=RideStatus.COMPLETED
            ),
        ),

        cancelled_rides=Count(
            "id",
            filter=models.Q(
                status=RideStatus.CANCELLED
            ),
        ),

        average_fare=Avg("fare"),

        maximum_fare=Max("fare"),

        minimum_fare=Min("fare"),
    )


# ============================================================
# BASE RIDE QUERYSET
# ============================================================

def base_filter_queryset():
    return (
        Ride.objects
        .select_related(
            "passenger",
            "driver__user",
            "vehicle",
            "ride_type",
            "pickup_location",
            "drop_location",
        )
        .order_by("-requested_at")
    )


# ============================================================
# FILTER RIDES
# ============================================================

def filter_rides(
    user,
    search=None,
    status=None,
    driver_id=None,
    start_date=None,
    end_date=None,
    min_fare=None,
    max_fare=None,
    ordering="-requested_at",
):
    """
    Advanced ride filtering.

    Supports:

    - Role-based filtering
    - Search
    - Status
    - Driver
    - Start date
    - End date
    - Minimum fare
    - Maximum fare
    - Ordering
    """

    queryset = base_filter_queryset()

    # ========================================================
    # ROLE FILTERING
    # ========================================================

    if user.role == "ADMIN":

        pass

    elif user.role == "USER":

        queryset = queryset.filter(
            passenger=user
        )

    elif user.role == "DRIVER":

        queryset = queryset.filter(
            driver__user=user
        )

    else:

        return Ride.objects.none()

    # ========================================================
    # SEARCH
    # ========================================================

    if search:

        search = search.strip()

        if search:

            queryset = queryset.filter(
                models.Q(
                    passenger__email__icontains=search
                )
                |
                models.Q(
                    driver__user__email__icontains=search
                )
                |
                models.Q(
                    vehicle__vehicle_number__icontains=search
                )
                |
                models.Q(
                    pickup_location__address__icontains=search
                )
                |
                models.Q(
                    drop_location__address__icontains=search
                )
                |
                models.Q(
                    ride_type__name__icontains=search
                )
            )

    # ========================================================
    # STATUS FILTER
    # ========================================================

    if status:

        valid_statuses = [
            choice[0]
            for choice in RideStatus.choices
        ]

        status = status.upper()

        if status not in valid_statuses:

            return Ride.objects.none()

        queryset = queryset.filter(
            status=status
        )

    # ========================================================
    # DRIVER FILTER
    # ========================================================

    if driver_id:

        queryset = queryset.filter(
            driver_id=driver_id
        )

    # ========================================================
    # START DATE
    # ========================================================

    if start_date:

        queryset = queryset.filter(
            requested_at__date__gte=start_date
        )

    # ========================================================
    # END DATE
    # ========================================================

    if end_date:

        queryset = queryset.filter(
            requested_at__date__lte=end_date
        )

    # ========================================================
    # MINIMUM FARE
    # ========================================================

    if min_fare is not None:

        queryset = queryset.filter(
            fare__gte=min_fare
        )

    # ========================================================
    # MAXIMUM FARE
    # ========================================================

    if max_fare is not None:

        queryset = queryset.filter(
            fare__lte=max_fare
        )

    # ========================================================
    # ORDERING
    # ========================================================

    allowed_ordering = {
        "requested_at",
        "-requested_at",

        "fare",
        "-fare",

        "status",
        "-status",

        "updated_at",
        "-updated_at",
    }

    if ordering in allowed_ordering:

        queryset = queryset.order_by(
            ordering
        )

    else:

        queryset = queryset.order_by(
            "-requested_at"
        )

    return queryset