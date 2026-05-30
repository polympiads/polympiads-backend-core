from django.test import TransactionTestCase
from unittest.mock import patch
from polympiads.contrib.auth.models import User
from polympiads.contrib.auth.signals import on_user_password_set

class OnUserSavedSignalTest(TransactionTestCase):

    def test_signal_fired_on_user_creation(self):
        with patch("polympiads.contrib.auth.signals.on_user_password_set.send") as mock_send:
            user = User.objects.create_user(username="alice", password="secret123")

            mock_send.assert_called_once_with(
                sender=User,
                user=user,
                password="secret123"
            )

    def test_signal_fired_on_password_change(self):
        user = User.objects.create_user(username="alice", password="oldpass")

        with patch("polympiads.contrib.auth.signals.on_user_password_set.send") as mock_send:
            user.set_password("newpass")
            user.save()

            mock_send.assert_called_once_with(
                sender=User,
                user=user,
                password="newpass"
            )

    def test_signal_not_fired_when_no_password_set(self):
        with patch("polympiads.contrib.auth.signals.on_user_password_set.send") as mock_send:
            user = User.objects.create_user(username="alice", password="secret123")
            mock_send.reset_mock()

            user.email = "alice@example.com"
            user.save()

            mock_send.assert_not_called()

    def test_signal_carries_correct_raw_password(self):
        received = []

        def handler(sender, user, password, **kwargs):
            received.append(password)

        on_user_password_set.connect(handler)
        try:
            User.objects.create_user(username="alice", password="secret123")
            self.assertEqual(received, ["secret123"])
        finally:
            on_user_password_set.disconnect(handler)