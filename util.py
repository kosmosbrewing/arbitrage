from datetime import datetime, timedelta

from logging_utils import setup_collect_logging, setup_order_logging
from position_reporting import get_profit_position
from storage_utils import (
    load_close_mode,
    load_history_data,
    load_low_gimp,
    load_order_flag,
    load_orderbook_check,
    load_profit_count,
    load_profit_data,
    load_remain_position,
    load_top_ticker,
    put_close_mode,
    put_low_gimp,
    put_order_flag,
    put_orderbook_check,
    put_profit_count,
    put_profit_data,
    put_remain_position,
    put_top_ticker,
)
from telegram_utils import get_chat_id, send_to_telegram, send_to_telegram_image


def is_need_reset_socket(start_time):
    return start_time < datetime.now() - timedelta(days=1)
