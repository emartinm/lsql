"""
Django settings loaded only in DEPLOYMENT (when DJANGO_DEVELOPMENT is NOT defined in the environment),
on top of settings_shared. See deploy/env.example.

Additional environment variables:
  ALLOWED_HOSTS     public host names of the judge, comma separated (required)
  SENTRY_DSN        (optional)
  SENTRY_TRACES_SAMPLE_RATE  (optional, 0.1 by default)
"""

import os

import sentry_sdk

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False  # Redefined

# Accept only requests directed to the public host names of the judge
ALLOWED_HOSTS = [host.strip() for host in os.environ["ALLOWED_HOSTS"].split(",") if host.strip()]  # Redefined
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]

# Browsers are forced to connect using only HTTPS for 1 year
SECURE_HSTS_SECONDS = 31536000

# HSTS seconds also include subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Needed to be elegible to be included in the Chrome HSTS preload list of domains
# harcoded to be HTTPS only
SECURE_HSTS_PRELOAD = True

# Requests redirected from Nginx with X-Forwarded-proto = https will be considered secure
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HTTP must be redirected to HTTPS (Nginx assures that)
SECURE_SSL_REDIRECT = True

# Session cookies are only sent through HTTPS
SESSION_COOKIE_SECURE = True

# AntiCSRF cookies are only sent through HTTPS
CSRF_COOKIE_SECURE = True


# Sentry for error log
if os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        # Sampling every request (as 1.0 would) is expensive and unnecessary
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
    )
