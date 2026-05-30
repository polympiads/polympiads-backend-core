
from typing import List, Literal, Optional, TypedDict, Type, Dict

from rest_framework.views import APIView
from rest_framework.permissions import BasePermission

from polympiads.contrib.utils.permissions.never import NeverAllow

SupportedActions = Literal[
    'get', 'edit',
    'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'
]

ACTION_ALIASES: Dict[str, str] = {
    'list': 'get',
    'retrieve': 'get',
    'update': 'edit',
    'partial_update': 'edit',
}

class ActionPermissionMixin:
    """
    A mixin that allows defining permission_classes per viewset action 
    using both standard DRF actions and aliases (get, edit).
    """
    permission_classes_default: List[Type[BasePermission]] = [NeverAllow]
    permission_classes_by_action: Dict[SupportedActions, List[Type[BasePermission]]] = {}

    def get_permissions(self) -> list:
        action = self.action

        if action in self.permission_classes_by_action:
            permission_classes = self.permission_classes_by_action[action]
        else:
            alias = ACTION_ALIASES.get(action)
            if alias and alias in self.permission_classes_by_action:
                permission_classes = self.permission_classes_by_action[alias]
            else:
                permission_classes = self.permission_classes_default
        
        return [permission() for permission in permission_classes]
