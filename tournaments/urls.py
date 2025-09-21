from django.urls import path
from . import views

app_name = "tournaments"

urlpatterns = [
    path("", views.TournamentListView.as_view(), name="tournament_list"),
    path("new/", views.TournamentCreateView.as_view(), name="tournament_new"),

    path("<int:pk>/", views.TournamentDetailView.as_view(), name="tournament_detail"),
    path("<int:pk>/edit/", views.TournamentUpdateView.as_view(), name="tournament_edit"),
    path("<int:pk>/delete/", views.TournamentDeleteView.as_view(), name="tournament_delete"),

    path("<int:pk>/teams/add/", views.TournamentTeamAddView.as_view(), name="tournament_team_add"),
    path("<int:pk>/teams/<int:tt_id>/remove/", views.TournamentTeamRemoveView.as_view(), name="tournament_team_remove"),

    path("<int:pk>/generate/", views.TournamentGenerateFixturesView.as_view(), name="tournament_generate"),

    # Matches
    path("matches/<int:pk>/schedule/", views.MatchScheduleView.as_view(), name="match_schedule"),
    path("matches/<int:pk>/result/", views.ResultUpdateView.as_view(), name="match_result"),
    path("matches/<int:pk>/delete/", views.MatchDeleteView.as_view(), name="match_delete"),

    # Lineups
    path("matches/<int:match_id>/lineup/<str:side>/", views.LineupBuildView.as_view(), name="lineup_build"),
    path("matches/<int:match_id>/lineup/entry/<int:entry_id>/remove/", views.LineupEntryRemoveView.as_view(), name="lineup_entry_remove"),
]
