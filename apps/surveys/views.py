from rest_framework.viewsets import (
    ReadOnlyModelViewSet,
)
from .serializers import (
    DeviceTypeSerializer,
    QuestionTypeSerializer,
)
from .models import (
    DeviceType,
    QuestionType,
)
from rest_framework.permissions import (
    AllowAny,
)
from core.throttling import (
    AnonBurstThrottle,
    AnonSustainedThrottle
)

class DeviceTypeViewSet(ReadOnlyModelViewSet):
    """
    Read-only device type list/detail. No auth required.
    """

    queryset = DeviceType.objects.all()
    serializer_class = DeviceTypeSerializer
    permission_classes = [AllowAny]
    ordering = ["code", "name"]
    pagination_class = None

    throttle_classes = [
        AnonBurstThrottle,
        AnonSustainedThrottle,
    ]

class QuestionTypeViewSet(ReadOnlyModelViewSet):
    """
    Read-only question type list/detail. No auth required.
    """

    queryset = QuestionType.objects.all()
    serializer_class = QuestionTypeSerializer
    permission_classes = [AllowAny]
    ordering = ["code", "name"]
    pagination_class = None
    
    throttle_classes = [
        AnonBurstThrottle,
        AnonSustainedThrottle,
    ]