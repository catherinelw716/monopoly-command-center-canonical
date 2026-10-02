from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CTX = ROOT / 'v2/season_2026/week_04_context_research_2026-10-02_1551ET.json'
SLY = ROOT / 'v2/season_2026/week_04_sly_freeze.json'


def main() -> None:
    ctx = json.loads(CTX.read_text(encoding='utf-8'))
    sly = json.loads(SLY.read_text(encoding='utf-8'))
    games = ctx['games']
    sly_ids = {g['game'] for g in sly['games']}
    ctx_ids = {g['game_id'] for g in games}
    assert len(games) == 15
    assert ctx_ids == sly_ids
    assert ctx['completeness']['games_with_injury_context'] == 15
    assert ctx['completeness']['games_with_qb_status'] == 15
    assert ctx['completeness']['games_with_weather_context'] == 15
    assert ctx['completeness']['games_with_weather_materiality'] == 15

    allowed_ext = {'UNVERIFIED', 'NOT_PUBLICLY_AVAILABLE'}
    for g in games:
        assert g['injury_context']
        assert g['qb_status']
        assert g['weather_context']
        assert g['weather_materiality']
        assert isinstance(g['context_flags'], list)
        assert g['sportsline_public']
        assert g['gridiron'] in allowed_ext
        assert g['lucas'] in allowed_ext

    # Guard against accidentally presenting inaccessible source picks as verified.
    availability = ctx['external_source_availability']
    assert availability['SportsLine']['status'] == 'PARTIAL_PUBLIC_ONLY'
    assert availability['Gridiron']['status'] == 'UNVERIFIED_PUBLIC_WEEK4_PICKSET'
    assert availability['Lucas']['status'] == 'NOT_PUBLICLY_AVAILABLE'
    assert ctx['completeness']['sportsline_full_ATS_publicly_verified'] == 0
    assert ctx['completeness']['gridiron_week4_pickset_publicly_verified'] == 0
    assert ctx['completeness']['lucas_week4_pickset_verified'] == 0

    # High-impact Friday facts that Step 6 must not drop.
    by_id = {g['game_id']: g for g in games}
    assert 'WAS_STARTING_QB_OUT' in by_id['IND @ WAS']['context_flags']
    assert 'TB_BACKUP_QB' in by_id['GB @ TB']['context_flags']
    assert 'NYJ_MULTIPLE_OFFENSIVE_STARTERS_OUT' in by_id['NYJ @ CHI']['context_flags']
    assert 'CAR_TWO_STARTERS_OUT' in by_id['DET @ CAR']['context_flags']
    assert 'SF_HEAVY_INJURY_VOLUME' in by_id['DEN @ SF']['context_flags']
    assert 'MIN_JEFFERSON_OUT' in by_id['MIA @ MIN']['context_flags']

    print('Week 4 external-context QA passed: 15/15 games; unverified source picks remain explicit.')


if __name__ == '__main__':
    main()
