from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from apps.users.views import GoogleLoginView

api_v1_urlpatterns = [
    # ── Auth (Djoser + SimpleJWT) ──────────────────────────────
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
    # path("auth/", include("djoser.social.urls")),
    path("auth/google/", GoogleLoginView.as_view(), name="google-login"),

    # ── Users resource ─────────────────────────────────────────
    path("users/", include("apps.users.urls")),

    # ── Surveys resource ─────────────────────────────────────────
    path("", include("apps.surveys.urls")),

    # ── OpenAPI schema ─────────────────────────────────────────
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/",   SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/",  SpectacularRedocView.as_view(url_name="schema"),   name="redoc"),
]

urlpatterns = [
    path("admin/",    admin.site.urls),
    path("api/v1/",   include(api_v1_urlpatterns)),
]

# ── Development extras ────────────────────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()

    try:
        import debug_toolbar
        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass