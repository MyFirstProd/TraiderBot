from app.risk.manager import RiskManager


def test_risk_manager_rejects_open_circuit():
    manager = RiskManager()
    manager.circuit_breaker_open = True
    decision = manager.evaluate(
        should_trade=True,
        symbol="BTCUSDT",
        equity=10000,
        price=100,
        stop_distance=1,
        spread_bps=2,
        open_positions=0,
        total_exposure=0,
    )
    assert not decision.approved
    assert decision.reason == "circuit_breaker_open"
