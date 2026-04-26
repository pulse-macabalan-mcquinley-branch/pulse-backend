from rest_framework.routers import (
    DefaultRouter,
)
from .views import (
    DeviceTypeViewSet,
    QuestionTypeViewSet,
    SurveyViewSet,
    QuestionViewSet,
    ResponseViewSet,
)
from django.urls import (
    include,
    path,
)
from rest_framework_nested import routers


router = DefaultRouter()
router.register(r"device-types", DeviceTypeViewSet, basename="device-types")
router.register(r"question-types", QuestionTypeViewSet, basename="question-types")
router.register(r"surveys", SurveyViewSet, basename="surveys")

surveys_router = routers.NestedDefaultRouter(
    router,
    r"surveys",
    lookup="survey"
)
surveys_router.register(r"questions", QuestionViewSet, basename="survey-questions")
surveys_router.register(r"responses", ResponseViewSet,  basename="survey-responses")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(surveys_router.urls))
]

