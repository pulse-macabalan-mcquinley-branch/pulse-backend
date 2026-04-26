from django_filters import rest_framework as filters
from ..models import Response

class ResponseFilter(filters.FilterSet):
    status        = filters.ChoiceFilter(choices=Response.Status.choices)
    is_flagged    = filters.BooleanFilter()
    is_offline    = filters.BooleanFilter(field_name="is_offline_submitted")
    submitted_from = filters.DateTimeFilter(field_name="submitted_at", lookup_expr="gte")
    submitted_to   = filters.DateTimeFilter(field_name="submitted_at", lookup_expr="lte")
    device_type   = filters.CharFilter(field_name="device_type__code")

    class Meta:
        model = Response
        fields = [
            "status",
            "is_flagged",
            "is_offline",
            "submitted_from",
            "submitted_to",
            "device_type",
        ]