from rest_framework import serializers

from .models import (
    Notification,
    DriverProfile,
    VehicleType,
    Vehicle,
    Location,
    Ride,
    RideStatus,
    DriverLocation,
)


# ============================================================
# VEHICLE TYPE SERIALIZER
# ============================================================

class VehicleTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = VehicleType

        fields = [
            "id",
            "name",
            "description",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]


# ============================================================
# VEHICLE SERIALIZER
# ============================================================

class VehicleSerializer(serializers.ModelSerializer):

    driver_name = serializers.EmailField(
        source="driver.user.email",
        read_only=True,
    )

    vehicle_type_name = serializers.CharField(
        source="vehicle_type.name",
        read_only=True,
    )

    class Meta:
        model = Vehicle

        fields = [
            "id",
            "driver",
            "driver_name",
            "vehicle_type",
            "vehicle_type_name",
            "vehicle_number",
            "model_name",
            "color",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "driver_name",
            "vehicle_type_name",
            "created_at",
            "updated_at",
        ]

    def validate_vehicle_number(self, value):

        value = value.strip().upper()

        if not value:
            raise serializers.ValidationError(
                "Vehicle registration number is required."
            )

        queryset = Vehicle.objects.filter(
            vehicle_number__iexact=value
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "Vehicle registration number already exists."
            )

        return value


# ============================================================
# DRIVER PROFILE SERIALIZER
# ============================================================

class DriverProfileSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    name = serializers.SerializerMethodField()

    vehicles = serializers.SerializerMethodField()

    class Meta:
        model = DriverProfile

        fields = [
            "id",
            "email",
            "name",
            "license_number",
            "phone_number",
            "availability_status",
            "vehicles",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "email",
            "name",
            "vehicles",
            "created_at",
            "updated_at",
        ]

    def get_name(self, obj):

        return obj.user.first_name

    def get_vehicles(self, obj):

        return VehicleSerializer(
            obj.vehicles.all(),
            many=True,
        ).data


# ============================================================
# LOCATION SERIALIZER
# ============================================================

class LocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Location

        fields = [
            "id",
            "address",
            "latitude",
            "longitude",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]


# ============================================================
# RIDE SERIALIZER
# ============================================================

class RideSerializer(serializers.ModelSerializer):

    passenger_name = serializers.EmailField(
        source="passenger.email",
        read_only=True,
    )

    driver_name = serializers.EmailField(
        source="driver.user.email",
        read_only=True,
        allow_null=True,
    )

    vehicle_number = serializers.CharField(
        source="vehicle.vehicle_number",
        read_only=True,
        allow_null=True,
    )

    pickup_address = serializers.CharField(
        source="pickup_location.address",
        read_only=True,
    )

    drop_address = serializers.CharField(
        source="drop_location.address",
        read_only=True,
    )

    ride_type_name = serializers.CharField(
        source="ride_type.name",
        read_only=True,
    )

    class Meta:
        model = Ride

        fields = [
            "id",

            "passenger",
            "passenger_name",

            "driver",
            "driver_name",

            "vehicle",
            "vehicle_number",

            "ride_type",
            "ride_type_name",

            "pickup_location",
            "pickup_address",

            "drop_location",
            "drop_address",

            "status",
            "fare",
            "requested_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",

            "passenger",
            "passenger_name",

            "driver",
            "driver_name",

            "vehicle",
            "vehicle_number",

            "ride_type_name",

            "pickup_address",
            "drop_address",

            "status",
            "fare",

            "requested_at",
            "updated_at",
        ]

    def validate(self, attrs):

        request = self.context.get("request")

        passenger = (
            request.user
            if request
            else None
        )

        pickup = attrs.get(
            "pickup_location"
        )

        drop = attrs.get(
            "drop_location"
        )

        ride_type = attrs.get(
            "ride_type"
        )

        # ====================================================
        # PASSENGER VALIDATION
        # ====================================================

        if passenger and passenger.role != "USER":

            raise serializers.ValidationError({
                "passenger":
                    "Only normal users can create rides."
            })

        # ====================================================
        # PICKUP / DROP VALIDATION
        # ====================================================

        if pickup and drop and pickup == drop:

            raise serializers.ValidationError({
                "drop_location":
                    "Pickup and drop locations cannot be the same."
            })

        # ====================================================
        # RIDE TYPE VALIDATION
        # ====================================================

        if not ride_type:

            raise serializers.ValidationError({
                "ride_type":
                    "Ride type is required."
            })

        # ====================================================
        # ACTIVE RIDE VALIDATION
        # ====================================================

        active_statuses = [
            RideStatus.REQUESTED,
            RideStatus.ACCEPTED,
            RideStatus.DRIVER_ARRIVING,
            RideStatus.STARTED,
        ]

        if passenger:

            conflicting_ride = (
                Ride.objects
                .filter(
                    passenger=passenger,
                    status__in=active_statuses,
                )
                .exists()
            )

            if conflicting_ride:

                raise serializers.ValidationError({
                    "passenger":
                        "You already have an active ride."
                })

        return attrs


