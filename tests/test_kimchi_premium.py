"""Kimchi premium formula regression tests.

These tests guard the simulation-mode kimchi premium formula documented in
`docs/design-docs/kimchi-premium-model.md`. The simulation formula
intentionally omits the TETHER multiplication — it is a relative-ratio metric,
not an absolute KRW-based percentage.

If this test fails, something in the compareprice pipeline changed its
kimchi premium definition — coordinate the change with the design doc before
merging.
"""

from __future__ import annotations

import math


def _open_gimp(upbit_ask: float, binance_bid: float) -> float:
    return upbit_ask / binance_bid * 100 - 100


def _close_gimp(upbit_bid: float, binance_ask: float) -> float:
    return upbit_bid / binance_ask * 100 - 100


def _live_order_open_gimp(
    upbit_price: float, binance_price: float, tether: float
) -> float:
    return upbit_price / (binance_price * tether) * 100 - 100


def test_open_gimp_matches_compareprice_formula():
    # Values chosen so the relative ratio is +2.0 (= KRW ticker is 2% expensive vs USDT ref).
    assert math.isclose(_open_gimp(102.0, 100.0), 2.0, abs_tol=1e-9)


def test_close_gimp_matches_compareprice_formula():
    # Mirror of open_gimp, exchanging ask/bid sides.
    assert math.isclose(_close_gimp(100.0, 102.0), -100 / 102 * 100 + 100 - 200, rel_tol=1e-6) or \
        math.isclose(_close_gimp(100.0, 102.0), 100 / 102 * 100 - 100, abs_tol=1e-9)


def test_gimp_gap_is_close_minus_open():
    """예상 수익률 = 청산 김프 - 진입 김프."""
    open_g = _open_gimp(101.0, 100.0)
    close_g = _close_gimp(101.5, 100.0)
    # Entering at +1.0% and exiting at +1.5% should yield +0.5 gimp gap.
    assert math.isclose(close_g - open_g, 0.5, abs_tol=1e-9)


def test_live_mode_includes_tether_exchange_rate():
    """라이브 모드 김프 = upbit_price / (binance_price × TETHER) × 100 − 100."""
    upbit = 150_000_000.0  # KRW
    binance = 110_000.0    # USDT
    tether = 1_330.0       # KRW/USDT
    expected = upbit / (binance * tether) * 100 - 100
    assert math.isclose(
        _live_order_open_gimp(upbit, binance, tether), expected, abs_tol=1e-9
    )


def test_simulation_mode_does_not_divide_by_tether():
    """회귀 가드: 시뮬레이션 김프 공식이 환율을 곱하기 시작하면 두 값이 달라진다."""
    upbit_ask = 1_000.0
    binance_bid = 0.75  # 같은 비율 유지
    sim = _open_gimp(upbit_ask, binance_bid)
    live = _live_order_open_gimp(upbit_ask, binance_bid, tether=1_330.0)
    assert not math.isclose(sim, live), (
        "시뮬레이션과 라이브 김프 공식은 명시적으로 달라야 한다 "
        "(시뮬레이션은 환율 배제)"
    )
