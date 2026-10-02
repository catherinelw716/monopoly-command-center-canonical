"""Deterministic QA for Week 4 adaptive-state policy.

Ensures Weeks 1-3 learnings change evaluation/execution/optimizer stress behavior
without silently retuning the frozen Week 4 NFL probability model.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "v2/season_2026/week_04_adaptive_state.json"


def main() -> None:
    d = json.loads(STATE.read_text(encoding="utf-8"))
    assert d["season"] == 2026 and d["week"] == 4
    assert d["status"] == "STEP_4_ADAPTIVE_STATE"

    p = d["probability_model_policy"]
    assert p["frozen_model_version"] == "V2-0006C-global-hybrid-r1"
    assert p["retrain_for_week4"] is False
    assert p["week3_11_3_used_as_retuning_signal"] is False

    src = d["prospective_evidence"]["external_sources"]
    for key in ("sportsline_exact_ats", "gridiron_exact_sly_directional_non_50_50", "lucas_all_takes"):
        assert src[key]["prediction_weight"] == 0.0
    assert src["sportsline_exact_ats"]["wins"] == 4 and src["sportsline_exact_ats"]["losses"] == 4
    assert src["gridiron_exact_sly_directional_non_50_50"]["wins"] == 4
    assert src["lucas_all_takes"]["wins"] == 2 and src["lucas_all_takes"]["losses"] == 5

    hist = d["household_execution_history"]
    assert hist["week1"]["household_outlay"] == 6100
    assert hist["week2"]["household_outlay"] == 7800
    assert hist["week3"]["household_outlay"] == 6600
    assert hist["week3"]["aligned_with_final_model"]["net"] == 1500
    assert hist["week3"]["opposed_to_final_model"]["net"] == -3700

    mp = d["market_edge_policy"]["week4_step3_mapping"]
    assert set(mp["SOURCE_SENSITIVE"]) == {"DAL @ HOU", "LAC @ SEA"}
    assert set(mp["SOURCE_DISPUTED"]) == {"NE @ BUF", "DEN @ SF", "IND @ WAS"}
    assert len(mp["MARKET_EQUAL"]) == 10
    all_games = mp["SOURCE_SENSITIVE"] + mp["SOURCE_DISPUTED"] + mp["MARKET_EQUAL"]
    assert len(all_games) == 15 and len(set(all_games)) == 15

    rec = d["decision_reconciliation_policy"]
    assert rec["blocking_error"] == "LINE_MISMATCH"
    assert set(rec["statuses"]) == {"ALIGNED", "OVERRIDE", "LINE_MISMATCH"}
    assert set(rec["override_requirements"]) == {"reason", "source_or_evidence", "timestamp"}

    opt = d["optimizer_adaptation"]
    assert opt["probability_stress_factors"] == [1.0, 0.75, 0.5, 0.25]
    assert len(opt["additional_week4_stress_tests"]) >= 4

    legacy = d["legacy_heuristic_policy"]
    assert legacy["v1_week4_rebuild_status"] == "NOT_REPRODUCIBLE_FROM_REPO"
    assert legacy["m1_m5_week4_rebuild_status"] == "NOT_REPRODUCIBLE_FROM_REPO"

    print("Week 4 adaptive-state QA passed: frozen model preserved, source weights zero, execution/optimizer learnings encoded.")


if __name__ == "__main__":
    main()
