
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter, SearchFilter

from django.contrib.auth.models import Permission

class PermissionFilterSet(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Permission
        fields = ['name']

class PermissionFilterMixin:
    filter_backends = [filters.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PermissionFilterSet
    search_fields = ['name']
    ordering_fields  = ['name']
    ordering = ['-pk']
