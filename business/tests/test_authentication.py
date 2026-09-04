from datetime import timedelta

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from business.models import User


class AuthenticationTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="auth@test.com",
            password="Test@12345",
            role="USER",
        )

    # ========================================================
    # TEST 1
    # VALID LOGIN
    # ========================================================

    def test_valid_login(self):

        response = self.client.post(
            "/api/v1/login/",
            {
                "email": "auth@test.com",
                "password": "Test@12345",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "refresh",
            response.data,
        )

    # ========================================================
    # TEST 2
    # INVALID PASSWORD
    # ========================================================

    def test_invalid_credentials_rejected(self):

        response = self.client.post(
            "/api/v1/login/",
            {
                "email": "auth@test.com",
                "password": "WrongPassword",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # ========================================================
    # TEST 3
    # NON-EXISTENT USER
    # ========================================================

    def test_nonexistent_user_rejected(self):

        response = self.client.post(
            "/api/v1/login/",
            {
                "email": "doesnotexist@test.com",
                "password": "Test@12345",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # ========================================================
    # TEST 4
    # TOKEN REFRESH
    # ========================================================

    def test_token_refresh(self):

        response = self.client.post(
            "/api/v1/login/",
            {
                "email": "auth@test.com",
                "password": "Test@12345",
            },
            format="json",
        )

        refresh_token = response.data["refresh"]

        refresh_response = self.client.post(
            "/api/v1/token/refresh/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            refresh_response.data,
        )

        self.assertIn(
            "refresh",
            refresh_response.data,
        )

    # ========================================================
    # TEST 5
    # INVALID REFRESH TOKEN
    # ========================================================

    def test_invalid_refresh_token_rejected(self):

        response = self.client.post(
            "/api/v1/token/refresh/",
            {
                "refresh": "invalid-refresh-token",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # ========================================================
    # TEST 6
    # EXPIRED ACCESS TOKEN
    # ========================================================

    def test_expired_access_token_rejected(self):

        token = AccessToken.for_user(self.user)

        token.set_exp(
            lifetime=timedelta(seconds=-1)
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(token)}"
        )

        response = self.client.get(
            "/api/v1/notifications/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )