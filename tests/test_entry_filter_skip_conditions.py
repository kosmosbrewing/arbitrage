"""Entry filter skip-condition regression tests.

These tests do NOT exercise the async function in compareprice/. Instead they
lock in the skip-condition truth tables that the entry filter chain relies on.
If any of these assertions flip, `docs/design-docs/entry-filter-chain.md` and
the compareprice/comparePriceOpenOrder.py should be reconciled in the same PR.
"""

from __future__ import annotations

import math

CURR_GIMP_GAP = 0.2  # consts.py — 진입 스프레드 허용 한도
BTC_ANCHOR_GAP = 0.75  # comparePriceOpenOrder.py:85 hardcoded
RSI_OVERSOLD = 35
RSI_OVERBOUGHT = 65


def should_skip_due_to_negative_balance(balance: float) -> bool:
    # comparePriceOpenOrder.py:64
    return balance < 0


def should_skip_due_to_spread(open_gimp: float, close_gimp: float) -> bool:
    # comparePriceOpenOrder.py:82
    return (open_gimp - close_gimp) > CURR_GIMP_GAP


def should_skip_due_to_btc_anchor(btc_open_gimp: float, open_gimp: float) -> bool:
    # comparePriceOpenOrder.py:85 — BTC 괴리 과대 시 스킵
    return btc_open_gimp < (open_gimp - BTC_ANCHOR_GAP)


def is_rsi_4h_oversold(upbit_rsi: float, binance_rsi: float) -> bool:
    # 양쪽 모두 35 이하일 때만 과매도 스킵 (compareprice line 97)
    return upbit_rsi <= RSI_OVERSOLD and binance_rsi <= RSI_OVERSOLD


def is_rsi_4h_overbought(upbit_rsi: float, binance_rsi: float) -> bool:
    # 양쪽 모두 65 이상일 때만 과매수 분기 (compareprice line 102)
    return upbit_rsi >= RSI_OVERBOUGHT and binance_rsi >= RSI_OVERBOUGHT


def test_negative_balance_triggers_skip():
    assert should_skip_due_to_negative_balance(-1)
    assert not should_skip_due_to_negative_balance(0)
    assert not should_skip_due_to_negative_balance(1_000_000)


def test_spread_skip_uses_curr_gimp_gap_threshold():
    # Spread of 0.21 > 0.2 → skip
    assert should_skip_due_to_spread(open_gimp=2.0, close_gimp=1.79)
    # Spread of 0.1 < 0.2 → pass
    assert not should_skip_due_to_spread(open_gimp=2.0, close_gimp=1.9)
    # Exactly at threshold is still pass (strict `>`)
    assert not should_skip_due_to_spread(open_gimp=2.0, close_gimp=1.8)


def test_btc_anchor_skip_when_ticker_gimp_exceeds_btc_by_075():
    # Ticker at 2.0, BTC at 1.2 → diff 0.8 > 0.75 → skip
    assert should_skip_due_to_btc_anchor(btc_open_gimp=1.2, open_gimp=2.0)
    # Ticker at 2.0, BTC at 1.3 → diff 0.7 < 0.75 → pass
    assert not should_skip_due_to_btc_anchor(btc_open_gimp=1.3, open_gimp=2.0)
    # Strict `<` — exactly 0.75 gap passes.
    assert not should_skip_due_to_btc_anchor(btc_open_gimp=1.25, open_gimp=2.0)


def test_rsi_4h_oversold_requires_both_exchanges():
    # 양쪽 모두 저 RSI → 과매도 판정
    assert is_rsi_4h_oversold(30, 32)
    # 한쪽만 저 RSI → 과매도 아님 (entry-filter-chain.md 핵심 수정사항)
    assert not is_rsi_4h_oversold(30, 40)
    assert not is_rsi_4h_oversold(40, 30)


def test_rsi_4h_overbought_threshold_is_65_not_70():
    """TD 회귀 가드: 이전 문서 버그 — 70으로 잘못 기재되어 있었음."""
    assert is_rsi_4h_overbought(65, 66)  # 양쪽 65↑ → 과매수 분기 진입
    assert not is_rsi_4h_overbought(64, 70)  # 한쪽만 → 진입 안 함
    # 70 임계값이 아니라는 것을 명시적으로 검증
    assert is_rsi_4h_overbought(66, 66), "65 임계값이 70으로 바뀌면 실패해야 한다"


def test_target_grid_close_mode_mapping():
    """comparePriceOpenOrder.py:202-207 의 close_mode → target_grid 매핑."""
    CLOSE_GIMP_GAP = 0.5  # consts.py 현재 값

    def target_grid(close_mode: int) -> float:
        if close_mode == 0:
            return CLOSE_GIMP_GAP + 0.1
        if close_mode == 1:
            return CLOSE_GIMP_GAP - 0.1
        if close_mode == 2:
            return CLOSE_GIMP_GAP
        raise ValueError(close_mode)

    assert math.isclose(target_grid(0), 0.6)
    assert math.isclose(target_grid(1), 0.4)
    assert math.isclose(target_grid(2), 0.5)
