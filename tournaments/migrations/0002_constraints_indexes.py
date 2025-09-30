# tournaments/migrations/0002_constraints_indexes.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tournaments", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="tournament",
            constraint=models.UniqueConstraint(
                fields=("name", "sport", "start_date"),
                name="uniq_tournament_name_sport_start",
            ),
        ),
        migrations.AddIndex(
            model_name="tournamentteam",
            index=models.Index(fields=["tournament", "seed"], name="tt_tournament_seed_idx"),
        ),
        migrations.AddConstraint(
            model_name="match",
            constraint=models.CheckConstraint(
                check=~models.Q(team_a=models.F("team_b")),
                name="match_teams_distinct",
            ),
        ),
        migrations.AddConstraint(
            model_name="match",
            constraint=models.UniqueConstraint(
                fields=("tournament", "round_no", "group_label", "team_a", "team_b"),
                name="uniq_match_per_round_group",
            ),
        ),
        migrations.AddIndex(
            model_name="match",
            index=models.Index(fields=["tournament", "round_no"], name="match_t_round_idx"),
        ),
        migrations.AddIndex(
            model_name="match",
            index=models.Index(fields=["tournament", "group_label"], name="match_t_group_idx"),
        ),
        migrations.AddIndex(
            model_name="match",
            index=models.Index(fields=["scheduled_at"], name="match_scheduled_idx"),
        ),
    ]
