from decimal import Decimal

from django.test import SimpleTestCase

from business.services.fare_service import calculate_fare


class FareCalculationTests(SimpleTestCase):

    def test_basic_fare_calculation(self):
        result = calculate_fare(
            base_fare=40,
            distance_km=8,
            time_minutes=10,
            surge_multiplier=1,
        )

        self.assertEqual(
            result["base_fare"],
            Decimal("40")
        )

        self.assertEqual(
            result["distance_fare"],
            Decimal("80")
        )

        self.assertEqual(
            result["time_fare"],
            Decimal("20")
        )

        self.assertEqual(
            result["surge"],
            Decimal("0")
        )

        self.assertEqual(
            result["total"],
            Decimal("140")
        )

    def test_surge_fare_calculation(self):
        result = calculate_fare(
            base_fare=40,
            distance_km=8,
            time_minutes=10,
            surge_multiplier=1.5,
        )

        self.assertEqual(
            result["surge"],
            Decimal("70")
        )

        self.assertEqual(
            result["total"],
            Decimal("210")
        )