
from rest_framework.permissions import BasePermission

class NeverAllow (BasePermission):
    def has_permission(self, request, view):
        return False
