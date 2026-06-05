
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter, SearchFilter

from django.contrib.auth.models import Group

class GroupFilterSet(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Group
        fields = ['name']

class GroupFilterMixin:
    filter_backends = [filters.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = GroupFilterSet
    search_fields = ['name']
    ordering_fields  = ['name']
    ordering = ['-pk']
