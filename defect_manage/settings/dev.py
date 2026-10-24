from .base import *  # noqa
import os

# 加载.env文件（如果存在）
_env_path = BASE_DIR / ".env"
if _env_path.exists():
    for line in _env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-=4n_$f!f%m7k&%-h)6$6a@8q!(8ir37(_vajee)wvhvv#dmsl7",
)
DEBUG = True
ALLOWED_HOSTS = ["*"]
