"""
Django setting that will be loaded only when DJANGO_DEVELOPMENT is defined in the environment

Can define new settings or override previous settings in settings_shared
"""

import os
import sentry_sdk


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False  # Redefined

# Accept only requests directed to learn.fdi.ucm.es
ALLOWED_HOSTS = ['learn.fdi.ucm.es']  # Redefined

# Browsers are forced to connect using only HTTPS for 1 year
SECURE_HSTS_SECONDS = 31536000

# HSTS seconds also include subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Needed to be elegible to be included in the Chrome HSTS preload list of domains
# harcoded to be HTTPS only
SECURE_HSTS_PRELOAD = True

# Requests redirected from Nginx with X-Forwarded-proto = https will be considered secure
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HTTP must be redirected to HTTPS (Nginx assures that)
SECURE_SSL_REDIRECT = True

# Session cookies are only sent through HTTPS
SESSION_COOKIE_SECURE = True

# AntiCSRF cookies are only sent through HTTPS
CSRF_COOKIE_SECURE = True


# Sentry for error log
sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN', ''),
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)
