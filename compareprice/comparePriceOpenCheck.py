import traceback
import logging
from collections import deque
from consts import *

async def compare_price_open_check(orderbook_check, check_data, trade_data,
                                position_data, acc_ticker_count, acc_ticker_data, position_ticker_count):
    """ self.exchange_price 저장된 거래소별 코인정보를 비교하고 특정 (%)이상 갭발생시 알림 전달하는 함수 """
    base_exchange = UPBIT
    compare_exchange = BINANCE
    position_gimp_list = []
    position_ticker_list = []

    for ticker in orderbook_check:
        try:
            if orderbook_check[ticker]['Binance'] is None or orderbook_check[ticker]['Upbit'] is None:
                continue

            open_bid = orderbook_check[ticker][base_exchange]['balance_ask_average']
            close_bid = orderbook_check[ticker][base_exchange]['balance_bid_average']
            open_ask = orderbook_check[ticker][compare_exchange]['balance_bid_average']
            close_ask = orderbook_check[ticker][compare_exchange]['balance_ask_average']
            open_bid_btc = orderbook_check['BTC'][base_exchange]['balance_ask_average']
            open_ask_btc = orderbook_check['BTC'][compare_exchange]['balance_bid_average']

            ## 가격이 없는 친구들 PASS
            if open_bid == 0 or close_bid == 0 or open_ask == 0 or close_ask == 0 or open_bid_btc == 0 or open_ask_btc == 0:
                continue

            open_gimp = open_bid / open_ask * 100 - 100
            close_gimp = close_bid / close_ask * 100 - 100

            ## 데이터 값 초기화
            if ticker not in check_data:
                check_data[ticker] = {
                    "open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                    "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask
                }
            if ticker not in position_data:
                position_data[ticker] = {
                    "open_install_count": 0, "close_install_count": 0, "acc_open_install_count": 0,
                    "position": 0, "position_gimp": 0, "position_gimp_acc": [], "position_gimp_acc_weight": [],
                    "profit_count": 0, "front_close_gimp": 0, "open_timestamp": 0, "open_limit_count": 0,
                    "open_install_check": 0
                }
            if ticker not in trade_data:
                trade_data[ticker] = {
                    "open_bid_price_acc": 0, "open_ask_price_acc": 0,
                    "close_bid_price_acc": 0, "close_ask_price_acc": 0,
                    "upbit_total_quantity": 0, "upbit_close_quantity": 0,
                    "binance_total_quantity": 0, "binance_close_quantity": 0,
                    "trade_profit": 0, "total_profit": 0
                }
            if ticker not in acc_ticker_count:
                acc_ticker_count[ticker] = {
                    'data': deque(maxlen=FRONT_OPEN_COUNT),
                    'open_count': 0
                }
            if ticker not in acc_ticker_data:
                acc_ticker_data[ticker] = {
                    'data': deque(maxlen=FRONT_AVERAGE_COUNT),
                    'fall_check': 0
                }

            ## 저점 진입 김프 <-> 현재 포지션 종료 김프 계산하여 수익 변동성 확인
            if close_gimp - check_data[ticker]['open_gimp'] > OPEN_GIMP_GAP:
                check_data[ticker] = {
                    "open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                    "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask
                }

                acc_ticker_count[ticker]['data'].append(1)
                acc_ticker_count[ticker]['open_count'] = sum(acc_ticker_count[ticker]['data'])
            else:
                acc_ticker_count[ticker]['data'].append(0)
                acc_ticker_count[ticker]['open_count'] = sum(acc_ticker_count[ticker]['data'])

            if position_data[ticker]['position'] == 1:
                position_gimp_list.append(position_data[ticker]['position_gimp'])
                position_ticker_list.append(ticker)
            else:
                position_data[ticker]['open_install_check'] = 0

            acc_ticker_data[ticker]['data'].append(open_gimp)
            acc_ticker_data_len = len(acc_ticker_data[ticker]['data'])

            if acc_ticker_data_len > 30:
                acc_ticker_data[ticker]['fall_check'] = 1
                for i in range(3):
                    if acc_ticker_data[ticker]['data'][round(i * acc_ticker_data_len / 3)] < acc_ticker_data[ticker]['data'][round((i+1) * acc_ticker_data_len / 3) - 1]:
                        acc_ticker_data[ticker]['fall_check'] = 0

        except Exception as e:
            logging.info(f"OpenCheck 오류: {traceback.format_exc()}")
            continue
    try:
        if len(position_gimp_list) >= POSITION_CHECK_COUNT:
            temp_gimp = 0

            for i in range(POSITION_CHECK_COUNT):
                min_position_gimp = min(position_gimp_list)
                temp_gimp += min_position_gimp

                ticker_index = position_gimp_list.index(min_position_gimp)
                min_ticker = position_ticker_list[ticker_index]
                position_data[min_ticker]['open_install_check'] = 1

                position_gimp_list.remove(min_position_gimp)
                position_ticker_list.remove(min_ticker)

            position_ticker_count['open_gimp_limit'] = temp_gimp * 0.93 / POSITION_CHECK_COUNT
    except Exception as e:
        logging.info(f"OpenCheck 오류: {traceback.format_exc()}")

