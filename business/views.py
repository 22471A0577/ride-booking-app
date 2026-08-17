from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from .services.fare_service import calculate_fare
from .services.ride_service import (
    accept_ride,
    change_ride_status,
)

from .models import (
    DriverProfile,
    Vehicle,
    Ride,
    RideStatus,
)

from .serializers import (
    DriverProfileSerializer,
    VehicleSerializer,
    RideSerializer,
    FareCalculationSerializer,
)

from .permissions import (
    IsAdmin,
    IsAdminOrReadOnly,
    IsAdminOrDriver,
)


class DriverListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = DriverProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

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
        "is_available",
    ]

    ordering = ["-created_at"]

    def get_queryset(self):
        return DriverProfile.objects.select_related(
            "user"
        ).prefetch_related(
            "vehicles__vehicle_type"
        ).all()


class DriverDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = DriverProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    lookup_field = "pk"

    def get_queryset(self):
        return DriverProfile.objects.select_related(
            "user"
        ).prefetch_related(
            "vehicles__vehicle_type"
        ).all()


class VehicleListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = VehicleSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]

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

    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Vehicle.objects.select_related(
            "driver__user",
            "vehicle_type",
        )

        user = self.request.user

        if user.role == "ADMIN":
            return queryset

        if user.role == "DRIVER":
            return queryset.filter(
                driver__user=user
            )

        # Normal users can VIEW active vehicles.
        return queryset.filter(
            is_active=True
        )

class VehicleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VehicleSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]

        return [
            IsAuthenticated(),
            IsAdminOrDriver(),
        ]

    lookup_field = "pk"

    def get_queryset(self):
        queryset = Vehicle.objects.select_related(
            "driver__user",
            "vehicle_type",
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
class RideListCreateAPIView(generics.ListCreateAPIView):

    serializer_class = RideSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Ride.objects.select_related(
            "passenger",
            "driver__user",
            "vehicle",
            "ride_type",
            "pickup_location",
            "drop_location",
        ).order_by("-requested_at")

        user = self.request.user

        # Admin can see every ride
        if user.role == "ADMIN":
            return queryset

        # Passenger sees only their own rides
        if user.role == "USER":
            return queryset.filter(
                passenger=user
            )

        # Driver sees rides assigned to them
        if user.role == "DRIVER":
            return queryset.filter(
                driver__user=user
            )

        return queryset.none()

    def perform_create(self, serializer):
        serializer.save(
            passenger=self.request.user
        )

class RideDetailAPIView(generics.RetrieveAPIView):
    queryset = Ride.objects.select_related(
        "passenger",
        "driver__user",
        "vehicle",
        "ride_type",
        "pickup_location",
        "drop_location",
    )

    serializer_class = RideSerializer
    permission_classes = [IsAuthenticated]
from rest_framework.response import Response
from rest_framework import status
class RideStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            ride = Ride.objects.select_related(
                "passenger",
                "driver__user",
                "vehicle",
                "ride_type",
                "pickup_location",
                "drop_location",
            ).get(pk=pk)

        except Ride.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Ride not found.",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {
                    "success": False,
                    "message": "Status is required.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only the assigned driver can move the ride forward.
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
                        "message": "Only drivers can update this ride status.",
                        "data": None,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if not ride.driver:
                return Response(
                    {
                        "success": False,
                        "message": "Ride has not been assigned to a driver.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if ride.driver.user_id != request.user.id:
                return Response(
                    {
                        "success": False,
                        "message": "You are not the driver assigned to this ride.",
                        "data": None,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Pass the actual business rule to the service layer.
        from .services.ride_service import change_ride_status

        try:
            ride = change_ride_status(
                ride_id=ride.id,
                new_status=new_status,
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
                "message": f"Ride status changed to {new_status}.",
                "data": RideSerializer(ride).data,
            },
            status=status.HTTP_200_OK,
        )
    
class RideAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        # Only drivers can accept rides
        if request.user.role != "DRIVER":
            return Response(
                {"detail": "Only drivers can accept rides."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get driver's profile
        try:
            driver = request.user.driver_profile
        except DriverProfile.DoesNotExist:
            return Response(
                {"detail": "Driver profile not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            ride = accept_ride(
                ride_id=pk,
                driver=driver
            )

        except Ride.DoesNotExist:
            return Response(
                {"detail": "Ride not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            RideSerializer(ride).data,
            status=status.HTTP_200_OK
        )
class RideCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            ride = Ride.objects.get(pk=pk)
        except Ride.DoesNotExist:
            return Response(
                {"detail": "Ride not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only passenger can cancel the ride
        if ride.passenger != request.user:
            return Response(
                {"detail": "Only the passenger can cancel this ride."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Cancellation allowed only for REQUESTED or ACCEPTED rides
        if ride.status not in [
            RideStatus.REQUESTED,
            RideStatus.ACCEPTED,
        ]:
            return Response(
                {
                    "detail": (
                        f"Ride cannot be cancelled because "
                        f"its current status is {ride.status}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        ride.status = RideStatus.CANCELLED
        ride.save(update_fields=["status", "updated_at"])

        return Response(
            RideSerializer(ride).data,
            status=status.HTTP_200_OK
        )
class FareCalculationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FareCalculationSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Invalid fare calculation data.",
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        from .services.fare_service import calculate_fare

        fare = calculate_fare(
            base_fare=serializer.validated_data["base_fare"],
            distance_km=serializer.validated_data["distance_km"],
            time_minutes=serializer.validated_data["time_minutes"],
            surge_multiplier=serializer.validated_data.get(
                "surge_multiplier",
                1.00
            ),
        )

        return Response(
            {
                "success": True,
                "message": "Fare calculated successfully.",
                "data": fare,
            },
            status=status.HTTP_200_OK
        )  
      