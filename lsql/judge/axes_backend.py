"""
Copyright Enrique Martín <emartinm@ucm.es> 2026

Authentication backend that wraps django-axes to make it tolerate authenticate() calls
made without a request object.
"""

from axes.backends import AxesBackend


class RequestOptionalAxesBackend(AxesBackend):
    """
    django-axes' own AxesBackend.authenticate() requires a real HttpRequest: if it is
    called with request=None, it raises AxesBackendRequestParameterRequired (a plain
    ValueError, NOT a PermissionDenied). Django's own authenticate() function only
    catches PermissionDenied to move on to the next configured backend, so any other
    exception - including that ValueError - propagates and crashes the caller.

    Every REAL login attempt always provides a request: Django's LoginView calls
    authenticate(self.request, **credentials). The only caller that omits it is
    Django's test Client.login() shortcut:

        def login(self, **credentials):
            user = authenticate(**credentials)  # no request passed -> defaults to None
            ...

    This project's test suite uses that shortcut hundreds of times across test_views.py,
    test_submit.py, test_ranking.py, test_languages.py, etc., purely to set up an
    authenticated session while testing unrelated features - never to exercise the login
    endpoint itself. Without this subclass, simply adding the stock AxesBackend to
    AUTHENTICATION_BACKENDS would make every one of those unrelated calls raise
    ValueError, unrelated to whatever each test actually intends to check.

    This subclass defers to the next backend (plain ModelBackend, via returning None)
    whenever request is None, and behaves exactly like the stock AxesBackend otherwise -
    so real login attempts (always carrying a request) remain fully protected by Axes'
    lockout logic, while the test-only shortcut keeps working unaffected.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if request is None:
            return None
        return super().authenticate(request, username=username, password=password, **kwargs)
