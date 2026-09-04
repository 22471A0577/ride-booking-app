import os

environment = os.getenv(
    "DJANGO_ENV",
    "development"
).lower()

if environment == "production":
    from .production import *
elif environment == "testing":
    from .testing import *
else:
    from .development import *