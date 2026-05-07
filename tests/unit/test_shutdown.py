from src.utils.shutdown import ShutdownController


def test_shutdown_request_sets_state():
    controller = ShutdownController()
    assert not controller.requested
    controller.request()
    assert controller.requested


def test_exit_key_requests_shutdown():
    controller = ShutdownController()
    assert controller.check_key(ord("q"), "q")
    assert controller.requested
