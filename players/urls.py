from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = "players"

urlpatterns = [
    # Teams
    path("teams/", views.TeamListView.as_view(), name="team_list"),
    path("teams/create/", views.TeamCreateView.as_view(), name="team_create"),
    path("teams/<int:pk>/", views.TeamDetailView.as_view(), name="team_detail"),
    path("teams/<int:pk>/join/", views.AcceptInviteView.as_view(), name="team_accept"),
    path("memberships/<int:pk>/edit/", views.MembershipEditView.as_view(), name="membership_edit"),

    # Position admin
    path("positions/", views.PositionAdminDashboard.as_view(), name="position_admin"),

    # Groups
    path("positions/group/new/", views.PositionGroupCreateView.as_view(), name="position_group_new"),
    path("positions/group/<int:pk>/edit/", views.PositionGroupUpdateView.as_view(), name="position_group_edit"),
    path("positions/group/<int:pk>/delete/", views.PositionGroupDeleteView.as_view(), name="position_group_delete"),

    # Positions
    path("positions/new/", views.PositionCreateView.as_view(), name="position_new"),
    path("positions/<int:pk>/delete/", views.PositionDeleteView.as_view(), name="position_delete"),

    # Formations (no JSON)
    path("formations/new/", views.FormationCreateView.as_view(), name="formation_new"),
    path("formations/<int:pk>/edit/", views.FormationUpdateView.as_view(), name="formation_edit"),
    path("formations/<int:pk>/delete/", views.FormationDeleteView.as_view(), name="formation_delete"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
