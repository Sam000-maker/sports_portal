"""
URL configuration for sports_portal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin as dj_admin
from django.urls import path, include
from django.views.generic import TemplateView

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
