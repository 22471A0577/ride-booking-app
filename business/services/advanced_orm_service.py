from django.db.models import Q, F, Count, Sum, Avg, Max, Min

from business.models import Ride, RideStatus


# ============================================================
# ADVANCED DJANGO ORM EXAMPLES
# ============================================================

def orm_filter_example():
    """
    filter()

    Returns completed rides.
    """

    return Ride.objects.filter(
        status=RideStatus.COMPLETED
    )


def orm_exclude_example():
    """
    exclude()

    Returns rides that are NOT cancelled.
    """

    return Ride.objects.exclude(
        status=RideStatus.CANCELLED
    )


def orm_q_example():
    """
    Q()

    Find rides that are either completed
    OR cancelled.
    """

    return Ride.objects.filter(
        Q(status=RideStatus.COMPLETED)
        | Q(status=RideStatus.CANCELLED)
    )


def orm_f_example():
    """
    F()

    Compare two database fields.

    Example:
    Find rides where fare is greater than 100.
    """

    return Ride.objects.filter(
        fare__gt=F("fare") - 0
    ).filter(
        fare__gt=100
    )


def orm_annotate_example():
    """
    annotate()

    Add calculated information to every ride.

    Example:
    Count notifications associated with the ride.
    """

    return Ride.objects.annotate(
        notification_count=Count("notifications")
    )


def orm_aggregate_example():
    """
    aggregate()

    Calculate statistics across the entire queryset.
    """

    return Ride.objects.aggregate(
        total_rides=Count("id"),
        total_earnings=Sum("fare"),
        average_fare=Avg("fare"),
        maximum_fare=Max("fare"),
        minimum_fare=Min("fare"),
    )


def orm_values_example():
    """
    values()

    Return dictionaries instead of complete Ride objects.
    """

    return Ride.objects.values(
        "id",
        "status",
        "fare",
        "requested_at",
    )


def orm_values_list_example():
    """
    values_list()

    Return only selected fields as tuples.
    """

    return Ride.objects.values_list(
        "id",
        "status",
        "fare",
    )


def orm_exists_example():
    """
    exists()

    Efficiently check whether at least one
    completed ride exists.
    """

    return Ride.objects.filter(
        status=RideStatus.COMPLETED
    ).exists()


def orm_distinct_example():
    """
    distinct()

    Return unique driver IDs that have rides.
    """

    return (
        Ride.objects
        .filter(driver__isnull=False)
        .values("driver_id")
        .distinct()
    )