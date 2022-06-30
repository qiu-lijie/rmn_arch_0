"""
Production settings
"""

from .base import *

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


ALLOWED_HOSTS = ['.rmn_arch_0.com']


# Security settings
DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True


# AWS SES for EMAIL_BACKEND
EMAIL_BACKEND = "anymail.backends.amazon_ses.EmailBackend"
INSTALLED_APPS.append('anymail')


# AWS S3 storage for media and static files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'rmn_arch_0.settings.storages.StaticStorage'
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}


# Sentry config for capturing errors
sentry_sdk.init(
    dsn = env('SENTRY_DSN'),
    integrations = [DjangoIntegration()],
    send_default_pii = True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate = 0,
)
