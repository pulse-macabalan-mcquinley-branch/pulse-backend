from rest_framework.routers import (
    DefaultRouter,
)
from .views import (
    DeviceTypeViewSet,
    QuestionTypeViewSet,
    SurveyViewSet,
)
from django.urls import (
    include,
    path,
)

router = DefaultRouter()
router.register(r"device-types", DeviceTypeViewSet, basename="device-types")
router.register(r"question-types", QuestionTypeViewSet, basename="question-types")
router.register(r"surveys", SurveyViewSet, basename="surveys")

urlpatterns = [
    path("", include(router.urls))
]

