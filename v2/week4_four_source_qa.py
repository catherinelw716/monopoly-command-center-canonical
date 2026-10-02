from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYER = ROOT / 'v2/results/week_04_four_source_contradiction_layer.json'
MODEL = ROOT / 'v2/results/week_04_friday_model_layer.json'
CTX = ROOT / 'v2/season_2026/week_04_context_research_2026-10-02_1551ET.json'


def main() -> None:
    layer = json.loads(LAYER.read_text(encoding='utf-8'))
    model = json.loads(MODEL.read_text(encoding='utf-8'))
    ctx = json.loads(CTX.read_text(encoding='utf-8'))

    games = layer['games']
    assert len(games) == 15
    layer_ids = {g['game_id'] for g in games}
    assert layer_ids == {g['game_id'] for g in model['games']}
    assert layer_ids == {g['game_id'] for g in ctx['games']}

    # No fake consensus: unavailable external ATS sources cannot count as votes.
    assert layer['summary']['verified_four_source_consensus_games'] == 0
    assert layer['summary']['games_with_any_verified_ats_vote'] == 2

    by_id = {g['game_id']: g for g in games}
    assert by_id['DAL @ HOU']['our_model']['side'] == 'HOU -3'
    assert by_id['LAC @ SEA']['our_model']['side'] == 'SEA -7'
    assert by_id['DAL @ HOU']['verified_ats_votes'] == 1
    assert by_id['LAC @ SEA']['verified_ats_votes'] == 1

    for gid in ('NE @ BUF', 'DEN @ SF', 'IND @ WAS'):
        assert by_id[gid]['our_model']['state'] == 'SOURCE_DISPUTED_DIRECTION'
        assert by_id[gid]['our_model']['side'] is None
        assert 'MARKET_SOURCE_DIRECTION_CONFLICT' in by_id[gid]['contradiction_flags']

    for g in games:
        assert g['verified_consensus'] == 'INCOMPLETE_EVIDENCE'
        assert g['sportsline']['side'] is None
        assert g['gridiron']['side'] is None
        assert g['lucas']['side'] is None
        assert g['verified_ats_votes'] in (0, 1)

    # Major contextual facts should survive synthesis without becoming ATS votes.
    assert 'MAJOR_QB_NEWS_ALREADY_PRICED' in by_id['GB @ TB']['contradiction_flags']
    assert 'CONTEXT_TILTS_IND_BUT_NOT_A_VOTE' in by_id['IND @ WAS']['contradiction_flags']
    assert 'MODEL_CONTEXT_ALIGNMENT_SEA' in by_id['LAC @ SEA']['contradiction_flags']

    print('Week 4 four-source QA passed: 15/15 games; no fabricated consensus.')


if __name__ == '__main__':
    main()
