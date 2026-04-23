"""VWAP / orderbook aggregation tests for api/checkOrderbook.py.

We bypass `api/__init__.py` to avoid pulling the full API surface (which needs
requests/aiohttp/pyupbit). `api/checkOrderbook.py` itself only needs `consts`
and thin stubs of `upbit`/`binance`, which we inject via sys.modules.
"""

from __future__ import annotations

import importlib.util
import math
import os
import sys
import types
from unittest.mock import patch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_checkOrderbook():
    # Build a minimal fake `api` package that only exposes `upbit` / `binance`
    # attribute stubs, so `from api import upbit, binance` resolves without
    # triggering `api/__init__.py` (which imports requests-heavy modules).
    fake_api = types.ModuleType("api")
    fake_api.__path__ = []  # mark as package
    fake_upbit = types.ModuleType("api.upbit")
    fake_binance = types.ModuleType("api.binance")
    fake_upbit.get_all_ticker = lambda: []
    fake_binance.get_all_book_ticker = lambda: []
    fake_api.upbit = fake_upbit
    fake_api.binance = fake_binance

    sys.modules["api"] = fake_api
    sys.modules["api.upbit"] = fake_upbit
    sys.modules["api.binance"] = fake_binance

    module_path = os.path.join(REPO_ROOT, "api", "checkOrderbook.py")
    spec = importlib.util.spec_from_file_location("api.checkOrderbook", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["api.checkOrderbook"] = module
    spec.loader.exec_module(module)
    return module


def _make_level(ask_price, ask_size, bid_price, bid_size):
    return {
        "ask_price": ask_price,
        "ask_size": ask_size,
        "bid_price": bid_price,
        "bid_size": bid_size,
    }


def _minimal_orderbook_info(ticker="BTC"):
    # Two exchanges, three orderbook levels each. Numbers chosen to give
    # deterministic VWAPs so we can check the aggregation math.
    return {
        ticker: {
            "Upbit": {
                "orderbook_units": [
                    _make_level(ask_price=100.0, ask_size=2.0, bid_price=99.0, bid_size=3.0),
                    _make_level(ask_price=101.0, ask_size=1.0, bid_price=98.0, bid_size=2.0),
                    _make_level(ask_price=102.0, ask_size=1.0, bid_price=97.0, bid_size=1.0),
                ]
            },
            "Binance": {
                "orderbook_units": [
                    _make_level(ask_price=50.0, ask_size=4.0, bid_price=49.0, bid_size=5.0),
                    _make_level(ask_price=50.5, ask_size=2.0, bid_price=48.5, bid_size=3.0),
                    _make_level(ask_price=51.0, ask_size=2.0, bid_price=48.0, bid_size=2.0),
                ]
            },
            "Bithumb": {
                "orderbook_units": [
                    _make_level(ask_price=0.0, ask_size=0.0, bid_price=0.0, bid_size=0.0),
                ]
            },
        }
    }


def test_vwap_computes_expected_averages_when_balance_threshold_is_low():
    checkOrderbook = _load_checkOrderbook()
    info = _minimal_orderbook_info()
    orderbook_check = {}

    # Force the balance threshold low so the first orderbook level triggers
    # balance_bid_average / balance_ask_average assignment on both exchanges.
    with patch.object(checkOrderbook, "BALANCE", 1), patch.object(
        checkOrderbook, "OPEN_INSTALLMENT", 0.01
    ):
        checkOrderbook.check_orderbook(info, orderbook_check)

    upbit = orderbook_check["BTC"]["Upbit"]
    binance = orderbook_check["BTC"]["Binance"]

    # Non-weighted VWAP across all three Upbit levels:
    # bid_amount = 99*3 + 98*2 + 97*1 = 297 + 196 + 97 = 590
    # bid_size   = 3 + 2 + 1 = 6
    assert math.isclose(upbit["bid_amount"], 590.0, abs_tol=1e-9)
    assert math.isclose(upbit["bid_average"], 590.0 / 6, rel_tol=1e-9)

    # Binance ask_amount = 50*4 + 50.5*2 + 51*2 = 200 + 101 + 102 = 403
    # Binance ask_size   = 4 + 2 + 2 = 8
    assert math.isclose(binance["ask_amount"], 403.0, abs_tol=1e-9)
    assert math.isclose(binance["ask_average"], 403.0 / 8, rel_tol=1e-9)

    # With a negligible balance threshold the balance_*_average must be set
    # on the first level (never 0).
    assert upbit["balance_bid_average"] > 0
    assert upbit["balance_ask_average"] > 0
    assert binance["balance_bid_average"] > 0
    assert binance["balance_ask_average"] > 0


def test_vwap_skips_stablecoin_ton():
    checkOrderbook = _load_checkOrderbook()
    info = _minimal_orderbook_info(ticker="TON")
    orderbook_check = {}

    checkOrderbook.check_orderbook(info, orderbook_check)

    assert "TON" not in orderbook_check, "TON은 스테이블코인 취급으로 집계 제외되어야 한다"


def test_vwap_skips_empty_orderbook_side():
    checkOrderbook = _load_checkOrderbook()
    info = _minimal_orderbook_info()
    # Wipe Upbit bid liquidity entirely.
    for level in info["BTC"]["Upbit"]["orderbook_units"]:
        level["bid_size"] = 0
        level["bid_price"] = 0

    orderbook_check = {}
    checkOrderbook.check_orderbook(info, orderbook_check)

    # Upbit entry must remain None when bid_size == 0 (check_orderbook hits `continue`
    # before writing the dict, leaving the pre-populated None).
    assert orderbook_check["BTC"]["Upbit"] is None
