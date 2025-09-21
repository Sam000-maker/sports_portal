from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional

from .models import Tournament, TournamentTeam, Match

@dataclass
class Pair:
    a: int
    b: int

def _round_robin_pairs(team_ids: List[int]) -> List[List[Pair]]:
    """Circle method. Adds BYE if odd."""
    ids = list(team_ids)
    bye = None
    if len(ids) % 2 == 1:
        ids.append(-1)  # BYE mark
        bye = -1
    n = len(ids)
    rounds = []
    for r in range(n - 1):
        pairs = []
        for i in range(n // 2):
            t1 = ids[i]
            t2 = ids[n - 1 - i]
            if t1 != bye and t2 != bye:
                pairs.append(Pair(t1, t2))
        rounds.append(pairs)
        ids = [ids[0]] + [ids[-1]] + ids[1:-1]  # rotate
    return rounds

def generate_fixtures(t: Tournament) -> None:
    """
    Creates Match rows for the tournament. Idempotent enough for first use.
    Round Robin: circle method
    Single Elim: simple seeding 1 vs N
    Groups+KO: minimal group builder (even split), then RR in groups
    """
    teams = list(TournamentTeam.objects.filter(tournament=t).order_by("seed", "team__name").values_list("team_id", flat=True))
    if len(teams) < 2:
        return

    if t.ttype == Tournament.Type.ROUND_ROBIN:
        rounds = _round_robin_pairs(teams)
        for rno, pairs in enumerate(rounds, start=1):
            for p in pairs:
                Match.objects.get_or_create(tournament=t, round_no=rno, team_a_id=p.a, team_b_id=p.b)

    elif t.ttype == Tournament.Type.SINGLE_ELIM:
        # Basic bracket: 1 vs N, 2 vs N-1, ...
        ordered = teams
        N = len(ordered)
        for i in range(N // 2):
            a = ordered[i]
            b = ordered[N - 1 - i]
            Match.objects.get_or_create(tournament=t, round_no=1, team_a_id=a, team_b_id=b)
        # Next rounds will be created later after results, or you can pre-create placeholders.

    else:  # GROUPS_KO
        # Minimal grouping: split into 2 groups A/B, then round robin inside
        half = (len(teams) + 1) // 2
        groups = [("A", teams[:half]), ("B", teams[half:])]
        for label, members in groups:
            rounds = _round_robin_pairs(members)
            for rno, pairs in enumerate(rounds, start=1):
                for p in pairs:
                    Match.objects.get_or_create(tournament=t, round_no=rno, group_label=label, team_a_id=p.a, team_b_id=p.b)
