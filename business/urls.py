from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RideStatusUpdateAPIView
from .views import RideCancelAPIView


from .views import (
    DriverListCreateAPIView,
    DriverDetailAPIView,
    VehicleListCreateAPIView,
    VehicleDetailAPIView,
    RideListCreateAPIView,
    RideDetailAPIView,
    RideAcceptAPIView,
    RideStatusUpdateAPIView,
    RideCancelAPIView,
    FareCalculationAPIView,
)



urlpatterns = [

    # Driver APIs
    path(
        "drivers/",
        DriverListCreateAPIView.as_view(),
        name="driver-list-create",
    ),

    path(
        "drivers/<uuid:pk>/",
        DriverDetailAPIView.as_view(),
        name="driver-detail",
    ),

    # Vehicle APIs
    path(
        "vehicles/",
        VehicleListCreateAPIView.as_view(),
        name="vehicle-list-create",
    ),

    path(
        "vehicles/<uuid:pk>/",
        VehicleDetailAPIView.as_view(),
        name="vehicle-detail",
    ),

    # Ride APIs
    path(
        "rides/",
        RideListCreateAPIView.as_view(),
        name="ride-list-create",
    ),

    path(
        "rides/<uuid:pk>/",
        RideDetailAPIView.as_view(),
        name="ride-detail",
    ),
    path(
    "login/",
    TokenObtainPairView.as_view(),
    name="token-obtain-pair",
),

path(
    "token/refresh/",
    TokenRefreshView.as_view(),
    name="token-refresh",
),
path(
    "rides/<uuid:pk>/status/",
    RideStatusUpdateAPIView.as_view(),
    name="ride-status-update",
),
path(
    "rides/<uuid:pk>/accept/",
    RideAcceptAPIView.as_view(),
),
path(
    "rides/<uuid:pk>/cancel/",
    RideCancelAPIView.as_view(),
    name="ride-cancel",
),
    path(
        "fare/calculate/",
        FareCalculationAPIView.as_view(),
        name="fare-calculate",
    )
    
]