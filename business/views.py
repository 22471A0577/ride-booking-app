from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import (
    DriverProfile,
    Vehicle,
    Ride,
    RideStatus,
    DriverLocation,
    Notification,
)

from .serializers import (
    DriverProfileSerializer,
    VehicleSerializer,
    RideSerializer,
    FareCalculationSerializer,
    DriverLocationSerializer,
    NearbyDriverSerializer,
    NotificationSerializer,
    RideStatisticsSerializer,
    DriverEarningsSerializer,
)

from .permissions import (
    IsAdminOrReadOnly,
    IsAdminOrDriver,
)

from .services.fare_service import calculate_fare

from .services.ride_service import (
    accept_ride,
    change_ride_status,
    cancel_ride,
)

from .services.driver_location_service import (
    get_nearby_drivers,
)

from .services.ride_query_service import (
    filter_rides,
    get_active_rides_for_user,
    get_completed_rides_for_user,
    get_cancelled_rides_for_user,
    get_ride_history_for_user,
    get_driver_ride_history,
    get_daily_ride_count,
    get_total_completed_rides,
    get_total_driver_earnings,
    get_ride_statistics,
)


# ============================================================
# DRIVER APIs
# ============================================================

class DriverListCreateAPIView(generics.ListCreateAPIView):

    serializer_class = DriverProfileSerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminOrReadOnly,
    ]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "user__email",
        "license_number",
        "phone_number",
    ]

    ordering_fields = [
        "created_at",
        "updated_at",
        "license_number",
        "availability_status",
    ]

    ordering = [
        "-created_at"
    ]

    def get_queryset(self):

        return (
            DriverProfile.objects
            .select_related("user")
            .prefetch_related(
                "vehicles__vehicle_type"
            )
            .all()
        )


# ============================================================
# DRIVER DETAIL
# ============================================================

class DriverDetailAPIView(
    generics.RetrieveUpdateAPIView
):

    serializer_class = DriverProfileSerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminOrReadOnly,
    ]

    lookup_field = "pk"

    def get_queryset(self):

        return (
            DriverProfile.objects
            .select_related("user")
            .prefetch_related(
                "vehicles__vehicle_type"
            )
            .all()
        )


# ============================================================
# VEHICLE APIs
# ============================================================

class VehicleListCreateAPIView(
    generics.ListCreateAPIView
):

    serializer_class = VehicleSerializer

    def get_permissions(self):

        if self.request.method == "GET":

            return [
                IsAuthenticated()
            ]

        return [
            IsAuthenticated(),
            IsAdminOrDriver(),
        ]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "vehicle_number",
        "model_name",
        "color",
        "driver__user__email",
    ]

    ordering_fields = [
        "created_at",
        "updated_at",
        "vehicle_number",
        "is_active",
    ]

    ordering = [
        "-created_at"
    ]

    def get_queryset(self):

        queryset = (
            Vehicle.objects
            .select_related(
                "driver__user",
                "vehicle_type",
            )
        )

        user = self.request.user

        if user.role == "ADMIN":
            return queryset

        if user.role == "DRIVER":
            return queryset.filter(
                driver__user=user
            )

        return queryset.filter(
            is_active=True
        )


# ============================================================
# VEHICLE DETAIL
# ============================================================

class VehicleDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = VehicleSerializer

    def get_permissions(self):

        if self.request.method == "GET":

            return [
                IsAuthenticated()
            ]

        return [
            IsAuthenticated(),
            IsAdminOrDriver(),
        ]

    lookup_field = "pk"

    def get_queryset(self):

        queryset = (
            Vehicle.objects
            .select_related(
                "driver__user",
                "vehicle_type",
            )
        )

        user = self.request.user

        if user.role == "ADMIN":
            return queryset

        if user.role == "DRIVER":

            return queryset.filter(
                driver__user=user
            )

        return queryset.filter(
            is_active=True
        )


# ============================================================
# RIDE LIST / CREATE
# ============================================================

class RideListCreateAPIView(
    generics.ListCreateAPIView
):

    serializer_class = RideSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        queryset = (
            Ride.objects
            .select_related(
                "passenger",
                "driver__user",
                "vehicle",
                "ride_type",
                "pickup_location",
                "drop_location",
            )
            .order_by("-requested_at")
        )

        user = self.request.user

        if user.role == "ADMIN":

            return queryset

        if user.role == "USER":

            return queryset.filter(
                passenger=user
            )

        if user.role == "DRIVER":

            return queryset.filter(
                driver__user=user
            )

        return queryset.none()

    def perform_create(self, serializer):

        serializer.save(
            passenger=self.request.user
        )


