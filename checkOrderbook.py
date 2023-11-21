import asyncio
import traceback
import logging
from consts import *


@profile
def check_orderbook(orderbook_info, orderbook_check):
    # 거래소별 socket 연결을 통해 필요한 코인정보가 있어서 대기
    for ticker in orderbook_info:
        if ticker in ["USD", "USDT"]:  # 스테이블코인은 비교 제외
            continue

        if ticker not in orderbook_check:
            orderbook_check[ticker] = {}
            for exchange_list in EXCHANGE_LIST:
                orderbook_check[ticker].update({exchange_list: None})

        for exchange in EXCHANGE_LIST:
            bid_amount = 0
            bid_size = 0
            ask_amount = 0
            ask_size = 0
            balance_bid_check = 0
            balance_ask_check = 0
            balance_bid_average = 0
            balance_ask_average = 0

            for orderbook in orderbook_info[ticker][exchange]['orderbook_units']:
                if orderbook is None:
                    continue

                bid_amount += float(orderbook['bid_price']) * float(orderbook['bid_size'])
                bid_size += float(orderbook['bid_size'])
                ask_amount += float(orderbook['ask_price']) * float(orderbook['ask_size'])
                ask_size += float(orderbook['ask_size'])

                ## bid_amount 로직 수정하기
                if bid_amount > BALANCE and balance_bid_check == 0:
                    balance_bid_average = round(float(bid_amount / bid_size), 2) if bid_size != 0 else 0
                    balance_bid_check += 1

                if ask_amount > BALANCE and balance_ask_check == 0:
                    balance_ask_average = round(float(ask_amount / ask_size), 2) if ask_size != 0 else 0
                    balance_ask_check += 1

            if bid_size == 0 or ask_size == 0:
                continue

            bid_average = round(float(bid_amount / bid_size), 2)
            ask_average = round(float(ask_amount / ask_size), 2)

            orderbook_check[ticker][exchange] = \
                {"bid_amount": bid_amount, "bid_average": bid_average,
                 "ask_amount": ask_amount, "ask_average": ask_average,
                 "balance_bid_average": balance_bid_average, "balance_ask_average": balance_ask_average}