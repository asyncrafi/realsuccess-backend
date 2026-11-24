"""
URL configuration for Real Success project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from apps.content_settings.views import (
    privacy_policy_page,
    terms_conditions_page,
)

urlpatterns = [
    # Public Compliance Web Pages (Apple App Store & Google Play Store)
    path("privacy/", privacy_policy_page, name="public-privacy"),
    path("privacy-policy/", privacy_policy_page, name="public-privacy-policy"),
    path("terms/", terms_conditions_page, name="public-terms"),
    path("terms-and-conditions/", terms_conditions_page, name="public-terms-conditions"),

    # Admin
    path("admin/", admin.site.urls),

    # API Documentation (Swagger & OpenAPI schema)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Feature Apps
    path("api/auth/", include("apps.accounts.urls")),
    path("api/events/", include("apps.events.urls")),
    path("api/schedule/", include("apps.schedule.urls")),
    path("api/tickets/", include("apps.tickets.urls")),
    path("api/announcements/", include("apps.announcements.urls")),
    path("api/resources/", include("apps.resources.urls")),
    path("api/chat/", include(("apps.message_team.urls", "message_team"), namespace="chat")),
    path("api/team/", include(("apps.message_team.urls", "message_team"), namespace="team")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/content/", include("apps.content_settings.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