# ============================================================
# RIDE DETAIL
# ============================================================

class RideDetailAPIView(
    generics.RetrieveAPIView
):

    serializer_class = RideSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        queryset = (
            Ride.objects
            .select_related(
                "passenger",
                "driver__user",
                "vehicle",
                "ride_type",
                "pickup_location",
                "drop_location",
            )
        )

        user = self.request.user

        if user.role == "ADMIN":

            return queryset

        if user.role == "USER":

            return queryset.filter(
                passenger=user
            )

        if user.role == "DRIVER":

            return queryset.filter(
                driver__user=user
            )

        return queryset.none()


# ============================================================
# RIDE HISTORY
# ============================================================

class RideHistoryAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        rides = get_ride_history_for_user(
            request.user
        )

        paginator = RidePagination()

        page = paginator.paginate_queryset(
            rides,
            request,
            view=self,
        )

        serializer = RideSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )


# ============================================================
# RIDE STATUS UPDATE
# ============================================================

class RideStatusUpdateAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def patch(self, request, pk):

        try:

            ride = (
                Ride.objects
                .select_related(
                    "passenger",
                    "driver__user",
                    "vehicle",
                    "ride_type",
                    "pickup_location",
                    "drop_location",
                )
                .get(pk=pk)
            )

        except Ride.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Ride not found.",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get(
            "status"
        )

        if not new_status:

            return Response(
                {
                    "success": False,
                    "message": "Status is required.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        driver_statuses = [
            RideStatus.DRIVER_ARRIVING,
            RideStatus.STARTED,
            RideStatus.COMPLETED,
        ]

        if new_status in driver_statuses:

            if request.user.role != "DRIVER":

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Only drivers can update "
                            "this ride status."
                        ),
                        "data": None,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if not ride.driver:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "Ride has not been assigned "
                            "to a driver."
                        ),
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if ride.driver.user_id != request.user.id:

                return Response(
                    {
                        "success": False,
                        "message": (
                            "You are not the driver "
                            "assigned to this ride."
                        ),
                        "data": None,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:

            ride = change_ride_status(
                ride=ride,
                new_status=new_status,
            )

        except ValueError as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": (
                    f"Ride status changed to {new_status}."
                ),
                "data": RideSerializer(
                    ride
                ).data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# RIDE ACCEPT
# ============================================================

class RideAcceptAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request, pk):

        if request.user.role != "DRIVER":

            return Response(
                {
                    "success": False,
                    "message": (
                        "Only drivers can accept rides."
                    ),
                    "data": None,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:

            driver = request.user.driver_profile

        except DriverProfile.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Driver profile not found.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            ride = accept_ride(
                ride_id=pk,
                driver=driver,
            )

        except Ride.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Ride not found.",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": (
                    "Ride accepted successfully."
                ),
                "data": RideSerializer(
                    ride
                ).data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# RIDE CANCEL
# ============================================================

class RideCancelAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request, pk):

        try:

            ride = (
                Ride.objects
                .select_related(
                    "passenger",
                    "driver__user",
                    "vehicle",
                    "ride_type",
                    "pickup_location",
                    "drop_location",
                )
                .get(pk=pk)
            )

        except Ride.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Ride not found.",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:

            ride = cancel_ride(
                ride=ride,
                user=request.user,
            )

        except PermissionError as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        except ValueError as e:

            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": (
                    "Ride cancelled successfully."
                ),
                "data": RideSerializer(
                    ride
                ).data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# FARE CALCULATION
# ============================================================

class FareCalculationAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        serializer = FareCalculationSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": (
                        "Invalid fare calculation data."
                    ),
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        fare = calculate_fare(
            base_fare=serializer.validated_data[
                "base_fare"
            ],
            distance_km=serializer.validated_data[
                "distance_km"
            ],
            time_minutes=serializer.validated_data[
                "time_minutes"
            ],
            surge_multiplier=serializer.validated_data.get(
                "surge_multiplier",
                1.00,
            ),
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Fare calculated successfully."
                ),
                "data": fare,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# RIDE PAGINATION
# ============================================================

class RidePagination(
    PageNumberPagination
):

    page_size = 20

    page_size_query_param = "page_size"

    max_page_size = 100


# ============================================================
# SERIALIZE RIDE LIST
# ============================================================

