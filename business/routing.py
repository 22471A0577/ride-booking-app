from django.urls import re_path

from .consumers import RideConsumer


websocket_urlpatterns = [
    re_path(
        r"ws/rides/(?P<ride_id>[0-9a-f-]+)/$",
        RideConsumer.as_asgi(),
    ),
]