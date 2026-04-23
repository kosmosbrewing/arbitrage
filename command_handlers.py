import logging
import subprocess
import traceback

import util
from consts import BALANCE
from graph_command_service import handle_graph


def prepare_current_state(premium):
    premium.orderbook_check = {}
    premium.position_data = {}
    premium.trade_data = {}
    premium.remain_bid_balance = {"balance": BALANCE}
    premium.position_ticker_count = {"count": 0, "open_gimp_limit": 0}


async def handle_current(premium):
    prepare_current_state(premium)
    util.load_orderbook_check(premium.orderbook_check)
    util.load_remain_position(premium.position_data, premium.trade_data, premium.position_ticker_count)
    util.load_close_mode(premium.exchange_data)

    for ticker in premium.position_data:
        if premium.position_data[ticker]['position'] == 1:
            premium.remain_bid_balance['balance'] -= (
                premium.trade_data[ticker]['open_bid_price_acc'] - premium.trade_data[ticker]['close_bid_price_acc']
            )

    current_message = util.get_profit_position(
        premium.orderbook_check,
        premium.position_data,
        premium.trade_data,
        premium.remain_bid_balance,
        premium.exchange_data,
    )
    await premium.bot.send_message(chat_id=premium.allowed_chat_id, text=current_message)


async def handle_order(bot, allowed_chat_id, args):
    if len(args) < 2:
        await bot.send_message(chat_id=allowed_chat_id, text="🌚 Flag와 Ticker를 입력 하세요. (open/close/stop_open/init BTC)")
        return

    flag = args[0]
    ticker = args[1]
    order_flag = {}

    if flag == 'open':
        order_flag = {"open": 1, "close": 0, "ticker": ticker}
    elif flag == 'close':
        order_flag = {"open": 0, "close": 1, "ticker": ticker}
    elif flag == 'stop_open':
        order_flag = {"open": -1, "close": 0, "ticker": ticker}
    elif flag == 'init':
        order_flag = {"open": 0, "close": 0, "ticker": ticker}
    else:
        await bot.send_message(chat_id=allowed_chat_id, text="🌚 지원하지 않는 Flag 입니다.")
        return

    util.put_order_flag(order_flag)
    await bot.send_message(chat_id=allowed_chat_id, text=f"🌝 진입/종료 강제 Flag 설정 완료 : {order_flag}")


async def handle_set_grid(bot, allowed_chat_id, args):
    if not args:
        await bot.send_message(chat_id=allowed_chat_id, text="🌚 숫자를 입력 하세요.")
        return

    exchange_data = {'low_gimp': args[0]}
    util.put_low_gimp(exchange_data)
    await bot.send_message(chat_id=allowed_chat_id, text=f"🌝 진입 그리드 최저 값 설정 : {exchange_data}%")


async def handle_set_close(bot, allowed_chat_id, args):
    if not args:
        await bot.send_message(chat_id=allowed_chat_id, text="🌚 숫자를 입력 하세요.")
        return

    exchange_data = {'close_mode': args[0]}
    util.put_close_mode(exchange_data)
    await bot.send_message(chat_id=allowed_chat_id, text=f"🌝 종료 모드 설정 : {exchange_data}\n")


async def handle_restart(bot, allowed_chat_id):
    execute_shell = "/root/arbitrage/bin/main_restart.sh"
    process = subprocess.Popen(execute_shell, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, error = process.communicate()

    if error:
        await bot.send_message(chat_id=allowed_chat_id, text="🌚 Main Restart 수행 실패")
        logging.info(error.decode("utf-8"))
    else:
        await bot.send_message(chat_id=allowed_chat_id, text="🌝 Main Restart 수행 성공!")
async def send_error(bot, allowed_chat_id):
    await bot.send_message(chat_id=allowed_chat_id, text='🌚 오류 발생..')
    logging.info(traceback.format_exc())
