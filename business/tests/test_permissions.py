from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from business.models import User


class PermissionTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="Test@12345",
            role="ADMIN",
        )

        self.driver = User.objects.create_user(
            email="driver@test.com",
            password="Test@12345",
            role="DRIVER",
        )

        self.passenger = User.objects.create_user(
            email="passenger@test.com",
            password="Test@12345",
            role="USER",
        )

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )

    # ========================================================
    # TEST 1
    # ANONYMOUS USER REJECTED
    # ========================================================

    def test_anonymous_user_cannot_access_rides(self):

        response = self.client.get(
            "/api/v1/rides/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # ========================================================
    # TEST 2
    # PASSENGER CAN ACCESS RIDE API
    # ========================================================

    def test_passenger_can_access_rides(self):

        self.authenticate(self.passenger)

        response = self.client.get(
            "/api/v1/rides/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    # ========================================================
    # TEST 3
    # PASSENGER CANNOT UPDATE DRIVER LOCATION
    # ========================================================

    def test_passenger_cannot_update_driver_location(self):

        self.authenticate(self.passenger)

        response = self.client.post(
            "/api/v1/drivers/location/",
            {
                "latitude": 17.3850,
                "longitude": 78.4867,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # ========================================================
    # TEST 4
    # DRIVER CAN ACCESS DRIVER LOCATION API
    # ========================================================

    def test_driver_can_access_driver_location(self):

        self.authenticate(self.driver)

        response = self.client.post(
            "/api/v1/drivers/location/",
            {
                "latitude": 17.3850,
                "longitude": 78.4867,
            },
            format="json",
        )

        self.assertNotEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # ========================================================
    # TEST 5
    # PASSENGER CANNOT ACCESS DRIVER EARNINGS
    # ========================================================

    def test_passenger_cannot_access_driver_earnings(self):

        self.authenticate(self.passenger)

        response = self.client.get(
            "/api/v1/drivers/earnings/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # ========================================================
    # TEST 6
    # ADMIN CAN ACCESS RIDE LIST
    # ========================================================

    def test_admin_can_access_rides(self):

        self.authenticate(self.admin)

        response = self.client.get(
            "/api/v1/rides/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    # ========================================================
    # TEST 7
    # PASSENGER CANNOT ACCEPT RIDE
    # ========================================================

    def test_passenger_cannot_accept_ride(self):

        self.authenticate(self.passenger)

        response = self.client.post(
            "/api/v1/rides/00000000-0000-0000-0000-000000000000/accept/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )