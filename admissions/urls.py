# admissions/urls.py
from django.urls import path
from . import views

app_name = "admissions"

urlpatterns = [
    # Applicant flows
    path("applications/", views.ApplicationListView.as_view(), name="my_applications"),
    path("applications/new/", views.ApplicationCreateView.as_view(), name="application_create"),
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
