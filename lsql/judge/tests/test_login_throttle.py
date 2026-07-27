"""
Copyright Enrique Martín <emartinm@ucm.es> 2026

Unit tests for the django-axes login lockout (see AUTHENTICATION_BACKENDS and the
AXES_* settings in settings_shared.py, and judge/axes_backend.py)
"""

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from judge.tests.test_common import create_user


class LoginThrottleTest(TestCase):
    """Tests for the login lockout enforced by django-axes"""

    def test_locks_out_after_failure_limit(self):
        """The AXES_FAILURE_LIMIT-th wrong-password attempt reaches the limit and is itself
        turned into a lockout response (Axes counts and checks the limit synchronously within
        that same request - it does not wait for one further attempt beyond the limit).
        Afterwards, even the correct password is rejected until the cool-off period passes"""
        client = Client()
        create_user("correcta1234", "victima")
        login_url = reverse("judge:login")

        # The first AXES_FAILURE_LIMIT - 1 wrong attempts are plain invalid-credentials responses
        for _ in range(settings.AXES_FAILURE_LIMIT - 1):
            response = client.post(login_url, {"username": "victima", "password": "incorrecta"})  # nosec B105
            self.assertEqual(response.status_code, 200)  # LoginView re-renders the form with errors
            self.assertFalse(response.wsgi_request.user.is_authenticated)

        # The AXES_FAILURE_LIMIT-th wrong attempt pushes the failure count to the limit, so Axes
        # turns this very response into a lockout instead of the usual "wrong credentials" one
        response = client.post(login_url, {"username": "victima", "password": "incorrecta"})  # nosec B105
        self.assertEqual(response.status_code, settings.AXES_HTTP_RESPONSE_CODE)

        # Once locked out, even the CORRECT password is rejected - this is what proves it is a
        # real lockout and not just coincidentally still the wrong password
        response = client.post(login_url, {"username": "victima", "password": "correcta1234"})  # nosec B105
        self.assertEqual(response.status_code, settings.AXES_HTTP_RESPONSE_CODE)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_does_not_lock_out_under_failure_limit(self):
        """Fewer than AXES_FAILURE_LIMIT wrong attempts still allow the correct
        password to succeed afterward"""
        client = Client()
        create_user("correcta1234", "victima2")
        login_url = reverse("judge:login")

        for _ in range(settings.AXES_FAILURE_LIMIT - 1):
            response = client.post(login_url, {"username": "victima2", "password": "incorrecta"})  # nosec B105
            self.assertEqual(response.status_code, 200)

        response = client.post(
            login_url, {"username": "victima2", "password": "correcta1234"}, follow=True  # nosec B105
        )
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, "victima2")

    def test_lockout_is_scoped_to_username_not_whole_ip(self):
        """Locking out one username does not block a different user logging in from
        the same IP: AXES_LOCKOUT_PARAMETERS is keyed on (username, ip_address), not
        ip_address alone, so one account under attack cannot take down every other
        student behind the same shared/lab IP"""
        client = Client()
        create_user("correcta1234", "victima3")
        create_user("otra1234", "companera")
        login_url = reverse("judge:login")

        for _ in range(settings.AXES_FAILURE_LIMIT):
            client.post(login_url, {"username": "victima3", "password": "incorrecta"})  # nosec B105

        # victima3 is now locked out...
        response = client.post(login_url, {"username": "victima3", "password": "correcta1234"})  # nosec B105
        self.assertEqual(response.status_code, settings.AXES_HTTP_RESPONSE_CODE)

        # ...but a different user from the same test client (same IP) can still log in
        response = client.post(
            login_url, {"username": "companera", "password": "otra1234"}, follow=True  # nosec B105
        )
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, "companera")
