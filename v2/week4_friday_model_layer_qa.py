from __future__ import annotations

import json
from pathlib import Path

from run_week4_friday_model_layer import build

HISTORY = Path('v2/season_2026/week_04_market_history_2026-10-02_1433ET.json')
ARTIFACT = Path('v2/model_artifacts/v2_global_hybrid_2016_2025.json')
RESULT = Path('v2/results/week_04_friday_model_layer.json')

expected = json.loads(RESULT.read_text())
actual = build(HISTORY, ARTIFACT)
assert actual == expected, 'checked-in Week 4 model layer does not reproduce from frozen inputs'
assert len(actual['games']) == 15
by_game = {g['game_id']: g for g in actual['games']}

assert by_game['DAL @ HOU']['state'] == 'SOURCE_SENSITIVE_SAME_DIRECTION'
assert by_game['DAL @ HOU']['robust_side'] == 'HOU'
assert by_game['LAC @ SEA']['state'] == 'SOURCE_SENSITIVE_SAME_DIRECTION'
assert by_game['LAC @ SEA']['robust_side'] == 'SEA'
assert by_game['NE @ BUF']['state'] == 'SOURCE_DISPUTED_DIRECTION'
assert by_game['DEN @ SF']['state'] == 'SOURCE_DISPUTED_DIRECTION'
assert by_game['IND @ WAS']['state'] == 'SOURCE_DISPUTED_DIRECTION'

# Exact integer Sly lines must preserve non-zero push probability.
assert by_game['NE @ BUF']['vi']['p_push'] > 0
assert by_game['DAL @ HOU']['vi']['p_push'] > 0
assert by_game['DEN @ SF']['vi']['p_push'] > 0
assert by_game['LAC @ SEA']['vi']['p_push'] > 0

# Equal-market rows are diagnostics, not promoted price edges.
for g in actual['games']:
    if g['state'] == 'MARKET_EQUAL':
        assert g['robust_side'] is None
        assert g['vi_market_home_spread'] == g['sly_home_spread']
        assert g['action_market_home_spread'] == g['sly_home_spread']

assert actual['artifact_hash'] == 'da2b587b06a91d05834a92ed5d2dc6cc42ba7d38069d8d0e7f73b94a71617026'
print('Week 4 Friday model-layer QA passed: 15 games, frozen artifact, source sensitivity preserved.')
