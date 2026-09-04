from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class RegistrationRateThrottle(AnonRateThrottle):
    scope = "registration"


class PasswordResetRateThrottle(AnonRateThrottle):
    scope = "password_reset"


class OTPRateThrottle(AnonRateThrottle):
    scope = "otp"


class RideCreationRateThrottle(UserRateThrottle):
    scope = "ride_creation"