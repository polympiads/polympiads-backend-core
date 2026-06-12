
from typing import Any

from django.test import TestCase
from django.contrib.auth.models import Group

from polympiads.contrib.auth.serializers.modify.groups import ModifyGroupsSerializer


class TestModifyGroupsSerializer (TestCase):
    def setUp(self):
        self.admins  = Group.objects.create(name="Admins")
        self.editors = Group.objects.create(name="Editors")
        self.viewers = Group.objects.create(name="Viewers")

    def get_data (self, data: Any):
        ser = ModifyGroupsSerializer(data = data)
        if not ser.is_valid():
            print(ser.errors)
            raise AssertionError()
        return ser.data
    def get_errors (self, data: Any):
        ser = ModifyGroupsSerializer(data = data)
        assert not ser.is_valid()
        return ser.errors

    def test_serializer_empty_data (self):
        errors = self.get_errors({})
        assert errors.keys() == { 'non_field_errors' }
        assert errors["non_field_errors"][0].code == "invalid"
        assert errors["non_field_errors"][0] == "At least one of add_groups or remove_groups must be provided."

    def test_serializer_conflict (self):
        errors = self.get_errors({
            "add_groups"    : [ "Admins" ],
            "remove_groups" : [ "Admins" ]
        })
        assert errors.keys() == { 'non_field_errors' }
        assert errors["non_field_errors"][0].code == "invalid"
        assert errors["non_field_errors"][0] == "Cannot add and remove the same groups simultaneously."

    def test_serializer_group_doesnt_exist (self):
        errors = self.get_errors({
            "add_groups"    : [ "NonExistentGroup1" ],
            "remove_groups" : [ "NonExistentGroup2" ],
        })
        assert errors.keys() == { 'add_groups', "remove_groups" }
        assert errors["add_groups"][0].code == "does_not_exist"
        assert errors["add_groups"][0] == "Object with name=NonExistentGroup1 does not exist."
        assert errors["remove_groups"][0].code == "does_not_exist"
        assert errors["remove_groups"][0] == "Object with name=NonExistentGroup2 does not exist."

    def test_serializer_properly_returns_to_add_and_to_remove (self):
        data = self.get_data({
            "add_groups" : [ "Admins" ],
            "remove_groups" : [ "Editors", "Viewers" ]
        })
        assert len(data["add_groups"]) == 1
        assert len(data["remove_groups"]) == 2
        data = self.get_data({
            "add_groups" : [ "Admins" ],
            "remove_groups" : []
        })
        assert len(data["add_groups"]) == 1
        assert len(data["remove_groups"]) == 0
        data = self.get_data({
            "add_groups" : [],
            "remove_groups" : [ "Editors", "Viewers" ]
        })
        assert len(data["add_groups"]) == 0
        assert len(data["remove_groups"]) == 2
