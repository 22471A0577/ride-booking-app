from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        return request.user.role == "ADMIN"


class IsAdminOrDriver(BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ["ADMIN", "DRIVER"]

    def has_object_permission(self, request, view, obj):

        if request.user.role == "ADMIN":
            return True

        if request.user.role == "DRIVER":
            return obj.driver.user == request.user

        return False


class IsRideParticipant(BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ["ADMIN", "USER", "DRIVER"]

    def has_object_permission(self, request, view, obj):

        if request.user.role == "ADMIN":
            return True

        if request.user.role == "USER":
            return obj.passenger == request.user

        if request.user.role == "DRIVER":
            return (
                obj.driver is not None
                and obj.driver.user == request.user
            )

        return False