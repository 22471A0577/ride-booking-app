from business.models import (
    DriverProfile,
    Ride,
    RideStatus,
    Vehicle,
)


ACTIVE_RIDE_STATUSES = [
    RideStatus.ACCEPTED,
    RideStatus.DRIVER_ARRIVING,
    RideStatus.STARTED,
]


def get_available_driver_vehicle(driver):
    """
    Validate driver availability and return
    an active vehicle belonging to the driver.
    """

    if driver.availability_status != DriverProfile.AvailabilityStatus.ONLINE:
        raise ValueError(
            "Driver is not available."
        )

    active_ride = Ride.objects.filter(
        driver=driver,
        status__in=ACTIVE_RIDE_STATUSES,
    ).exists()

    if active_ride:
        raise ValueError(
            "Driver already has an active ride."
        )

    vehicle = Vehicle.objects.filter(
        driver=driver,
        is_active=True,
    ).first()

    if not vehicle:
        raise ValueError(
            "Driver does not have an active vehicle."
        )

    return vehicle


def set_driver_availability(driver, is_available):
    """
    Update driver availability.

    A driver cannot become available if the driver
    already has an active ride.
    """

    if is_available:
        active_ride = Ride.objects.filter(
            driver=driver,
            status__in=ACTIVE_RIDE_STATUSES,
        ).exists()

        if active_ride:
            raise ValueError(
                "Driver cannot become available "
                "while having an active ride."
            )

        driver.availability_status = (
            DriverProfile.AvailabilityStatus.ONLINE
        )

    else:
        driver.availability_status = (
            DriverProfile.AvailabilityStatus.OFFLINE
        )

    driver.save(
        update_fields=[
            "availability_status",
            "updated_at",
        ]
    )

    return driver