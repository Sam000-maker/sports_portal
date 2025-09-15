
from django.contrib import admin as dj_admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    # Keep Django's default admin reachable at /dj-admin/ (optional), but we won't use it.
    path("dj-admin/", dj_admin.site.urls),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("accounts/", include("accounts.urls")),
    path("backoffice/", include("backoffice.urls", namespace="backoffice")),
    path("tournaments/", include("tournaments.urls")),
    path("players/", include("players.urls")),
    path("admissions/", include("admissions.urls", namespace="admissions")),
    path("facilities/", include("facilities.urls")),
    path("analytics/", include("analytics.urls")),
]

if settings.DEBUG:
    # This must match MEDIA_URL exactly (leading/trailing slashes matter)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
