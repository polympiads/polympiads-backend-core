
from django.apps import AppConfig

class PolympiadsAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'polympiads.contrib.auth'
    label = "polympiads_auth"
    
    def ready(self):
        # discover signals receivers
        import polympiads.contrib.auth.signals.receivers

        from polympiads.core.router import router

        from polympiads.contrib.auth.views.permissions import PermissionViewSet
        from polympiads.contrib.auth.views.groups import GroupViewSet
        from polympiads.contrib.auth.views.users import UserViewSet

        router.register("auth/permissions", PermissionViewSet)
        router.register("auth/groups", GroupViewSet)
        router.register("auth/users", UserViewSet)

        from django.db.models.signals import post_migrate
        post_migrate.connect(create_permissions, sender=self)

def create_permissions(sender, **kwargs):
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission

    ct, _ = ContentType.objects.get_or_create(app_label='polympiads_auth', model='')

    Permission.objects.get_or_create(
        codename='access_dashboard',
        content_type=ct,
        defaults={'name': 'Can access dashboard'},
    )