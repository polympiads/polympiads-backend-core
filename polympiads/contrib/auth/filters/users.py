
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter, SearchFilter

from polympiads.contrib.auth.models import User

class UserFilterSet(filters.FilterSet):
    username     = filters.CharFilter(lookup_expr='icontains')
    email        = filters.CharFilter(lookup_expr='icontains')
    first_name   = filters.CharFilter(lookup_expr='icontains')
    last_name    = filters.CharFilter(lookup_expr='icontains')
    is_active    = filters.BooleanFilter()
    is_staff     = filters.BooleanFilter()
    is_superuser = filters.BooleanFilter()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name',
                  'is_active', 'is_staff', 'is_superuser']

class UserFilterMixin:
    filter_backends = [filters.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = UserFilterSet
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields  = ['username', 'email', 'date_joined', 'last_login', 'is_active', 'is_staff', 'is_superuser']
    ordering = ['-pk']
