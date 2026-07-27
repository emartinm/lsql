"""
Copyright Enrique Martín <emartinm@ucm.es> 2020

Tags Sentry events with the authenticated user's numeric id only (no username/email/IP,
so send_default_pii stays disabled)
"""

import sentry_sdk


class SentryUserMiddleware:
    """Associates Sentry events with request.user.pk when authenticated"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            sentry_sdk.set_user({"id": request.user.pk})
        return self.get_response(request)
