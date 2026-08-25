from unittest.mock import patch

from django.test import TestCase

from business.tasks import create_notification


class CeleryRetryTests(TestCase):

    @patch(
        "business.tasks.Notification.objects.filter"
    )
    def test_notification_task_retries_on_failure(
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