def serialize_ride_list(rides):

    return RideSerializer(
        rides,
        many=True,
    ).data


# ============================================================
# ACTIVE RIDES
# ============================================================

class ActiveRidesAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        rides = get_active_rides_for_user(
            request.user
        )

        paginator = RidePagination()

        page = paginator.paginate_queryset(
            rides,
            request,
            view=self,
        )

        serializer = RideSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )


# ============================================================
# COMPLETED RIDES
# ============================================================

class CompletedRidesAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        rides = get_completed_rides_for_user(
            request.user
        )

        paginator = RidePagination()

        page = paginator.paginate_queryset(
            rides,
            request,
            view=self,
        )

        serializer = RideSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )


# ============================================================
# CANCELLED RIDES
# ============================================================

class CancelledRidesAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        rides = get_cancelled_rides_for_user(
            request.user
        )

        paginator = RidePagination()

        page = paginator.paginate_queryset(
            rides,
            request,
            view=self,
        )

        serializer = RideSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )


# ============================================================
# DAILY RIDE COUNT
# ============================================================

class DailyRideCountAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        count = get_daily_ride_count(
            request.user
        )

        return Response(
            {
                "success": True,
                "daily_ride_count": count,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# TOTAL COMPLETED RIDES
# ============================================================

class TotalCompletedRidesAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        count = get_total_completed_rides(
            request.user
        )

        return Response(
            {
                "success": True,
                "total_completed_rides": count,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# DRIVER RIDE HISTORY
# ============================================================

class DriverRideHistoryAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        rides = get_driver_ride_history(
            request.user
        )

        paginator = RidePagination()

        page = paginator.paginate_queryset(
            rides,
            request,
            view=self,
        )

        serializer = RideSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )


# ============================================================
# DRIVER EARNINGS
# ============================================================

class DriverEarningsAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        if request.user.role != "DRIVER":

            return Response(
                {
                    "success": False,
                    "message": (
                        "Only drivers can view "
                        "driver earnings."
                    ),
                    "data": None,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        earnings = get_total_driver_earnings(
            request.user
        )

        serializer = DriverEarningsSerializer(
            {
                "total_earnings": earnings
            }
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Driver earnings retrieved "
                    "successfully."
                ),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# RIDE STATISTICS
# ============================================================

class RideStatisticsAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        statistics = get_ride_statistics(
            request.user
        )

        serializer = RideStatisticsSerializer(
            statistics
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Ride statistics retrieved "
                    "successfully."
                ),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# RIDE FILTER + PAGINATION
# ============================================================

class RideFilterAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        rides = filter_rides(
            user=request.user,

            status=request.query_params.get(
                "status"
            ),

            driver_id=request.query_params.get(
                "driver_id"
            ),

            start_date=request.query_params.get(
                "start_date"
            ),

            end_date=request.query_params.get(
                "end_date"
            ),

            min_fare=request.query_params.get(
                "min_fare"
            ),

            max_fare=request.query_params.get(
                "max_fare"
            ),

            search=request.query_params.get(
                "search"
            ),

            ordering=request.query_params.get(
                "ordering",
                "-requested_at",
            ),
        )

        paginator = RidePagination()

        page = paginator.paginate_queryset(
            rides,
            request,
            view=self,
        )

        serializer = RideSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )


# ============================================================
# DRIVER LOCATION
# ============================================================

class DriverLocationAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):

        if request.user.role != "DRIVER":

            return Response(
                {
                    "success": False,
                    "message": (
                        "Only drivers can update "
                        "their location."
                    ),
                    "data": None,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:

            driver = request.user.driver_profile

        except DriverProfile.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Driver profile not found."
                    ),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DriverLocationSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": (
                        "Invalid location data."
                    ),
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        latitude = serializer.validated_data[
            "latitude"
        ]

        longitude = serializer.validated_data[
            "longitude"
        ]

        location, created = (
            DriverLocation.objects
            .update_or_create(
                driver=driver,
                defaults={
                    "latitude": latitude,
                    "longitude": longitude,
                },
            )
        )

        # ====================================================
        # ACTIVE RIDE
        # ====================================================

        active_ride = (
            Ride.objects
            .filter(
                driver=driver,
                status__in=[
                    RideStatus.ACCEPTED,
                    RideStatus.DRIVER_ARRIVING,
                    RideStatus.STARTED,
                ],
            )
            .first()
        )

        # ====================================================
        # WEBSOCKET LOCATION UPDATE
        # ====================================================

        if active_ride:

            channel_layer = get_channel_layer()

            if channel_layer:

                async_to_sync(
                    channel_layer.group_send
                )(
                    f"ride_{active_ride.id}",
                    {
                        "type": (
                            "driver_location_update"
                        ),
                        "driver_id": str(
                            driver.id
                        ),
                        "latitude": float(
                            latitude
                        ),
                        "longitude": float(
                            longitude
                        ),
                    },
                )

        return Response(
            {
                "success": True,
                "message": (
                    "Driver location created."
                    if created
                    else
                    "Driver location updated."
                ),
                "data": {
                    "driver_id": str(
                        driver.id
                    ),
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "last_updated": (
                        location.last_updated
                    ),
                },
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


# ============================================================
# NEARBY DRIVERS
# ============================================================

class NearbyDriverAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        latitude = request.query_params.get(
            "latitude"
        )

        longitude = request.query_params.get(
            "longitude"
        )

        radius = request.query_params.get(
            "radius"
        )

        # ====================================================
        # REQUIRED PARAMETERS
        # ====================================================

        if (
            latitude is None
            or longitude is None
            or radius is None
        ):

            return Response(
                {
                    "success": False,
                    "message": (
                        "latitude, longitude and "
                        "radius are required."
                    ),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====================================================
        # CONVERT VALUES
        # ====================================================

        try:

            latitude = float(latitude)

            longitude = float(longitude)

            radius = float(radius)

        except (
            TypeError,
            ValueError,
        ):

            return Response(
                {
                    "success": False,
                    "message": (
                        "latitude, longitude and "
                        "radius must be valid numbers."
                    ),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====================================================
        # LATITUDE VALIDATION
        # ====================================================

        if not -90 <= latitude <= 90:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Invalid latitude. "
                        "Must be between -90 and 90."
                    ),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====================================================
        # LONGITUDE VALIDATION
        # ====================================================

        if not -180 <= longitude <= 180:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Invalid longitude. "
                        "Must be between -180 and 180."
                    ),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====================================================
        # RADIUS VALIDATION
        # ====================================================

        if radius <= 0:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Radius must be greater than 0."
                    ),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ====================================================
        # NEARBY DRIVERS
        # ====================================================

        nearby_drivers = get_nearby_drivers(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius,
        )

        serializer = NearbyDriverSerializer(
            nearby_drivers,
            many=True,
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Nearby drivers retrieved "
                    "successfully."
                ),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# NOTIFICATION PAGINATION
# ============================================================

class NotificationPagination(
    PageNumberPagination
):

    page_size = 20

    page_size_query_param = "page_size"

    max_page_size = 100


# ============================================================
# NOTIFICATION LIST
# ============================================================

class NotificationListAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        notifications = (
            Notification.objects
            .filter(
                user=request.user
            )
            .select_related("ride")
            .order_by("-created_at")
        )

        paginator = NotificationPagination()

        page = paginator.paginate_queryset(
            notifications,
            request,
            view=self,
        )

        serializer = NotificationSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )


# ============================================================
# NOTIFICATION READ
# ============================================================

class NotificationReadAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def patch(self, request, pk):

        try:

            notification = (
                Notification.objects
                .get(
                    pk=pk,
                    user=request.user,
                )
            )

        except Notification.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Notification not found."
                    ),
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.is_read = True

        notification.save(
            update_fields=[
                "is_read"
            ]
        )

        serializer = NotificationSerializer(
            notification
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Notification marked as read."
                ),
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# NOTIFICATION READ ALL
# ============================================================

class NotificationReadAllAPIView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def patch(self, request):

        updated_count = (
            Notification.objects
            .filter(
                user=request.user,
                is_read=False,
            )
            .update(
                is_read=True
            )
        )

        return Response(
            {
                "success": True,
                "message": (
                    "All notifications marked as read."
                ),
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )
class BadRideListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        rides = Ride.objects.all()[:20]

        data = []

        for ride in rides:

            data.append({
                "id": str(ride.id),
                "passenger": ride.passenger.email,
                "driver": (
                    ride.driver.user.email
                    if ride.driver
                    else None
                ),
                "vehicle": (
                    ride.vehicle.vehicle_number
                    if ride.vehicle
                    else None
                ),
                "ride_type": ride.ride_type.name,
                "pickup": ride.pickup_location.address,
                "drop": ride.drop_location.address,
            })

        return Response(data)    