from django.test import TestCase
from unittest.mock import patch

from business.models import User, Notification
from business.tasks import create_notification, retry_test_task


class CeleryRetryTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="celery@test.com",
            password="Test@12345",
            role="USER",
        )

    def test_notification_task_executes_successfully(self):
        result = create_notification(
            self.user.id,
            "Test Notification",
            "Celery task executed successfully.",
            "SYSTEM",
        )

        self.assertTrue(result["success"])
        self.assertIn("notification_id", result)
        self.assertIn("event_key", result)

        self.assertEqual(
            Notification.objects.count(),
            1,
        )

        print("\n=== CELERY TASK EXECUTION TEST ===")
        print("Task executed successfully")
        print("Notification created:", result["notification_id"])

    def test_duplicate_notification_is_prevented(self):
        first_result = create_notification(
            self.user.id,
            "Test Notification",
            "First notification.",
            "SYSTEM",
        )

        second_result = create_notification(
            self.user.id,
            "Test Notification",
            "Duplicate notification.",
            "SYSTEM",
        )

        self.assertTrue(first_result["success"])
        self.assertTrue(second_result["success"])

        self.assertEqual(
            second_result["message"],
            "Duplicate notification prevented.",
        )

        self.assertEqual(
            Notification.objects.count(),
            1,
        )

        print("\n=== CELERY DUPLICATE PREVENTION TEST ===")
        print("Duplicate notification prevented successfully")

    def test_retry_task_succeeds_after_retries(self):
        result = retry_test_task.apply(
            args=[]
        ).get()

        self.assertTrue(result["success"])
        self.assertEqual(result["attempt"], 3)

        print("\n=== CELERY RETRY EXECUTION TEST ===")
        print("Retry task succeeded")
        print("Successful attempt:", result["attempt"])

    @patch(
        "business.tasks.Notification.objects.filter"
    )
    def test_notification_task_retry_configuration(
        self,
        mock_filter,
    ):
        mock_filter.side_effect = Exception(
            "Simulated Redis/Database failure"
        )

        task = create_notification

        self.assertTrue(
            task.autoretry_for
        )

        self.assertIn(
            Exception,
            task.autoretry_for
        )

        self.assertTrue(
            task.retry_backoff
        )

        self.assertEqual(
            task.max_retries,
            3,
        )

        print("\n========================================")
        print("=== CELERY RETRY CONFIGURATION TEST ===")
        print("========================================")
        print(
            "autoretry_for:",
            task.autoretry_for,
        )
        print(
            "retry_backoff:",
            task.retry_backoff,
        )
        print(
            "max_retries:",
            task.max_retries,
        )
        print("========================================")