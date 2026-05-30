
from django.dispatch import receiver
from django.db.models.signals import post_save
from polympiads.contrib.auth.models  import User
from polympiads.contrib.auth.signals import on_user_password_set

@receiver(post_save, sender=User)
def on_user_saved (sender, instance: User, created: bool, **kwargs):
    raw_password = getattr(instance, "_password", None)

    if raw_password is not None:
        on_user_password_set.send(
            sender = User,

            user     = instance,
            password = raw_password
        )
