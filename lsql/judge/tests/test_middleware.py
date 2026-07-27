"""
Copyright Enrique Martín <emartinm@ucm.es> 2026

Unit tests for judge.middleware
"""

from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from judge.tests.test_common import create_user


class SentryUserMiddlewareTest(TestCase):
    """Tests for SentryUserMiddleware"""

    def test_sets_user_when_authenticated(self):
        """Sentry's user context is set to the authenticated user's id, and nothing else"""
        client = Client()
        user = create_user("1234", "pepe")
        client.login(username="pepe", password="1234")  # nosec B106

        with patch("judge.middleware.sentry_sdk.set_user") as mocked_set_user:
            client.get(reverse("judge:index"))

        mocked_set_user.assert_called_once_with({"id": user.pk})

    def test_does_not_set_user_when_anonymous(self):
        """Sentry's user context is left untouched for anonymous requests"""
        client = Client()

        with patch("judge.middleware.sentry_sdk.set_user") as mocked_set_user:
            client.get(reverse("judge:index"))

        mocked_set_user.assert_not_called()