# ============================================================
# FARE CALCULATION SERIALIZER
# ============================================================

class FareCalculationSerializer(serializers.Serializer):

    base_fare = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    distance_km = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    time_minutes = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    surge_multiplier = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        default=1.00,
    )


# ============================================================
# RIDE STATISTICS SERIALIZER
# ============================================================

class RideStatisticsSerializer(serializers.Serializer):

    total_rides = serializers.IntegerField()

    completed_rides = serializers.IntegerField()

    cancelled_rides = serializers.IntegerField()

    total_earnings = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        allow_null=True,
    )

    average_fare = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        allow_null=True,
    )

    maximum_fare = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        allow_null=True,
    )

    minimum_fare = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        allow_null=True,
    )


# ============================================================
# DRIVER EARNINGS SERIALIZER
# ============================================================

class DriverEarningsSerializer(serializers.Serializer):

    total_earnings = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        allow_null=True,
    )


# ============================================================
# DRIVER LOCATION SERIALIZER
# ============================================================

class DriverLocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = DriverLocation

        fields = [
            "id",
            "driver",
            "latitude",
            "longitude",
            "last_updated",
        ]

        read_only_fields = [
            "id",
            "driver",
            "last_updated",
        ]

    def validate_latitude(self, value):

        if value < -90 or value > 90:

            raise serializers.ValidationError(
                "Latitude must be between -90 and 90."
            )

        return value

    def validate_longitude(self, value):

        if value < -180 or value > 180:

            raise serializers.ValidationError(
                "Longitude must be between -180 and 180."
            )

        return value


# ============================================================
# NOTIFICATION SERIALIZER
# ============================================================

class NotificationSerializer(serializers.ModelSerializer):

    ride_id = serializers.UUIDField(
        source="ride.id",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Notification

        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "ride_id",
            "is_read",
            "created_at",
        ]

        read_only_fields = fields


# ============================================================
# NEARBY DRIVER SERIALIZER
# ============================================================

class NearbyDriverSerializer(serializers.Serializer):

    driver_id = serializers.UUIDField()

    user_id = serializers.UUIDField()

    distance_km = serializers.FloatField()

    latitude = serializers.FloatField()

    longitude = serializers.FloatField()
def validate(self, attrs):

    request = self.context.get("request")

    passenger = request.user if request else None

    pickup = attrs.get("pickup_location")
    drop = attrs.get("drop_location")
    ride_type = attrs.get("ride_type")
    driver = attrs.get("driver")

    # ====================================================
    # PASSENGER VALIDATION
    # ====================================================

    if passenger and passenger.role != "USER":

        raise serializers.ValidationError({
            "passenger":
                "Only normal users can create rides."
        })

    # ====================================================
    # PICKUP / DROP VALIDATION
    # ====================================================

    if pickup and drop and pickup == drop:

        raise serializers.ValidationError({
            "drop_location":
                "Pickup and drop locations cannot be the same."
        })

    # ====================================================
    # RIDE TYPE VALIDATION
    # ====================================================

    if not ride_type:

        raise serializers.ValidationError({
            "ride_type":
                "Ride type is required."
        })

    # ====================================================
    # PASSENGER / DRIVER VALIDATION
    # ====================================================

    if passenger and driver:

        if driver.user_id == passenger.id:

            raise serializers.ValidationError({
                "driver":
                    "Passenger cannot be the same user as the driver."
            })

    # ====================================================
    # ACTIVE RIDE VALIDATION
    # ====================================================

    active_statuses = [
        RideStatus.REQUESTED,
        RideStatus.ACCEPTED,
        RideStatus.DRIVER_ARRIVING,
        RideStatus.STARTED,
    ]

    if passenger:

        conflicting_ride = (
            Ride.objects
            .filter(
                passenger=passenger,
                status__in=active_statuses,
            )
            .exists()
        )

        if conflicting_ride:

            raise serializers.ValidationError({
                "passenger":
                    "You already have an active ride."
            })

    return attrs