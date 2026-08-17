from urllib import request

from rest_framework import serializers

from .models import (
    DriverProfile,
    VehicleType,
    Vehicle,
    Location,
    Ride,
    RideStatus,
    
)


class VehicleTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = VehicleType
        fields = [
            "id",
            "name",
            "description",
            "created_at",
        ]


class DriverProfileSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(
        source="user.email",
        read_only=True
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
            "is_available",
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
            many=True
        ).data


class VehicleSerializer(serializers.ModelSerializer):

    driver_name = serializers.EmailField(
        source="driver.user.email",
        read_only=True
    )

    vehicle_type_name = serializers.CharField(
        source="vehicle_type.name",
        read_only=True
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

    def validate_vehicle_type(self, value):

        if not VehicleType.objects.filter(
            pk=value.pk
        ).exists():

            raise serializers.ValidationError(
                "Invalid vehicle type."
            )

        return value

    def validate_driver(self, value):

        if not DriverProfile.objects.filter(
            pk=value.pk
        ).exists():

            raise serializers.ValidationError(
                "Invalid driver ID."
            )

        return value


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


class RideSerializer(serializers.ModelSerializer):

    passenger_name = serializers.EmailField(
        source="passenger.email",
        read_only=True
    )

    driver_name = serializers.EmailField(
        source="driver.user.email",
        read_only=True
    )

    vehicle_number = serializers.CharField(
        source="vehicle.vehicle_number",
        read_only=True
    )

    pickup_address = serializers.CharField(
        source="pickup_location.address",
        read_only=True
    )

    drop_address = serializers.CharField(
        source="drop_location.address",
        read_only=True
    )

    ride_type_name = serializers.CharField(
        source="ride_type.name",
        read_only=True
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
            "driver_name",
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
        passenger = request.user if request else None

        pickup = attrs.get("pickup_location")
        drop = attrs.get("drop_location")
        ride_type = attrs.get("ride_type")

        # Passenger must be a normal user
        if passenger and passenger.role != "USER":
            raise serializers.ValidationError({
                "passenger": "Only normal users can create rides."
            })

        # Pickup and drop cannot be the same
        if pickup == drop:
            raise serializers.ValidationError({
                "drop_location":
                "Pickup and drop locations cannot be the same."
            })

        # Ride type is required
        if not ride_type:
            raise serializers.ValidationError({
                "ride_type":
                "Ride type is required."
            })

        # Check conflicting active rides
        active_statuses = [
            RideStatus.REQUESTED,
            RideStatus.ACCEPTED,
            RideStatus.STARTED,
        ]

        if passenger:
            conflicting_ride = Ride.objects.filter(
                passenger=passenger,
                status__in=active_statuses
            ).exists()

            if conflicting_ride:
                raise serializers.ValidationError({
                    "passenger":
                    "You already have an active ride."
                })

        return attrs
            

                
        
class FareCalculationSerializer(serializers.Serializer):
    base_fare = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    distance_km = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    time_minutes = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    surge_multiplier = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        default=1.00
    )        
               

    