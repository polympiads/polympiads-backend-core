
from typing import Dict, List, Set

from rest_framework import serializers

from django.contrib.auth.models import Group

class ModifyGroupsSerializer (serializers.Serializer):
    add_groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        required=False,
        default=list,
    )
    remove_groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        required=False,
        default=list,
    )

    def validate(self, data: Dict[str, List[Group]]):
        add_groups    : Set[int] = { group.pk for group in data.get("add_groups", []) }
        remove_groups : Set[int] = { group.pk for group in data.get("remove_groups", []) }

        overlapping = add_groups & remove_groups

        if len(overlapping) != 0:
            raise serializers.ValidationError(
                "Cannot add and remove the same groups simultaneously."
            )

        if not any([
            data.get("add_groups"),
            data.get("remove_groups")
        ]):
            raise serializers.ValidationError(
                "At least one of add_groups or remove_groups must be provided."
            )

        return super().validate(data)
