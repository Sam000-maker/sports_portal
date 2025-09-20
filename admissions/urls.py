# admissions/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "admissions"

urlpatterns = [
    # Staff list (guests are redirected away in the view)
    path("applications/", views.ApplicationListView.as_view(), name="my_applications"),

    # Create: router + explicit guest/staff endpoints
    path("applications/new/", views.ApplicationCreateRouterView.as_view(), name="application_create"),
    path("applications/new/guest/", views.ApplicationCreateGuestView.as_view(), name="application_create_guest"),
    path("applications/new/staff/", views.ApplicationCreateStaffView.as_view(), name="application_create_staff"),

    # Guest: single profile (detail) and edit
    path("applications/me/", views.MyApplicationView.as_view(), name="my_application"),
    path("applications/me/<int:pk>/edit/", views.ApplicationUpdateSelfView.as_view(), name="application_edit_self"),

    # Staff detail + actions
    path("applications/<int:pk>/", views.ApplicationDetailView.as_view(), name="application_detail"),
    path("applications/<int:pk>/upload/", views.DocumentUploadView.as_view(), name="document_upload"),
    path("applications/<int:pk>/review/", views.ApplicationReviewUpdateView.as_view(), name="application_review"),
    path("applications/<int:pk>/decision/", views.ApplicationDecisionView.as_view(), name="application_decision"),

    # Admin controls
    path("admin/cycle/", views.AdmissionControlView.as_view(), name="admin_cycle"),
    path("admin/cycle/start/", views.StartAdmissionView.as_view(), name="admin_cycle_start"),
    path("admin/cycle/extend/", views.ExtendAdmissionView.as_view(), name="admin_cycle_extend"),
    path("admin/cycle/stop/", views.StopAdmissionView.as_view(), name="admin_cycle_stop"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
