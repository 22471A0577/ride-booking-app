from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from django.contrib.auth import get_user_model

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(
        self,
        scope,
        receive,
        send
    ):

        print("\n========================================")
        print("=== JWT AUTH MIDDLEWARE STARTED ===")
        print("========================================")

        # =====================================================
        # GET QUERY STRING
        # =====================================================

        query_string = (
            scope
            .get("query_string", b"")
            .decode()
        )

        print(
            "Query string:",
            query_string
        )

        # =====================================================
        # PARSE QUERY PARAMETERS
        # =====================================================

        query_params = parse_qs(
            query_string
        )

        print(
            "Query parameters:",
            query_params
        )

        # =====================================================
        # GET TOKEN
        # =====================================================

        token_list = query_params.get(
            "token"
        )

        if not token_list:

            print(
                "❌ NO JWT TOKEN FOUND"
            )

            scope["user"] = None

            return await super().__call__(
                scope,
                receive,
                send
            )

        token = token_list[0]

        print(
            "✅ JWT TOKEN RECEIVED"
        )

        # Don't print the actual token.
        # JWT tokens are credentials and should not
        # appear in application logs.

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

                print(
                    "❌ USER NOT AUTHENTICATED"
                )

                scope["user"] = None

            # ---------------------------------------------
            # User authenticated
            # ---------------------------------------------

            else:

                print(
                    "✅ USER AUTHENTICATED"
                )

                print(
                    "User ID:",
                    user.id
                )

                print(
                    "User email:",
                    user.email
                )

                print(
                    "User role:",
                    user.role
                )

                scope["user"] = user

        except Exception as e:

            print(
                "❌ JWT AUTHENTICATION ERROR:",
                repr(e)
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

            print(
                "✅ ACCESS TOKEN VALID"
            )

            # ---------------------------------------------
            # Get user ID from token
            # ---------------------------------------------

            user_id = access_token.get(
                "user_id"
            )

            print(
                "Token user_id:",
                user_id
            )

            if not user_id:

                print(
                    "❌ user_id missing from token"
                )

                return None

            # ---------------------------------------------
            # Get user from database
            # ---------------------------------------------

            user = User.objects.get(
                id=user_id
            )

            print(
                "✅ USER FOUND IN DATABASE"
            )

            # ---------------------------------------------
            # Check active status
            # ---------------------------------------------

            if not user.is_active:

                print(
                    "❌ USER IS INACTIVE"
                )

                return None

            # ---------------------------------------------
            # Return authenticated user
            # ---------------------------------------------

            return user

        # =================================================
        # INVALID / EXPIRED TOKEN
        # =================================================

        except TokenError as e:

            print(
                "❌ INVALID OR EXPIRED JWT TOKEN:",
                str(e)
            )

            return None

        # =================================================
        # USER DOES NOT EXIST
        # =================================================

        except User.DoesNotExist:

            print(
                "❌ USER DOES NOT EXIST"
            )

            return None

        # =================================================
        # OTHER DATABASE / AUTH ERROR
        # =================================================

        except Exception as e:

            print(
                "❌ DATABASE/AUTH ERROR:",
                repr(e)
            )

            return None