
from typing import Dict, List, Set

from rest_framework import serializers

from django.contrib.auth.models import Permission

from polympiads.contrib.auth.serializers.fields.permission import PermissionStringRelatedField

class ModifyPermissionsSerializer (serializers.Serializer):
    add_permissions    = PermissionStringRelatedField(many = True, required = False, default = list)
    remove_permissions = PermissionStringRelatedField(many = True, required = False, default = list)

    def validate(self, data: Dict[str, List[Permission]]):
        add_perms    : Set[int] = { perm.pk for perm in data.get("add_permissions", []) }
        remove_perms : Set[int] = { perm.pk for perm in data.get("remove_permissions", []) }

        overlapping = add_perms & remove_perms

        if len(overlapping) != 0:
            raise serializers.ValidationError(
                "Cannot add and remove the same permissions simultaneously."
            )
        
        if not any([
            data.get("add_permissions"),
            data.get("remove_permissions")
        ]):
            raise serializers.ValidationError(
                "At least one of add_permissions or remove_permissions must be provided."
            )

        return super().validate(data)
