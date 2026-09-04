import logging

from celery import shared_task
from django.db import IntegrityError

from .models import Notification


logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def create_notification(
    self,
    user_id,
    title,
    message,
    notification_type,
    ride_id=None,
):
    """
    Create notification asynchronously.

    Duplicate notifications are prevented using event_key.
    """

    # Build a unique event identifier
    if ride_id is not None:
        event_key = (
            f"{user_id}:{ride_id}:{notification_type}"
        )
    else:
        event_key = (
            f"{user_id}:{notification_type}:{title}"
        )

    logger.info(
        "Notification task started | "
        "user_id=%s | notification_type=%s | ride_id=%s",
        user_id,
        notification_type,
        ride_id,
    )

    # --------------------------------------------------
    # DUPLICATE PREVENTION
    # --------------------------------------------------

    if Notification.objects.filter(
        event_key=event_key
    ).exists():

        logger.warning(
            "Duplicate notification prevented | "
            "user_id=%s | notification_type=%s | ride_id=%s",
            user_id,
            notification_type,
            ride_id,
        )

        return {
            "success": True,
            "message": "Duplicate notification prevented.",
            "event_key": event_key,
        }

    # --------------------------------------------------
    # CREATE NOTIFICATION
    # --------------------------------------------------

    try:

        notification = Notification.objects.create(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            ride_id=ride_id,
            event_key=event_key,
        )

    except IntegrityError:

        # Another worker may have created the same
        # notification at almost the same time.

        logger.warning(
            "Notification creation conflict; "
            "duplicate prevented | "
            "user_id=%s | notification_type=%s | ride_id=%s",
            user_id,
            notification_type,
            ride_id,
        )

        return {
            "success": True,
            "message": "Duplicate notification prevented.",
            "event_key": event_key,
        }

    # --------------------------------------------------
    # SUCCESS
    # --------------------------------------------------

    logger.info(
        "Notification created successfully | "
        "notification_id=%s | user_id=%s | "
        "notification_type=%s | ride_id=%s",
        notification.id,
        user_id,
        notification_type,
        ride_id,
    )

    return {
        "success": True,
        "notification_id": str(notification.id),
        "event_key": event_key,
    }


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def retry_test_task(self):
    attempt = self.request.retries + 1

    logger.info(
        "Celery retry test task started | attempt=%s",
        attempt,
    )

    if self.request.retries < 2:

        logger.warning(
            "Celery retry test task intentionally failing | "
            "attempt=%s",
            attempt,
        )

        raise Exception(
            "Intentional failure for retry testing"
        )

    logger.info(
        "Celery retry test task succeeded | attempt=%s",
        attempt,
    )

    return {
        "success": True,
        "attempt": attempt,
    }

