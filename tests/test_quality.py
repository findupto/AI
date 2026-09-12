from evaluation.quality import evaluate_responses, score_response


def test_score_response_reports_basic_signals():
    result = score_response("hello local AI", min_length=5)
    assert result["non_empty"] is True
    assert result["minimum_length"] is True
    assert result["words"] == 3


def test_evaluate_responses_aggregates_pass_rate():
    result = evaluate_responses(["ok", "", "long enough"], min_length=2)
    assert result["count"] == 3
    assert result["passed"] == 2
    assert result["pass_rate"] == 2 / 3
