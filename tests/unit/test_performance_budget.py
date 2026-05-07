from src.utils.metrics import PerformanceBudget


def test_performance_budget_passes_when_within_limits():
    assert PerformanceBudget(target_fps=20, memory_growth_mb_limit=10).evaluate(25, 100, 105) == []


def test_performance_budget_reports_threshold_warnings():
    warnings = PerformanceBudget(target_fps=20, memory_growth_mb_limit=10).evaluate(10, 100, 120)
    assert len(warnings) == 2
