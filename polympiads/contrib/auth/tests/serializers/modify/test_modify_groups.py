
from typing import Any

from django.test import TestCase
from django.contrib.auth.models import Group

from polympiads.contrib.auth.serializers.modify.groups import ModifyGroupsSerializer


class TestModifyGroupsSerializer (TestCase):
    def setUp(self):
        self.admins  = Group.objects.create(name="Admins")
        self.editors = Group.objects.create(name="Editors")
        self.viewers = Group.objects.create(name="Viewers")

        self.nonexistent_pk = Group.objects.order_by("-pk").first().pk + 1

    def get_data(self, data: Any):
        ser = ModifyGroupsSerializer(data=data)
        if not ser.is_valid():
            print(ser.errors)
            raise AssertionError()
        return ser.data

    def get_errors(self, data: Any):
        ser = ModifyGroupsSerializer(data=data)
        assert not ser.is_valid()
        return ser.errors

    def test_serializer_empty_data(self):
        errors = self.get_errors({})
        assert errors.keys() == {'non_field_errors'}
        assert errors["non_field_errors"][0].code == "invalid"
        assert errors["non_field_errors"][0] == "At least one of add_groups or remove_groups must be provided."

    def test_serializer_conflict(self):
        errors = self.get_errors({
            "add_groups"    : [self.admins.pk],
            "remove_groups" : [self.admins.pk],
        })
        assert errors.keys() == {'non_field_errors'}
        assert errors["non_field_errors"][0].code == "invalid"
        assert errors["non_field_errors"][0] == "Cannot add and remove the same groups simultaneously."

    def test_serializer_wrong_type(self):
        errors = self.get_errors({
            "add_groups"    : [{}],
            "remove_groups" : [[]],
        })
        assert errors.keys() == {'add_groups', 'remove_groups'}
        assert errors["add_groups"][0].code == "incorrect_type"
        assert errors["add_groups"][0] == "Incorrect type. Expected pk value, received dict."
        assert errors["remove_groups"][0].code == "incorrect_type"
        assert errors["remove_groups"][0] == "Incorrect type. Expected pk value, received list."

    def test_serializer_group_doesnt_exist(self):
        errors = self.get_errors({
            "add_groups"    : [self.nonexistent_pk],
            "remove_groups" : [self.nonexistent_pk + 1],
        })
        assert errors.keys() == {'add_groups', 'remove_groups'}
        assert errors["add_groups"][0].code == "does_not_exist"
        assert errors["add_groups"][0] == f'Invalid pk "{self.nonexistent_pk}" - object does not exist.'
        assert errors["remove_groups"][0].code == "does_not_exist"
        assert errors["remove_groups"][0] == f'Invalid pk "{self.nonexistent_pk + 1}" - object does not exist.'

    def test_serializer_properly_returns_to_add_and_to_remove(self):
        data = self.get_data({
            "add_groups"    : [self.admins.pk],
            "remove_groups" : [self.editors.pk, self.viewers.pk],
        })
        assert len(data["add_groups"]) == 1
        assert len(data["remove_groups"]) == 2
        data = self.get_data({
            "add_groups"    : [self.admins.pk],
            "remove_groups" : [],
        })
