import logging
import traceback
from datetime import datetime, timedelta, timezone

from api import hana
from consts import BALANCE, POSITION_MAX_COUNT, TETHER


def get_profit_position(orderbook_check, position_data, trade_data, remain_bid_balance, exchange_data):
    try:
        usd_price = hana.get_currency_data("USD")
        open_timestamp = []
        open_message = {}
        message = ''

        open_bid_btc = float(orderbook_check['BTC']['Upbit']['balance_ask_average'])
        open_bid_eth = float(orderbook_check['ETH']['Upbit']['balance_ask_average'])
        open_bid_xrp = float(orderbook_check['XRP']['Upbit']['balance_ask_average'])

        open_ask_btc = float(orderbook_check['BTC']['Binance']['balance_bid_average'])
        open_ask_eth = float(orderbook_check['ETH']['Binance']['balance_bid_average'])
        open_ask_xrp = float(orderbook_check['XRP']['Binance']['balance_bid_average'])

        real_open_bid_btc = float(orderbook_check['BTC']['Upbit']['balance_ask_average'])
        real_open_bid_eth = float(orderbook_check['ETH']['Upbit']['balance_ask_average'])
        real_open_bid_xrp = float(orderbook_check['XRP']['Upbit']['balance_ask_average'])

        real_open_ask_btc = float(orderbook_check['BTC']['Binance']['balance_bid_average']) / TETHER * usd_price
        real_open_ask_eth = float(orderbook_check['ETH']['Binance']['balance_bid_average']) / TETHER * usd_price
        real_open_ask_xrp = float(orderbook_check['XRP']['Binance']['balance_bid_average']) / TETHER * usd_price

        if real_open_bid_btc == 0 or real_open_ask_btc == 0:
            return "🌚 1분 후 재시도..."
        if real_open_bid_eth == 0 or real_open_ask_eth == 0:
            return "🌚 1분 후 재시도..."
        if real_open_bid_xrp == 0 or real_open_ask_xrp == 0:
            return "🌚 1분 후 재시도..."
        if open_bid_btc == 0 or open_ask_btc == 0:
            return "🌚 1분 후 재시도..."
        if open_bid_eth == 0 or open_ask_eth == 0:
            return "🌚 1분 후 재시도..."
        if open_bid_xrp == 0 or open_ask_xrp == 0:
            return "🌚 1분 후 재시도..."

        fix_open_bid = open_bid_btc + open_bid_eth + open_bid_xrp
        fix_open_ask = open_ask_btc + open_ask_eth + open_ask_xrp

        real_open_bid = real_open_bid_btc + real_open_bid_eth + real_open_bid_xrp
        real_open_ask = real_open_ask_btc + real_open_ask_eth + real_open_ask_xrp
        fix_open_gimp = round(fix_open_bid / fix_open_ask * 100 - 100, 2)
        real_open_gimp = round(real_open_bid / real_open_ask * 100 - 100, 2)

        message = f"🌟고정김프:{fix_open_gimp}%|실제김프:{real_open_gimp}%\n"

        position_gimp_list = []
        position_ticker_list = []
        for ticker in position_data:
            if position_data[ticker]['position'] == 1:
                time_object_utc = datetime.fromtimestamp(position_data[ticker]['open_timestamp'], tz=timezone.utc)
                time_object_korea = time_object_utc.astimezone(timezone(timedelta(hours=9)))

                position_gimp_list.append(position_data[ticker]['position_gimp'])
                position_ticker_list.append(ticker)

                close_bid = float(orderbook_check[ticker]['Upbit']['balance_bid_average'])
                close_ask = float(orderbook_check[ticker]['Binance']['balance_ask_average'])

                if close_bid == 0 or close_ask == 0:
                    open_timestamp.append(time_object_korea)
                    open_message[time_object_korea] = (
                        f"🌚{ticker}({position_data[ticker]['open_install_count']}/{position_data[ticker]['close_install_count']})"
                        f"|{round(position_data[ticker]['position_gimp'], 2)}%|조회오류"
                        f"|{round(trade_data[ticker]['open_bid_price_acc']) - round(trade_data[ticker]['close_bid_price_acc']):,}원"
                        f"|{time_object_korea.strftime('%d일 %H:%M')}\n"
                    )
                else:
                    close_gimp = round(close_bid / close_ask * 100 - 100, 2)
                    open_timestamp.append(time_object_korea)
                    open_message[time_object_korea] = (
                        f"🌝{ticker}({position_data[ticker]['open_install_count']}/{position_data[ticker]['close_install_count']})"
                        f"|{round(position_data[ticker]['position_gimp'], 2)}%|{close_gimp}%"
                        f"|{round(trade_data[ticker]['open_bid_price_acc']) - round(trade_data[ticker]['close_bid_price_acc']):,}원"
                        f"|{time_object_korea.strftime('%d일 %H:%M')}\n"
                    )

        for _ in range(len(open_timestamp)):
            timestamp = min(open_timestamp)
            message += str(open_message[timestamp])
            open_timestamp.remove(timestamp)

        if len(position_gimp_list) > 0:
            min_position_gimp = min(position_gimp_list)
            ticker_index = position_gimp_list.index(min_position_gimp)
            min_ticker = position_ticker_list[ticker_index]

            message += f"🙆🏻진입현황({len(position_gimp_list)}/{POSITION_MAX_COUNT})\n"
            if exchange_data.get('close_mode') is not None:
                logging.debug(f"close_mode={exchange_data['close_mode']} min_ticker={min_ticker}")

        if remain_bid_balance['balance'] < BALANCE:
            message += f"💰잔액: {round(remain_bid_balance['balance']):,}원"

        if len(message) == 0:
            return "🌚 진입 정보 없음"
        return message
    except Exception:
        logging.info(traceback.format_exc())
        return "🌚 1분 후 재시도..."
