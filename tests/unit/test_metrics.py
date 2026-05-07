from src.utils.metrics import FpsCounter, PerformanceBudget, object_count


def test_fps_counter_calculates_window_rate():
    counter = FpsCounter(window=3)
    counter.tick(0.0)
    counter.tick(0.5)
    assert counter.tick(1.0) == 2.0


def test_object_count_matches_detections():
    assert object_count([object(), object()]) == 2


def test_performance_budget_warnings():
    budget = PerformanceBudget(target_fps=20, memory_growth_mb_limit=10)
    warnings = budget.evaluate(fps=15, memory_start_mb=100, memory_current_mb=115)
    assert any("fps below target" in warning for warning in warnings)
    assert any("memory growth" in warning for warning in warnings)
