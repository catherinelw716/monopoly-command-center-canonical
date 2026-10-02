from __future__ import annotations

import argparse
import json
from pathlib import Path

from shadow_model import ShadowModel

DEFAULT_HISTORY = Path('v2/season_2026/week_04_market_history_2026-10-02_1433ET.json')
DEFAULT_ARTIFACT = Path('v2/model_artifacts/v2_global_hybrid_2016_2025.json')
DEFAULT_OUTPUT = Path('v2/results/week_04_friday_model_layer.json')


def _side_eval(model: ShadowModel, market_home_spread: float, sly_home_spread: float, away: str, home: str) -> dict:
    p = model.predict(market_home_spread, sly_home_spread)['hybrid']
    home_cover = float(p['p_home_cover'])
    away_cover = float(p['p_away_cover'])
    push = float(p['p_push'])
    if home_cover >= away_cover:
        team = home
        spread = sly_home_spread
        win = home_cover
        loss = float(p['p_home_loss'])
    else:
        team = away
        spread = -sly_home_spread
        win = away_cover
        loss = float(p['p_away_loss'])
    return {
        'side': team,
        'sly_spread': float(spread),
        'p_cover': round(win, 6),
        'p_push': round(push, 6),
        'p_loss': round(loss, 6),
        'edge': round(win - loss, 6),
    }


def build(history_path: Path, artifact_path: Path) -> dict:
    h = json.loads(history_path.read_text())
    model = ShadowModel.load(artifact_path)
    rows = []
    for g in h['games']:
        away = g['away_team']
        home = g['home_team']
        sly = float(g['sly_home_spread'])
        opn = float(g['open_home_spread'])
        vi = float(g['vi_current_home_spread'])
        action = float(g['action_current_home_spread'])
        vi_eval = _side_eval(model, vi, sly, away, home)
        action_eval = _side_eval(model, action, sly, away, home)
        open_eval = _side_eval(model, opn, sly, away, home)
        if vi == sly and action == sly:
            state = 'MARKET_EQUAL'
            robust = None
        elif vi_eval['side'] == action_eval['side']:
            state = 'SOURCE_SENSITIVE_SAME_DIRECTION'
            robust = vi_eval['side']
        else:
            state = 'SOURCE_DISPUTED_DIRECTION'
            robust = None
        rows.append({
            'game_id': g['game_id'],
            'open_home_spread': opn,
            'sly_home_spread': sly,
            'vi_market_home_spread': vi,
            'action_market_home_spread': action,
            'vi': vi_eval,
            'action': action_eval,
            'open_diagnostic': open_eval,
            'state': state,
            'robust_side': robust,
        })
    return {
        'season': 2026,
        'week': 4,
        'snapshot_type': 'FRIDAY_MODEL_LAYER',
        'generated_from': str(history_path),
        'model_version': model.model_version,
        'artifact_hash': model.artifact_hash,
        'policy_notes': [
            'Frozen prospective model; no Week 1-3 refit.',
            'Equal-market residual direction is diagnostic only, not a material edge.',
            'Opening-anchor outputs are movement diagnostics only.',
            'Source-specific current lines are preserved; no synthetic consensus.',
        ],
        'games': rows,
        'summary': {
            'market_equal': [x['game_id'] for x in rows if x['state'] == 'MARKET_EQUAL'],
            'source_sensitive_same_direction': [
                {'game_id': x['game_id'], 'side': x['robust_side']}
                for x in rows if x['state'] == 'SOURCE_SENSITIVE_SAME_DIRECTION'
            ],
            'source_disputed_direction': [x['game_id'] for x in rows if x['state'] == 'SOURCE_DISPUTED_DIRECTION'],
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--history', type=Path, default=DEFAULT_HISTORY)
    ap.add_argument('--artifact', type=Path, default=DEFAULT_ARTIFACT)
    ap.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()
    out = build(args.history, args.artifact)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out['summary'], indent=2))


if __name__ == '__main__':
    main()
