import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from django.contrib.auth import get_user_model

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


User = get_user_model()

logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(
        self,
        scope,
        receive,
        send
    ):

        logger.info(
            "JWT authentication middleware started"
        )

        # =====================================================
        # GET QUERY STRING
        # =====================================================

        query_string = (
            scope
            .get("query_string", b"")
            .decode()
        )

        # =====================================================
        # PARSE QUERY PARAMETERS
        # =====================================================

        query_params = parse_qs(
            query_string
        )

        # =====================================================
        # GET TOKEN
        # =====================================================

        token_list = query_params.get(
            "token"
        )

        if not token_list:

            logger.warning(
                "WebSocket authentication failed | "
                "reason=jwt_token_missing"
            )

            scope["user"] = None

            return await super().__call__(
                scope,
                receive,
                send
            )

        token = token_list[0]

        # IMPORTANT:
        # Never log the actual JWT token.
        # JWT tokens are credentials.

        logger.info(
            "JWT token received for WebSocket authentication"
        )

        # =====================================================
        # VALIDATE JWT
        # =====================================================

        try:

            user = await self.get_user(
                token
            )

            # ---------------------------------------------
            # User not found / invalid
            # ---------------------------------------------

            if user is None:

                logger.warning(
                    "WebSocket authentication failed | "
                    "reason=user_not_authenticated"
                )

                scope["user"] = None

            # ---------------------------------------------
            # User authenticated
            # ---------------------------------------------

            else:

                logger.info(
                    "WebSocket user authenticated | "
                    "user_id=%s | role=%s",
                    user.id,
                    getattr(
                        user,
                        "role",
                        "UNKNOWN",
                    ),
                )

                scope["user"] = user

        except Exception:

            logger.exception(
                "Unexpected JWT authentication error"
            )

            scope["user"] = None

        # =====================================================
        # CONTINUE TO NEXT MIDDLEWARE / CONSUMER
        # =====================================================

        return await super().__call__(
            scope,
            receive,
            send
        )

    # =========================================================
    # GET USER FROM JWT
    # =========================================================

    @database_sync_to_async
    def get_user(
        self,
        token
    ):

        try:

            # ---------------------------------------------
            # Validate access token
            # ---------------------------------------------

            access_token = AccessToken(
                token
            )

            logger.info(
                "JWT access token validated successfully"
            )

            # ---------------------------------------------
            # Get user ID from token
            # ---------------------------------------------

            user_id = access_token.get(
                "user_id"
            )

            if not user_id:

                logger.warning(
                    "JWT authentication failed | "
                    "reason=user_id_missing"
                )

                return None

            # ---------------------------------------------
            # Get user from database
            # ---------------------------------------------

            user = User.objects.get(
                id=user_id
            )

            logger.info(
                "JWT user found in database | "
                "user_id=%s",
                user.id,
            )

            # ---------------------------------------------
            # Check active status
            # ---------------------------------------------

            if not user.is_active:

                logger.warning(
                    "JWT authentication rejected | "
                    "reason=user_inactive | user_id=%s",
                    user.id,
                )

                return None

            # ---------------------------------------------
            # Return authenticated user
            # ---------------------------------------------

            return user

        # =================================================
        # INVALID / EXPIRED TOKEN
        # =================================================

        except TokenError:

            logger.warning(
                "JWT authentication failed | "
                "reason=invalid_or_expired_token"
            )

            return None

        # =================================================
        # USER DOES NOT EXIST
        # =================================================

        except User.DoesNotExist:

            logger.warning(
                "JWT authentication failed | "
                "reason=user_not_found"
            )

            return None

        # =================================================
        # OTHER DATABASE / AUTH ERROR
        # =================================================

        except Exception:

            logger.exception(
                "Unexpected database or JWT authentication error"
            )

            return None

