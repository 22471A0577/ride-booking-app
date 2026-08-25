import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


# ============================================================
# USER
# ============================================================

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "ADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(
            email=email,
            password=password,
            **extra_fields
        )


class User(AbstractUser):

    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("DRIVER", "Driver"),
        ("USER", "User"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    email = models.EmailField(
        unique=True
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="USER"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    username = None

    objects = UserManager()

    def __str__(self):
        return self.email


# ============================================================
# SERVICE AREA
# ============================================================

class ServiceArea(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        max_length=100,
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "service_areas"

    def __str__(self):
        return self.name


# ============================================================
# DRIVER PROFILE
# ============================================================

class DriverProfile(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="driver_profile"
    )

    license_number = models.CharField(
        max_length=50,
        unique=True
    )

    service_areas = models.ManyToManyField(
        ServiceArea,
        related_name="drivers",
        blank=True
    )

    phone_number = models.CharField(
        max_length=15,
        unique=True
    )
    class AvailabilityStatus(models.TextChoices):
        ONLINE = "ONLINE", "Online"
        OFFLINE = "OFFLINE", "Offline"
        BUSY = "BUSY", "Busy"

    availability_status = models.CharField(
        max_length=10,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.OFFLINE,
        db_index=True    
    )

    

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "driver_profiles"

    def __str__(self):
        return self.user.email

    #DRIVER LOCATION MODEL


# ============================================================
# DRIVER LOCATION
# ============================================================

class DriverLocation(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    driver = models.OneToOneField(
        DriverProfile,
        on_delete=models.CASCADE,
        related_name="location"
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    last_updated = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "driver_locations"

        indexes = [
    models.Index(
        fields=["latitude", "longitude"],
        name="driver_loc_coords_idx",
    ),
    models.Index(
        fields=["driver"],
        name="driver_loc_driver_idx",
    ),
]

    def __str__(self):
        return (
            f"{self.driver.user.email} - "
            f"{self.latitude}, {self.longitude}"
        )
# ============================================================
# VEHICLE TYPE
# ============================================================

class VehicleType(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        max_length=50,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "vehicle_types"

    def __str__(self):
        return self.name


# ============================================================
# VEHICLE
# ============================================================

class Vehicle(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.CASCADE,
        related_name="vehicles"
    )

    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.PROTECT,
        related_name="vehicles"
    )

    vehicle_number = models.CharField(
        max_length=20,
        unique=True
    )

    model_name = models.CharField(
        max_length=100
    )

    color = models.CharField(
        max_length=30
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "vehicles"

        indexes = [
            models.Index(fields=["driver"]),
            models.Index(fields=["vehicle_type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.vehicle_number


# ============================================================
# RIDE STATUS
# ============================================================

class RideStatus(models.TextChoices):

    REQUESTED = "REQUESTED", "Requested"
    ACCEPTED = "ACCEPTED", "Accepted"
    DRIVER_ARRIVING = "DRIVER_ARRIVING", "Driver Arriving"
    STARTED = "STARTED", "Started"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


# ============================================================
# LOCATION
# ============================================================

class Location(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    address = models.CharField(
        max_length=255
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "locations"

        indexes = [
            models.Index(
                fields=["latitude", "longitude"]
            ),
        ]

    def __str__(self):
        return self.address


# ============================================================
# RIDE
# ============================================================

class Ride(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    passenger = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="rides"
    )

    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rides"
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rides"
    )

    ride_type = models.ForeignKey(
        VehicleType,
        on_delete=models.PROTECT,
        related_name="rides"
    )

    pickup_location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="pickup_rides"
    )

    drop_location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="drop_rides"
    )

    status = models.CharField(
        max_length=20,
        choices=RideStatus.choices,
        default=RideStatus.REQUESTED
    )

    fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    requested_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "rides"

        indexes = [

            # Individual indexes
            models.Index(
                fields=["passenger"],
                name="ride_passenger_idx",
            ),

            models.Index(
                fields=["driver"],
                name="ride_driver_idx",
            ),

            models.Index(
                fields=["vehicle"],
                name="ride_vehicle_idx",
            ),

            models.Index(
                fields=["status"],
                name="ride_status_idx",
            ),

            models.Index(
                fields=["requested_at"],
                name="ride_requested_at_idx",
            ),

            models.Index(
                fields=["updated_at"],
                name="ride_updated_at_idx",
            ),

            # Composite indexes

            models.Index(
                fields=[
                    "passenger",
                    "status",
                    "-requested_at",
                ],
                name="ride_pass_status_date_idx",
            ),

            models.Index(
                fields=[
                    "driver",
                    "status",
                    "-requested_at",
                ],
                name="ride_driver_status_date_idx",
            ),

            models.Index(
                fields=[
                    "status",
                    "-requested_at",
                ],
                name="ride_status_date_idx",
            ),

            models.Index(
                fields=[
                    "passenger",
                    "-requested_at",
                ],
                name="ride_passenger_date_idx",
            ),

            models.Index(
                fields=[
                    "driver",
                    "-requested_at",
                ],
                name="ride_driver_date_idx",
            ),

            models.Index(
                fields=[
                    "fare",
                ],
                name="ride_fare_idx",
            ),
        ]

    def __str__(self):
        return f"Ride {self.id} - {self.status}"

# ============================================================
# NOTIFICATION
# ============================================================

class Notification(models.Model):

    NOTIFICATION_TYPES = (
        ("RIDE_REQUEST", "Ride Request"),
        ("RIDE_ACCEPTED", "Ride Accepted"),
        ("DRIVER_ARRIVING", "Driver Arriving"),
        ("RIDE_STARTED", "Ride Started"),
        ("RIDE_COMPLETED", "Ride Completed"),
        ("RIDE_CANCELLED", "Ride Cancelled"),
        ("DRIVER_LOCATION", "Driver Location"),
        ("SYSTEM", "System"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    ride = models.ForeignKey(
        Ride,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
    )

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False,
        db_index=True,
    )

    event_key = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["user", "is_read"]
            ),
            models.Index(
                fields=["user", "created_at"]
            ),
            models.Index(
                fields=["notification_type"]
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "ride",
                    "notification_type",
                ],
                name="unique_user_ride_notification",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"