from pre_submit_reconciliation import reconcile


def base_freeze():
    return {
        "season": 2026,
        "week": 4,
        "freeze_type": "SLY_FRIDAY_FREEZE_INPUT",
        "games": [
            {"game": "AAA @ BBB", "sly_pick_display": "BBB -3", "sly_home_spread": -3.0},
            {"game": "CCC @ DDD", "sly_pick_display": "CCC +2.5", "sly_home_spread": -2.5},
        ],
    }


def base_model():
    return {
        "recommendations": [
            {"game": "AAA @ BBB", "pick": "BBB -3", "rank": 1, "grade": "A"},
            {"game": "CCC @ DDD", "pick": "DDD -2.5", "rank": 2, "grade": "B+"},
        ]
    }


def test_aligned_passes():
    p = {"entries": {"Catherine": [{"game": "AAA @ BBB", "pick": "BBB -3", "amount": 500, "sly_home_spread": -3.0}]}}
    r = reconcile(base_freeze(), base_model(), p)
    assert r["status"] == "PASS"
    assert r["summary"]["aligned"] == 1


def test_override_requires_reason_and_timestamp():
    p = {"entries": {"Amanda": [{"game": "AAA @ BBB", "pick": "AAA +3", "amount": 500}]}}
    r = reconcile(base_freeze(), base_model(), p)
    assert r["status"] == "BLOCK"
    assert r["summary"]["overrides"] == 1


def test_documented_override_passes():
    p = {"entries": {"Amanda": [{"game": "AAA @ BBB", "pick": "AAA +3", "amount": 500, "override_reason": "Late verified QB scratch changes contextual judgment; probability model remains frozen.", "override_timestamp": "2026-10-04T12:20:00-04:00"}]}}
    r = reconcile(base_freeze(), base_model(), p)
    assert r["status"] == "PASS"
    assert r["rows"][0]["status"] == "OVERRIDE"


def test_line_mismatch_blocks():
    p = {"entries": {"Catherine": [{"game": "AAA @ BBB", "pick": "BBB -3", "amount": 500, "sly_home_spread": -2.5}]}}
    r = reconcile(base_freeze(), base_model(), p)
    assert r["status"] == "BLOCK"
    assert r["summary"]["line_mismatches"] == 1


def test_unknown_game_blocks():
    p = {"entries": {"Catherine": [{"game": "EEE @ FFF", "pick": "EEE +3", "amount": 100}]}}
    r = reconcile(base_freeze(), base_model(), p)
    assert r["status"] == "BLOCK"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS: {len(tests)} pre-submit reconciliation QA checks")
