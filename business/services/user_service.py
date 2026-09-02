from business.models import User


def get_user_by_id(user_id):
    """
    Retrieve a user by primary key.
    """
    return User.objects.get(pk=user_id)


def get_user_by_email(email):
    """
    Retrieve a user by email address.
    """
    return User.objects.get(email=email)


def create_user(email, password=None, **extra_fields):
    """
    Create a user through the custom UserManager.
    """
    return User.objects.create_user(
        email=email,
        password=password,
        **extra_fields,
    )
