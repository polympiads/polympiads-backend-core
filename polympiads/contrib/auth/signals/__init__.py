
from django.dispatch import Signal

"""
This signal is called whenever a user's password is changed.

Parameters of the signal are
 - sender: the class polympiads.contrib.auth.models.User
 - user: the user that has been modified
 - password: its new password
"""
on_user_password_set = Signal()
