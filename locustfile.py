from itertools import cycle

from locust import HttpUser, task, between


with open("locust_tokens.txt", "r") as file:
    TOKENS = [line.strip() for line in file if line.strip()]

token_cycle = cycle(TOKENS)


class RideBookingUser(HttpUser):
    wait_time = between(5, 7)

    def on_start(self):
        token = next(token_cycle)

        self.client.headers.update({
            "Authorization": f"Bearer {token}"
        })

    @task
    def nearby_drivers(self):
        self.client.get(
            "/api/v1/drivers/nearby/"
            "?latitude=16.307000"
            "&longitude=80.437000"
            "&radius=10",
            name="Nearby Drivers",
        )