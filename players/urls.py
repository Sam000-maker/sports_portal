from django.urls import path
from . import views

app_name = "players"

urlpatterns = [
    path("register/", views.PlayerRegisterView.as_view(), name="player_register"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),

    # NEW: dashboard
    path("dashboard/", views.PlayerDashboardView.as_view(), name="dashboard"),

    path("teams/", views.TeamListView.as_view(), name="team_list"),
    path("teams/create/", views.TeamCreateView.as_view(), name="team_create"),
    path("teams/<int:pk>/", views.TeamDetailView.as_view(), name="team_detail"),
    path("teams/<int:pk>/join/", views.AcceptInviteView.as_view(), name="team_accept"),

    path("gallery/", views.GalleryListView.as_view(), name="gallery_list"),
    path("gallery/upload/", views.GalleryUploadView.as_view(), name="gallery_upload"),
    path("gallery/<int:pk>/like/", views.GalleryLikeToggle.as_view(), name="gallery_like"),
]
