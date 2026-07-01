
from typing import Any

from django.test import TestCase
from django.contrib.auth.models import Permission

from polympiads.contrib.auth.serializers.modify.permissions import ModifyPermissionsSerializer


class TestModifyPermissionsSerializer(TestCase):
    def setUp(self):
        self.access_dashboard = Permission.objects.get(
            codename="access_dashboard", content_type__app_label="polympiads_auth"
        )
        self.view_user = Permission.objects.get(
            codename="view_user", content_type__app_label="polympiads_auth"
        )
        self.change_user = Permission.objects.get(
            codename="change_user", content_type__app_label="polympiads_auth"
        )

        self.access_dashboard_pk = self.access_dashboard.pk
        self.view_user_pk        = self.view_user.pk
        self.change_user_pk      = self.change_user.pk

        self.nonexistent_pk = Permission.objects.order_by("-pk").first().pk + 1

    def get_data(self, data: Any):
        ser = ModifyPermissionsSerializer(data=data)
        if not ser.is_valid():
            print(ser.errors)
            raise AssertionError()
        return ser.data

    def get_errors(self, data: Any):
        ser = ModifyPermissionsSerializer(data=data)
        assert not ser.is_valid()
        return ser.errors

    def test_serializer_empty_data(self):
        errors = self.get_errors({})
        assert errors.keys() == {'non_field_errors'}
        assert errors["non_field_errors"][0].code == "invalid"
        assert errors["non_field_errors"][0] == "At least one of add_permissions or remove_permissions must be provided."

    def test_serializer_conflict(self):
        errors = self.get_errors({
            "add_permissions"    : [self.access_dashboard_pk],
            "remove_permissions" : [self.access_dashboard_pk],
        })
        assert errors.keys() == {'non_field_errors'}
        assert errors["non_field_errors"][0].code == "invalid"
        assert errors["non_field_errors"][0] == "Cannot add and remove the same permissions simultaneously."

    def test_serializer_wrong_type(self):
        errors = self.get_errors({
            "add_permissions"    : [{}],
            "remove_permissions" : [[]],
        })
        assert errors.keys() == {'add_permissions', 'remove_permissions'}
        assert errors["add_permissions"][0].code == "incorrect_type"
        assert errors["add_permissions"][0] == "Incorrect type. Expected pk value, received dict."
        assert errors["remove_permissions"][0].code == "incorrect_type"
        assert errors["remove_permissions"][0] == "Incorrect type. Expected pk value, received list."

    def test_serializer_wrong_format(self):
        errors = self.get_errors({
            "add_permissions"    : ["aaaaaa"],
            "remove_permissions" : ["aa.bb.cc"],
        })
        assert errors.keys() == {'add_permissions', 'remove_permissions'}
        assert errors["add_permissions"][0].code == "incorrect_type"
        assert errors["add_permissions"][0] == "Incorrect type. Expected pk value, received str."
        assert errors["remove_permissions"][0].code == "incorrect_type"
        assert errors["remove_permissions"][0] == "Incorrect type. Expected pk value, received str."

    def test_serializer_perm_doesnt_exist(self):
        errors = self.get_errors({
            "add_permissions"    : [self.nonexistent_pk],
            "remove_permissions" : [self.nonexistent_pk + 1],
        })
        assert errors.keys() == {'add_permissions', 'remove_permissions'}
        assert errors["add_permissions"][0].code == "does_not_exist"
        assert errors["add_permissions"][0] == f'Invalid pk "{self.nonexistent_pk}" - object does not exist.'
        assert errors["remove_permissions"][0].code == "does_not_exist"
        assert errors["remove_permissions"][0] == f'Invalid pk "{self.nonexistent_pk + 1}" - object does not exist.'

    def test_serializer_properly_returns_to_add_and_to_remove(self):
        data = self.get_data({
            "add_permissions"    : [self.access_dashboard_pk],
            "remove_permissions" : [self.view_user_pk, self.change_user_pk],
        })
        assert len(data["add_permissions"]) == 1
        assert len(data["remove_permissions"]) == 2
        data = self.get_data({
            "add_permissions"    : [self.access_dashboard_pk],
            "remove_permissions" : [],
        })
        assert len(data["add_permissions"]) == 1
        assert len(data["remove_permissions"]) == 0
        data = self.get_data({
            "add_permissions"    : [],
            "remove_permissions" : [self.view_user_pk, self.change_user_pk],
        })
        assert len(data["add_permissions"]) == 0
        assert len(data["remove_permissions"]) == 2
