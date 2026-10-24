"""
Django settings for defect_manage project.

配置来源: **环境变量** —— 可以写在项目根的 ``.env`` 里(模板见 ``.env.example``)。
本文件不硬编码任何密钥/主机名:

* ``DJANGO_SECRET_KEY``: 生产必填; 开发环境缺失时用一次性随机值并告警(重启后会话失效)。
* ``DJANGO_DEBUG``: 默认 true(开发); 生产必须设 false。
* ``DJANGO_ALLOWED_HOSTS``: 逗号分隔; DEBUG=true 时可留空。
* ``DJANGO_LANGUAGE_CODE`` / ``DJANGO_TIME_ZONE``: 默认 en-us / UTC。

For the full list of settings and their values, see
https://docs.djangoproject.com/en/6.1/ref/settings/
"""

import os
import secrets
import warnings
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = BASE_DIR / ".env"


def _load_env_file(path: Path) -> None:
    """把 .env 里的 KEY=value 灌进 os.environ(已存在的环境变量优先)。

    只用标准库实现, 不引入额外依赖: 支持 ``#`` 注释、空行、值两端引号;
    不支持多行值和变量展开(够用即可, 复杂场景请用真实环境变量)。
    """
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))


_load_env_file(ENV_FILE)


def _env_bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str) -> list:
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


def _secret_key() -> str:
    key = os.environ.get("DJANGO_SECRET_KEY", "").strip()
    if key:
        return key
    warnings.warn(
        "未设置 DJANGO_SECRET_KEY, 本次进程使用一次性随机密钥(重启后登录态与签名失效)。"
        " 请在项目根 .env 中设置, 模板见 .env.example。",
        RuntimeWarning, stacklevel=2)
    return secrets.token_urlsafe(64)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = _secret_key()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "defect",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "defect_manage.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "defect_manage.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases
# 路径由 BASE_DIR 推导, 不写死盘符; 需要用别的库时改这里或换 DATABASE_URL 方案。

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = os.environ.get("DJANGO_LANGUAGE_CODE", "en-us")

TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "UTC")

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# 用户上传图片配置
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}