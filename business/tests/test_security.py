from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

from business.models import (
    User,
    Notification,
)


class SecurityTests(APITestCase):

    def setUp(self):

        self.user1 = User.objects.create_user(
            email="user1@test.com",
            password="Test@12345",
            role="USER",
        )

        self.user2 = User.objects.create_user(
            email="user2@test.com",
            password="Test@12345",
            role="USER",
        )

        self.driver = User.objects.create_user(
            email="driver@test.com",
            password="Test@12345",
            role="DRIVER",
        )

    # ========================================================
    # JWT HELPER
    # ========================================================

    def authenticate(self, user):

        refresh = RefreshToken.for_user(user)

        access_token = str(
            refresh.access_token
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

    # ========================================================
    # TEST 1
    # UNAUTHENTICATED USER
    # ========================================================

    def test_notification_api_requires_authentication(self):

        response = self.client.get(
            "/api/notifications/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # ========================================================
    # TEST 2
    # INVALID JWT
    # ========================================================

    def test_invalid_jwt_rejected(self):

        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer invalid-token"
        )

        response = self.client.get(
            "/api/notifications/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # ========================================================
    # TEST 3
    # USER CAN ACCESS OWN NOTIFICATIONS
    # ========================================================

    def test_user_can_access_own_notifications(self):

        Notification.objects.create(
            user=self.user1,
            notification_type="SYSTEM",
            title="Test Notification",
            message="Hello",
        )

        self.authenticate(self.user1)

        response = self.client.get(
            "/api/notifications/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    # ========================================================
    # TEST 4
    # USER CANNOT SEE OTHER USER NOTIFICATIONS
    # ========================================================

    def test_user_cannot_see_other_users_notifications(self):

        Notification.objects.create(
            user=self.user2,
            notification_type="SYSTEM",
            title="Private Notification",
            message="This belongs to user2",
        )

        self.authenticate(self.user1)

        response = self.client.get(
            "/api/notifications/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        response_text = str(response.data)

        self.assertNotIn(
            "Private Notification",
            response_text,
        )

    # ========================================================
    # TEST 5
    # USER CANNOT MARK OTHER USER'S NOTIFICATION AS READ
    # ========================================================

    def test_user_cannot_mark_other_users_notification_read(self):

        notification = Notification.objects.create(
            user=self.user2,
            notification_type="SYSTEM",
            title="Private Notification",
            message="Private",
        )

        self.authenticate(self.user1)

        response = self.client.patch(
            f"/api/notifications/{notification.id}/read/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        notification.refresh_from_db()

        self.assertFalse(
            notification.is_read
        )

    # ========================================================
    # TEST 6
    # USER CAN MARK OWN NOTIFICATION AS READ
    # ========================================================

    def test_user_can_mark_own_notification_read(self):

        notification = Notification.objects.create(
            user=self.user1,
            notification_type="SYSTEM",
            title="My Notification",
            message="Read this",
        )

        self.authenticate(self.user1)

        response = self.client.patch(
            f"/api/notifications/{notification.id}/read/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read
        )

    # ========================================================
    # TEST 7
    # READ ALL ONLY AFFECTS CURRENT USER
    # ========================================================

    def test_read_all_only_affects_current_user(self):

        own_notification = Notification.objects.create(
            user=self.user1,
            notification_type="SYSTEM",
            title="Own",
            message="Own notification",
        )

        other_notification = Notification.objects.create(
            user=self.user2,
            notification_type="SYSTEM",
            title="Other",
            message="Other notification",
        )

        self.authenticate(self.user1)

        response = self.client.patch(
            "/api/notifications/read-all/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        own_notification.refresh_from_db()
        other_notification.refresh_from_db()

        self.assertTrue(
            own_notification.is_read
        )

        self.assertFalse(
            other_notification.is_read
        )

    # ========================================================
    # TEST 8
    # DRIVER CANNOT ACCESS UNAUTHENTICATED API
    # ========================================================

    def test_driver_with_invalid_token_rejected(self):

        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer invalid-token"
        )

        response = self.client.get(
            "/api/drivers/nearby/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # ========================================================
    # TEST 9
    # MISSING JWT REJECTED
    # ========================================================

    def test_missing_jwt_rejected_for_nearby_drivers(self):

        response = self.client.get(
            "/api/drivers/nearby/",
            {
                "latitude": 17.3850,
                "longitude": 78.4867,
                "radius": 5,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
    # ========================================================
    # TEST 10
    # USER CANNOT ACCESS ANOTHER USER'S RIDE
    # ========================================================

    def test_user_cannot_access_another_users_ride(self):

        from business.models import (
            Ride,
            VehicleType,
            Location,
        )

        vehicle_type = VehicleType.objects.create(
            name="Security Test Car"
        )

        pickup = Location.objects.create(
            address="Location A",
            latitude=17.385000,
            longitude=78.486700,
        )

        drop = Location.objects.create(
            address="Location B",
            latitude=17.400000,
            longitude=78.500000,
        )

        ride = Ride.objects.create(
            passenger=self.user2,
            ride_type=vehicle_type,
            pickup_location=pickup,
            drop_location=drop,
        )

        self.authenticate(self.user1)

        response = self.client.get(
            f"/api/rides/{ride.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


    # ========================================================
    # TEST 11
    # DRIVER CANNOT UPDATE ANOTHER DRIVER'S RIDE
    # ========================================================

    def test_driver_cannot_update_another_drivers_ride(self):

        from business.models import (
            Ride,
            DriverProfile,
            Vehicle,
            VehicleType,
            Location,
        )

        driver_profile_1 = DriverProfile.objects.create(
            user=self.driver,
            license_number="SEC-LICENSE-001",
            phone_number="9000000001",
        )

        driver_user_2 = User.objects.create_user(
            email="driver2@test.com",
            password="Test@12345",
            role="DRIVER",
        )

        driver_profile_2 = DriverProfile.objects.create(
            user=driver_user_2,
            license_number="SEC-LICENSE-002",
            phone_number="9000000002",
        )

        vehicle_type = VehicleType.objects.create(
            name="Security Test Bike"
        )

        vehicle = Vehicle.objects.create(
            driver=driver_profile_2,
            vehicle_type=vehicle_type,
            vehicle_number="SEC-VEH-002",
            model_name="Test Model",
            color="Black",
        )

        pickup = Location.objects.create(
            address="Pickup Location",
            latitude=17.385000,
            longitude=78.486700,
        )

        drop = Location.objects.create(
            address="Drop Location",
            latitude=17.400000,
            longitude=78.500000,
        )

        ride = Ride.objects.create(
            passenger=self.user1,
            driver=driver_profile_2,
            vehicle=vehicle,
            ride_type=vehicle_type,
            pickup_location=pickup,
            drop_location=drop,
        )

        self.authenticate(self.driver)

        response = self.client.patch(
            f"/api/rides/{ride.id}/status/",
            {
                "status": "STARTED",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        ride.refresh_from_db()

        self.assertEqual(
            ride.status,
            "REQUESTED",
        )