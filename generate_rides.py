import os
import django
import random
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django.setup()

from django.contrib.auth import get_user_model
from business.models import (
    Ride,
    RideStatus,
    DriverProfile,
    VehicleType,
    Vehicle,
    Location,
)

User = get_user_model()

users = list(User.objects.all())
drivers = list(DriverProfile.objects.all())
vehicle_types = list(VehicleType.objects.all())

print("Users:", len(users))
print("Drivers:", len(drivers))
print("Vehicle Types:", len(vehicle_types))

if not users:
    print("No users found.")
    exit()

if not vehicle_types:
    print("No vehicle types found.")
    exit()

rides = []

statuses = [
    RideStatus.REQUESTED,
    RideStatus.ACCEPTED,
    RideStatus.DRIVER_ARRIVING,
    RideStatus.STARTED,
    RideStatus.COMPLETED,
    RideStatus.CANCELLED,
]

fare_values = [
    Decimal("100.00"),
    Decimal("150.00"),
    Decimal("200.00"),
    Decimal("250.00"),
    Decimal("300.00"),
    Decimal("400.00"),
    Decimal("500.00"),
]

for i in range(5000):

    passenger = random.choice(users)
    ride_type = random.choice(vehicle_types)
    status = random.choice(statuses)

    pickup = Location.objects.create(
        address=f"Pickup Location {i}",
        latitude=Decimal(str(round(random.uniform(15.0, 16.0), 6))),
        longitude=Decimal(str(round(random.uniform(79.0, 80.0), 6))),
    )

    drop = Location.objects.create(
        address=f"Drop Location {i}",
        latitude=Decimal(str(round(random.uniform(15.0, 16.0), 6))),
        longitude=Decimal(str(round(random.uniform(79.0, 80.0), 6))),
    )

    driver = random.choice(drivers) if drivers else None

    vehicle = None

    if driver:
        vehicle = (
            Vehicle.objects
            .filter(driver=driver)
            .order_by("?")
            .first()
        )

    ride = Ride(
        passenger=passenger,
        driver=driver,
        vehicle=vehicle,
        ride_type=ride_type,
        pickup_location=pickup,
        drop_location=drop,
        status=status,
        fare=random.choice(fare_values),
    )

    rides.append(ride)

Ride.objects.bulk_create(
    rides,
    batch_size=500
)

print("Successfully created:", len(rides), "rides")
print("Total rides now:", Ride.objects.count())