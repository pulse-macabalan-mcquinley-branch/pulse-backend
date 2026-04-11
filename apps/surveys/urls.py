from rest_framework.routers import (
    DefaultRouter,
)
from .views import (
    DeviceTypeViewSet,
    QuestionTypeViewSet,
)
from django.urls import (
    include,
    path,
)

router = DefaultRouter()
router.register(r"device-types", DeviceTypeViewSet, basename="device-types")
router.register(r"question-types", QuestionTypeViewSet, basename="question-types")

urlpatterns = [
    path("", include(router.urls))
]

