from django.db.models import Q, F, Count, Avg, Sum
from business.models import Ride, RideStatus


# ============================================================
# 1. filter()
# ============================================================

def example_filter():
    return Ride.objects.filter(
        status=RideStatus.COMPLETED
    )


# ============================================================
# 2. exclude()
# ============================================================

def example_exclude():
    return Ride.objects.exclude(
        status=RideStatus.CANCELLED
    )


# ============================================================
# 3. Q()
# ============================================================

def example_q():
    return Ride.objects.filter(
        Q(status=RideStatus.COMPLETED)
        | Q(status=RideStatus.STARTED)
    )


# ============================================================
# 4. F()
# ============================================================

def example_f():
    return Ride.objects.filter(
        fare__gte=F("fare")
    )


# ============================================================
# 5. annotate()
# ============================================================

def example_annotate():
    return Ride.objects.values(
        "status"
    ).annotate(
        ride_count=Count("id")
    )


# ============================================================
# 6. aggregate()
# ============================================================

def example_aggregate():
    return Ride.objects.aggregate(
        average_fare=Avg("fare"),
        total_fare=Sum("fare"),
    )


# ============================================================
# 7. values()
# ============================================================

def example_values():
    return Ride.objects.values(
        "id",
        "status",
        "fare",
    )


# ============================================================
# 8. values_list()
# ============================================================

def example_values_list():
    return Ride.objects.values_list(
        "id",
        "status",
        "fare",
    )


# ============================================================
# 9. exists()
# ============================================================

def example_exists():
    return Ride.objects.filter(
        status=RideStatus.COMPLETED
    ).exists()


# ============================================================
# 10. distinct()
# ============================================================

def example_distinct():
    return Ride.objects.values(
        "driver_id"
    ).distinct()