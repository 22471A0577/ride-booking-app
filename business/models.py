import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


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

    is_available = models.BooleanField(
        default=True
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


class RideStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Requested"
    ACCEPTED = "ACCEPTED", "Accepted"
    DRIVER_ARRIVING = "DRIVER_ARRIVING", "Driver Arriving"
    STARTED = "STARTED", "Started"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"

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
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return self.address


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
            models.Index(fields=["passenger"]),
            models.Index(fields=["driver"]),
            models.Index(fields=["vehicle"]),
            models.Index(fields=["status"]),
            models.Index(fields=["requested_at"]),
        ]

    def __str__(self):
        return f"Ride {self.id} - {self.status}"

   