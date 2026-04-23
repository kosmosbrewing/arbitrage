import asyncio
import logging

from api import binance, upbit
from consts import EXECUTION_MODE, TETHER


def is_live_mode():
    return EXECUTION_MODE == "live"


def _build_paper_order_result(upbit_price, upbit_quantity, binance_price, binance_quantity):
    return {
        'uuid': 'paper',
        'orderId': 'paper',
        'upbit_price': upbit_price,
        'upbit_quantity': upbit_quantity,
        'binance_price': binance_price,
        'binance_quantity': binance_quantity,
    }


def _has_successful_order(order_result):
    return (
        order_result.get('uuid') not in (0, None)
        and order_result.get('orderId') not in (0, None)
        and order_result.get('upbit_quantity', 0) > 0
        and order_result.get('binance_quantity', 0) > 0
    )


async def execute_open_order(ticker, open_bid, open_ask, upbit_open_bid_price, open_quantity):
    if not is_live_mode():
        order_result = _build_paper_order_result(open_bid, open_quantity, open_ask, open_quantity)
        logging.info(f"ORDER_EXECUTION|MODE|paper|TYPE|open|TICKER|{ticker}|RESULT|{order_result}")
        return True, order_result

    order_result = {
        'uuid': 0,
        'orderId': 0,
        'upbit_price': 0,
        'upbit_quantity': 0,
        'binance_price': 0,
        'binance_quantity': 0,
    }
    order_lock = asyncio.Lock()

    await asyncio.gather(
        upbit.spot_order('KRW-' + ticker, 'bid', upbit_open_bid_price, 0, order_result, order_lock),
        binance.futures_order(ticker + 'USDT', 'ask', open_quantity, order_result, order_lock),
    )

    if order_result['uuid'] == 0 or order_result['orderId'] == 0:
        logging.info(f"ORDER_EXECUTION|MODE|live|TYPE|open|TICKER|{ticker}|STATUS|request_failed|RESULT|{order_result}")
        return False, order_result

    check_order_lock = asyncio.Lock()
    async with order_lock:
        await asyncio.gather(
            upbit.check_order(order_result, check_order_lock),
            binance.check_order(ticker + 'USDT', order_result, check_order_lock),
        )

    if not _has_successful_order(order_result):
        logging.info(f"ORDER_EXECUTION|MODE|live|TYPE|open|TICKER|{ticker}|STATUS|fill_failed|RESULT|{order_result}")
        return False, order_result

    order_result['binance_price'] = order_result['binance_price'] * TETHER
    logging.info(f"ORDER_EXECUTION|MODE|live|TYPE|open|TICKER|{ticker}|STATUS|filled|RESULT|{order_result}")
    return True, order_result


async def execute_close_order(ticker, close_bid, close_ask, upbit_quantity, binance_quantity):
    if not is_live_mode():
        order_result = _build_paper_order_result(close_bid, upbit_quantity, close_ask, binance_quantity)
        logging.info(f"ORDER_EXECUTION|MODE|paper|TYPE|close|TICKER|{ticker}|RESULT|{order_result}")
        return True, order_result

    order_result = {
        'uuid': 0,
        'orderId': 0,
        'upbit_price': 0,
        'upbit_quantity': 0,
        'binance_price': 0,
        'binance_quantity': 0,
    }
    order_lock = asyncio.Lock()

    await asyncio.gather(
        upbit.spot_order('KRW-' + ticker, 'ask', 0, upbit_quantity, order_result, order_lock),
        binance.futures_order(ticker + 'USDT', 'bid', binance_quantity, order_result, order_lock),
    )

    if order_result['uuid'] == 0 or order_result['orderId'] == 0:
        logging.info(f"ORDER_EXECUTION|MODE|live|TYPE|close|TICKER|{ticker}|STATUS|request_failed|RESULT|{order_result}")
        return False, order_result

    check_order_lock = asyncio.Lock()
    async with order_lock:
        await asyncio.gather(
            upbit.check_order(order_result, check_order_lock),
            binance.check_order(ticker + 'USDT', order_result, check_order_lock),
        )

    if not _has_successful_order(order_result):
        logging.info(f"ORDER_EXECUTION|MODE|live|TYPE|close|TICKER|{ticker}|STATUS|fill_failed|RESULT|{order_result}")
        return False, order_result

    order_result['binance_price'] = order_result['binance_price'] * TETHER
    logging.info(f"ORDER_EXECUTION|MODE|live|TYPE|close|TICKER|{ticker}|STATUS|filled|RESULT|{order_result}")
    return True, order_result
