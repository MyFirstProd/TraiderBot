from app.indicators.ma import EMA, SMA, WMA
from app.indicators.rsi import RSI


def test_moving_averages_compute():
    values = [1, 2, 3, 4, 5]
    assert SMA(3).compute(values)[-1] == 4
    assert round(EMA(3).compute(values)[-1], 4) > 3
    assert round(WMA(3).compute(values)[-1], 4) == round((3 + 8 + 15) / 6, 4)


def test_rsi_output_range():
    values = [1, 2, 3, 2, 4, 5, 4, 6, 7, 6, 8, 7, 9, 10, 11]
    current = RSI(14).compute(values)[-1]
    assert current is not None
    assert 0 <= current <= 100
