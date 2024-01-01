import logging

import util
from api import upbit
from consts import *

async def check_real_gimp(orderbook_info, exchange_data):
    usd_price = upbit.get_usd_price()
    upbit_balance_ask_average = 0
    binance_balance_bid_average = 0
    error_check = 0

    if 'grid_check' not in exchange_data:
        exchange_data['grid_check'] = 0

    for ticker in orderbook_info:
        if ticker in ["BTC", "ETH", "XRP"]:  # 스테이블코인은 비교 제외
            binance_bid_amount = 0
            binance_bid_size = 0
            upbit_ask_amount = 0
            upbit_ask_size = 0
            balance_bid_check = 0
            balance_ask_check = 0

            for exchange in EXCHANGE_LIST:
                for orderbook in orderbook_info[ticker][exchange]['orderbook_units']:
                    if orderbook is None:
                        error_check = 1

                    if exchange == 'Binance':
                        binance_bid_amount += float(orderbook['bid_price']) * float(orderbook['bid_size']) / TETHER * usd_price
                        binance_bid_size += float(orderbook['bid_size'])

                        if binance_bid_amount > BALANCE and balance_bid_check == 0:
                            binance_balance_bid_average += float(binance_bid_amount / binance_bid_size)
                            balance_bid_check = 1

                    if exchange == 'Upbit':
                        upbit_ask_amount += float(orderbook['ask_price']) * float(orderbook['ask_size'])
                        upbit_ask_size += float(orderbook['ask_size'])

                        if upbit_ask_amount > BALANCE and balance_ask_check == 0:
                            upbit_balance_ask_average += float(upbit_ask_amount / upbit_ask_size)
                            balance_ask_check = 1

            if balance_bid_check == 0 or balance_ask_check == 0:
                error_check = 1

    if error_check == 0:
        exchange_data['avg_gimp'] = upbit_balance_ask_average / binance_balance_bid_average * 100 - 100

        if 'low_gimp' not in exchange_data:
            exchange_data['low_gimp'] = exchange_data['avg_gimp']

        if exchange_data['avg_gimp'] < exchange_data['low_gimp']:
            exchange_data['low_gimp'] = exchange_data['avg_gimp']
            exchange_data['grid_check'] = 0
            util.put_low_gimp(exchange_data)
            logging.info(f"김프 저점 갱신|{round(exchange_data['low_gimp'], 2)}%|UPBIT|{upbit_balance_ask_average:,}원|BINANCE|{binance_balance_bid_average:,}원")
            message = f"🌚 김프 저점 갱신: {round(exchange_data['low_gimp'], 2)}%, 환율 : {usd_price}원"
            await util.send_to_telegram(message)

        elif exchange_data['avg_gimp'] > exchange_data['low_gimp'] + GRID_CHECK_GAP + 1:
            exchange_data['low_gimp'] = exchange_data['avg_gimp']
            exchange_data['grid_check'] = 0
            util.put_low_gimp(exchange_data)
            logging.info(f"김프 추세 전환|{round(exchange_data['low_gimp'], 2)}%|UPBIT|{upbit_balance_ask_average:,}원|BINANCE|{binance_balance_bid_average:,}원")
            message = f"🌚 김프 추세 전환: {round(exchange_data['low_gimp'], 2)}%, 환율 : {usd_price}원"
            await util.send_to_telegram(message)

        elif exchange_data['avg_gimp'] < exchange_data['low_gimp'] + GRID_CHECK_GAP:
            exchange_data['grid_check'] += 1
            logging.info(f"김프 진입 그리드 설정 {round(exchange_data['low_gimp'], 2)}% <-> {round(exchange_data['low_gimp'] + GRID_CHECK_GAP, 2)}%")
            if exchange_data['grid_check'] == 1:
                message = f"🌝김프 그리드 설정: {round(exchange_data['low_gimp'], 2)}% <-> {round(exchange_data['low_gimp'] + GRID_CHECK_GAP, 2)}%"
                await util.send_to_telegram(message)
