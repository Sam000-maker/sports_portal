# tournaments/services.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from django.db import transaction

from .models import Tournament, TournamentTeam, Match


@dataclass(frozen=True)
class Pair:
    a: int
    b: int


def _round_robin_pairs(team_ids: List[int]) -> List[List[Pair]]:
    """Circle method with BYE support. Returns list of rounds, each a list of Pair."""
    ids = list(team_ids)
    bye = None
    if len(ids) % 2 == 1:
        ids.append(-1)
        bye = -1
    n = len(ids)
    rounds: List[List[Pair]] = []
    for _ in range(n - 1):
        pairs: List[Pair] = []
        for i in range(n // 2):
            t1 = ids[i]
            t2 = ids[n - 1 - i]
            if t1 != bye and t2 != bye:
                pairs.append(Pair(t1, t2))
        rounds.append(pairs)
        # keep first fixed, rotate the rest right by one
        ids = [ids[0]] + ids[-1:] + ids[1:-1]
    return rounds


@transaction.atomic
def generate_fixtures(t: Tournament) -> None:
    """
    Create Match rows for the tournament.
    - Round Robin: circle method
    - Single Elim: 1 vs N, 2 vs N-1 (odd N -> last seed gets a bye)
    - Groups+KO: even split into A/B, then RR inside groups (KO not auto-built here)
    """
    teams = list(
        TournamentTeam.objects.filter(tournament=t)
        .order_by("seed", "team__name")
        .values_list("team_id", flat=True)
    )
    if len(teams) < 2:
        return

    if t.ttype == Tournament.Type.ROUND_ROBIN:
        rounds = _round_robin_pairs(teams)
        for rno, pairs in enumerate(rounds, start=1):
            for p in pairs:
                Match.objects.get_or_create(tournament=t, round_no=rno, team_a_id=p.a, team_b_id=p.b)

    elif t.ttype == Tournament.Type.SINGLE_ELIM:
        N = len(teams)
        limit = N // 2
        for i in range(limit):
            a = teams[i]
            b = teams[N - 1 - i]
            Match.objects.get_or_create(tournament=t, round_no=1, team_a_id=a, team_b_id=b)
        # bye auto-advances; later rounds can be created after results

    else:  # GROUPS_KO
        half = (len(teams) + 1) // 2
        groups = [("A", teams[:half]), ("B", teams[half:])]
        for label, members in groups:
            if len(members) < 2:
                continue
            rounds = _round_robin_pairs(members)
            for rno, pairs in enumerate(rounds, start=1):
                for p in pairs:
                    Match.objects.get_or_create(
                        tournament=t, round_no=rno, group_label=label, team_a_id=p.a, team_b_id=p.b
                    )
