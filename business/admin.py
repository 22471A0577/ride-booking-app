from django.contrib import admin

from .models import (
    DriverProfile,
    VehicleType,
    Vehicle,
    Location,
    Ride,
    ServiceArea,
)


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "license_number",
        "phone_number",
        "availability_status",
        "created_at",
    )

    search_fields = (
        "user__email",
        "license_number",
        "phone_number",
    )

    list_filter = (
        "availability_status",
        "created_at",
    )

    ordering = (
        "user__email",
    )

    filter_horizontal = (
        "service_areas",
    )


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "created_at",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle_number",
        "model_name",
        "driver",
        "vehicle_type",
        "color",
        "is_active",
    )

    search_fields = (
        "vehicle_number",
        "model_name",
        "driver__user__email",
    )

    list_filter = (
        "vehicle_type",
        "is_active",
    )

    ordering = (
        "vehicle_number",
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "address",
        "latitude",
        "longitude",
        "created_at",
    )

    search_fields = (
        "address",
    )

    ordering = (
        "address",
    )


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "passenger",
        "driver",
        "vehicle",
        "status",
        "fare",
        "requested_at",
    )

    search_fields = (
        "passenger__email",
        "driver__user__email",
        "vehicle__vehicle_number",
    )

    list_filter = (
        "status",
        "requested_at",
    )

    ordering = (
        "-requested_at",
    )


@admin.register(ServiceArea)
class ServiceAreaAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "created_at",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )