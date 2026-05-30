
from django.apps import apps
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth.hashers import make_password
from polympiads.contrib.auth.signals import on_user_password_set

class CustomUserManager (UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        user = super()._create_user(username, email, password, **extra_fields)

        if password is not None:
            on_user_password_set.send(
                sender = User,

                user     = user,
                password = password
            )

        return user

class User (AbstractUser):
    objects = CustomUserManager()
