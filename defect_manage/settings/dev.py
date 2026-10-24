from .base import *  # noqa

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-=4n_$f!f%m7k&%-h)6$6a@8q!(8ir37(_vajee)wvhvv#dmsl7",
)
DEBUG = True
ALLOWED_HOSTS = ["*"]
