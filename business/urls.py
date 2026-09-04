from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from .throttles import LoginRateThrottle, RideCreationRateThrottle

from .views import (
    # ========================================================
    # DRIVER
    # ========================================================

    DriverListCreateAPIView,
    DriverDetailAPIView,

    # ========================================================
    # VEHICLE
    # ========================================================

    VehicleListCreateAPIView,
    VehicleDetailAPIView,

    # ========================================================
    # RIDE
    # ========================================================

    RideListCreateAPIView,
    RideDetailAPIView,
    RideHistoryAPIView,
    RideAcceptAPIView,
    RideStatusUpdateAPIView,
    RideCancelAPIView,

    # ========================================================
    # FARE
    # ========================================================

    FareCalculationAPIView,

    # ========================================================
    # RIDE QUERY
    # ========================================================

    ActiveRidesAPIView,
    CompletedRidesAPIView,
    CancelledRidesAPIView,

    DriverRideHistoryAPIView,
    DailyRideCountAPIView,
    TotalCompletedRidesAPIView,
    DriverEarningsAPIView,
    RideStatisticsAPIView,
    RideFilterAPIView,

    # ========================================================
    # DRIVER LOCATION
    # ========================================================

    DriverLocationAPIView,
    NearbyDriverAPIView,

    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    NotificationListAPIView,
    NotificationReadAPIView,
    NotificationReadAllAPIView,
)


urlpatterns = [

    # ========================================================
    # AUTH APIs
    # ========================================================
    path(
    "login/",
    TokenObtainPairView.as_view(
        throttle_classes=[LoginRateThrottle]
    ),
    name="token-obtain-pair",
),

    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),


    # ========================================================
    # DRIVER APIs
    # ========================================================

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


    # ========================================================
    # VEHICLE APIs
    # ========================================================

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


    # ========================================================
    # RIDE APIs
    # ========================================================

    path(
        "rides/",
        RideListCreateAPIView.as_view(),
        name="ride-list-create",
    ),

    # IMPORTANT:
    # Keep /history/ before /<uuid:pk>/
    path(
        "rides/history/",
        RideHistoryAPIView.as_view(),
        name="ride-history",
    ),

    path(
        "rides/<uuid:pk>/",
        RideDetailAPIView.as_view(),
        name="ride-detail",
    ),

    path(
        "rides/<uuid:pk>/status/",
        RideStatusUpdateAPIView.as_view(),
        name="ride-status-update",
    ),

    path(
        "rides/<uuid:pk>/accept/",
        RideAcceptAPIView.as_view(),
        name="ride-accept",
    ),

    path(
        "rides/<uuid:pk>/cancel/",
        RideCancelAPIView.as_view(),
        name="ride-cancel",
    ),


    # ========================================================
    # FARE API
    # ========================================================

    path(
        "fare/calculate/",
        FareCalculationAPIView.as_view(),
        name="fare-calculate",
    ),


    # ========================================================
    # RIDE QUERY APIs
    # ========================================================

    path(
        "rides/active/",
        ActiveRidesAPIView.as_view(),
        name="active-rides",
    ),

    path(
        "rides/completed/",
        CompletedRidesAPIView.as_view(),
        name="completed-rides",
    ),

    path(
        "rides/cancelled/",
        CancelledRidesAPIView.as_view(),
        name="cancelled-rides",
    ),

    path(
        "drivers/rides/",
        DriverRideHistoryAPIView.as_view(),
        name="driver-ride-history",
    ),

    path(
        "rides/daily-count/",
        DailyRideCountAPIView.as_view(),
        name="daily-ride-count",
    ),

    path(
        "rides/completed-count/",
        TotalCompletedRidesAPIView.as_view(),
        name="total-completed-rides",
    ),

    path(
        "drivers/earnings/",
        DriverEarningsAPIView.as_view(),
        name="driver-earnings",
    ),

    path(
        "rides/statistics/",
        RideStatisticsAPIView.as_view(),
        name="ride-statistics",
    ),

    path(
        "rides/filter/",
        RideFilterAPIView.as_view(),
        name="ride-filter",
    ),


    # ========================================================
    # DRIVER LOCATION APIs
    # ========================================================

    path(
        "drivers/location/",
        DriverLocationAPIView.as_view(),
        name="driver-location",
    ),

    path(
        "drivers/nearby/",
        NearbyDriverAPIView.as_view(),
        name="nearby-drivers",
    ),


    # ========================================================
    # NOTIFICATION APIs
    # ========================================================

    path(
        "notifications/",
        NotificationListAPIView.as_view(),
        name="notification-list",
    ),

    path(
        "notifications/<uuid:pk>/read/",
        NotificationReadAPIView.as_view(),
        name="notification-read",
    ),

    path(
        "notifications/read-all/",
        NotificationReadAllAPIView.as_view(),
        name="notification-read-all",
    ),
    path(
    "api/schema/",
    SpectacularAPIView.as_view(),
    name="schema",
),

path(
    "api/docs/",
    SpectacularSwaggerView.as_view(url_name="schema"),
    name="swagger-ui",
),

path(
    "api/redoc/",
    SpectacularRedocView.as_view(url_name="schema"),
    name="redoc",
),
    
]
