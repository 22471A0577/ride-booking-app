from decimal import Decimal


def validate_positive_number(value, field_name):
    """Validate that a numeric value is zero or greater."""

    try:
        value = Decimal(str(value))
    except Exception:
        raise ValueError(
            f"{field_name} must be a valid number."
        )

    if value < 0:
        raise ValueError(
            f"{field_name} cannot be negative."
        )

    return value


def validate_required(value, field_name):
    """Validate that a required value exists."""

    if value is None or str(value).strip() == "":
        raise ValueError(
            f"{field_name} is required."
        )

    return value
