def get_user_role(user):
    """Return the authenticated user's role."""

    if not user or not user.is_authenticated:
        return None

    return getattr(user, "role", None)


def is_admin(user):
    return get_user_role(user) == "ADMIN"


def is_driver(user):
    return get_user_role(user) == "DRIVER"


def is_passenger(user):
    return get_user_role(user) == "USER"
