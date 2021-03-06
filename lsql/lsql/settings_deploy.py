"""
Django setting that will be loaded only when DJANGO_DEVELOPMENT is defined in the environment

Can define new settings or override previous settings in settings_shared
"""

import os


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

# For error reporting, sending e-mail for internal error (500)
ADMINS = [('Enrique Martín', 'emartinm@ucm.es')]
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_SUBJECT_PREFIX = 'Error en learn.fdi.ucm.es: '
EMAIL_HOST_USER = os.environ.get('REPORT_EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('REPORT_EMAIL_PASS')
SERVER_EMAIL = EMAIL_HOST_USER
