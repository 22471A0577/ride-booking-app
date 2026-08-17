from decimal import Decimal


# Configurable default fare values
DEFAULT_DISTANCE_RATE = Decimal("10.00")
DEFAULT_TIME_RATE = Decimal("2.00")


def calculate_fare(
    base_fare,
    distance_km,
    time_minutes,
    surge_multiplier=Decimal("1.00"),
    distance_rate=DEFAULT_DISTANCE_RATE,
    time_rate=DEFAULT_TIME_RATE,
):
    """
    Calculate ride fare.

    Formula:

    Base Fare
    + Distance Fare
    + Time Fare
    + Surge
    = Total
    """

    base_fare = Decimal(str(base_fare))
    distance_km = Decimal(str(distance_km))
    time_minutes = Decimal(str(time_minutes))
    surge_multiplier = Decimal(str(surge_multiplier))
    distance_rate = Decimal(str(distance_rate))
    time_rate = Decimal(str(time_rate))

    if base_fare < 0:
        raise ValueError("Base fare cannot be negative.")

    if distance_km < 0:
        raise ValueError("Distance cannot be negative.")

    if time_minutes < 0:
        raise ValueError("Time cannot be negative.")

    if surge_multiplier < Decimal("1.00"):
        raise ValueError(
            "Surge multiplier cannot be less than 1.00."
        )

    distance_fare = distance_km * distance_rate
    time_fare = time_minutes * time_rate

    subtotal = (
        base_fare
        + distance_fare
        + time_fare
    )

    surge_amount = subtotal * (
        surge_multiplier - Decimal("1.00")
    )

    total = subtotal + surge_amount

    return {
        "base_fare": base_fare.quantize(Decimal("0.01")),
        "distance_fare": distance_fare.quantize(Decimal("0.01")),
        "time_fare": time_fare.quantize(Decimal("0.01")),
        "surge": surge_amount.quantize(Decimal("0.01")),
        "total": total.quantize(Decimal("0.01")),
    }