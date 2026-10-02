from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'v2/results/week_04_adversarial_review.json'
FOUR = ROOT / 'v2/results/week_04_four_source_contradiction_layer.json'
MODEL = ROOT / 'v2/results/week_04_friday_model_layer.json'


def main() -> None:
    review = json.loads(REVIEW.read_text(encoding='utf-8'))
    four = json.loads(FOUR.read_text(encoding='utf-8'))
    model = json.loads(MODEL.read_text(encoding='utf-8'))

    assert review['status'] == 'STEP_7_COMPLETE_INPUT'
    assert review['review_policy']['no_probability_mutation'] is True
    assert review['review_policy']['no_external_source_weighting'] is True
    assert review['review_policy']['no_week3_result_chasing'] is True
    assert len(review['lenses']) == 7
    assert len(review['game_reviews']) == 15

    review_ids = {g['game_id'] for g in review['game_reviews']}
    four_ids = {g['game_id'] for g in four['games']}
    model_ids = {g['game_id'] for g in model['games']}
    assert review_ids == four_ids == model_ids

    summary = review['board_summary']
    assert summary['conditional_candidates'] == ['HOU -3', 'SEA -7']
    assert summary['high_priority_watch'] == ['IND -3.5']
    assert summary['aggressive_friday_stakes_supported'] is False
    assert summary['verified_multi_source_consensus_games'] == 0

    by_id = {g['game_id']: g for g in review['game_reviews']}
    assert by_id['DAL @ HOU']['friday_disposition'] == 'CONDITIONAL_CANDIDATE'
    assert by_id['LAC @ SEA']['friday_disposition'] == 'CONDITIONAL_CANDIDATE'
    assert by_id['IND @ WAS']['friday_disposition'] == 'HIGH_PRIORITY_WATCH'
    assert by_id['NE @ BUF']['friday_disposition'] == 'HOLD_SOURCE_DISPUTED'
    assert by_id['DEN @ SF']['friday_disposition'] == 'HOLD_SOURCE_DISPUTED'

    # Ensure the adversarial layer does not invent source consensus.
    assert four['summary']['verified_four_source_consensus_games'] == 0
    assert set(four['summary']['model_robust_takes']) == {'HOU -3', 'SEA -7'}

    # The review is diagnostic only; it cannot mutate the frozen model artifact.
    assert model['model_version'] == 'V2-0006C-global-hybrid-r1'
    print('Week 4 adversarial QA passed: 15 games, 7 lenses, no probability mutation, no fake consensus.')


if __name__ == '__main__':
    main()
