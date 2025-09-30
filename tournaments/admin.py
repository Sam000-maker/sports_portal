# # tournaments/admin.py
# from django.contrib import admin
# from .models import Tournament, TournamentTeam, Match, Lineup, LineupEntry


# @admin.register(Tournament)
# class TournamentAdmin(admin.ModelAdmin):
#     list_display = ("name", "sport", "ttype", "start_date", "end_date", "is_active")
#     list_filter = ("sport", "ttype", "is_active", "start_date")
#     search_fields = ("name", "sport__name")
#     autocomplete_fields = ("sport", "created_by")


# @admin.register(TournamentTeam)
# class TournamentTeamAdmin(admin.ModelAdmin):
#     list_display = ("tournament", "team", "seed")
#     list_filter = ("tournament",)
#     search_fields = ("tournament__name", "team__name")
#     autocomplete_fields = ("tournament", "team")


# @admin.register(Match)
# class MatchAdmin(admin.ModelAdmin):
#     list_display = ("tournament", "round_no", "group_label", "team_a", "team_b", "scheduled_at", "venue", "status")
#     list_filter = ("tournament", "round_no", "group_label", "status", "venue")
#     search_fields = ("tournament__name", "team_a__name", "team_b__name")
#     autocomplete_fields = ("tournament", "team_a", "team_b", "venue")


# class LineupEntryInline(admin.TabularInline):
#     model = LineupEntry
#     extra = 0
#     autocomplete_fields = ("user", "position")


# @admin.register(Lineup)
# class LineupAdmin(admin.ModelAdmin):
#     list_display = ("match", "team")
#     inlines = [LineupEntryInline]
#     autocomplete_fields = ("match", "team")


# @admin.register(LineupEntry)
# class LineupEntryAdmin(admin.ModelAdmin):
#     list_display = ("lineup", "user", "position", "is_bench")
#     list_filter = ("is_bench", "position")
#     search_fields = ("user__first_name", "user__last_name", "position__code")
#     autocomplete_fields = ("lineup", "user", "position")
