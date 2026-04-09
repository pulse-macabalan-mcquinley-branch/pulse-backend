import django_filters
from django_filters.rest_framework import FilterSet


class BaseFilterSet(FilterSet):
    """
    FilterSet base that all app filters extend.
    Adds created_after / created_before date range filtering.
    """

    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="Created after"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="Created before"
    )


class UserFilterSet(BaseFilterSet):
    """
    Filters for the User resource.
    ?role=admin&is_active=true&search=juan&created_after=2024-01-01
    """

    from apps.users.models import CustomUser

    role = django_filters.ChoiceFilter(choices=CustomUser.Role.choices)
    is_active = django_filters.BooleanFilter()
    search = django_filters.CharFilter(method="filter_search", label="Search")

    class Meta:
        model = CustomUser
        fields = ["role", "is_active"]

    def filter_search(self, queryset, name, value):
        from django.db.models import Q

        return queryset.filter(
            Q(email__icontains=value)
            | Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
        )