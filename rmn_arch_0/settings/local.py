"""
Local development settings
"""

from .base import *

import logging
import sys

# enable debug and allows all hosts
DEBUG = True
ALLOWED_HOSTS = ['*']

# output logs to console
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s\t%(asctime)s %(module)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
# disable logging in testing
if len(sys.argv) > 1 and sys.argv[1] == 'test':
    logging.disable(logging.CRITICAL)

# use console as email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# local static and media setting
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / '../static/'
MEDIA_ROOT = BASE_DIR / '../media/'
MEDIA_URL = '/media/'
