from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    "testserver",
    "127.0.0.1",
    "localhost",
]

CORS_ALLOWED_ORIGINS = []

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False