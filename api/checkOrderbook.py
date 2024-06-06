from consts import *
from api import upbit, binance
from collections import Counter

def get_common_orderbook_ticker():
    krw_ticker = upbit.get_all_ticker()
    usdt_ticker = binance.get_all_book_ticker()

    for i in range(len(krw_ticker)):
        krw_ticker[i] = krw_ticker[i].split('-')[1]

    for i in range(len(usdt_ticker)):
        usdt_ticker[i] = usdt_ticker[i].replace("usdt@depth", "")
        usdt_ticker[i] = usdt_ticker[i].upper()

    krw_ticker = set(krw_ticker)
    usdt_ticker = set(usdt_ticker)

    counter = Counter(list(krw_ticker) + list(usdt_ticker))

    # 빈도가 1보다 큰 요소들을 찾아 중복된 값을 구합니다.
    return [element for element, count in counter.items() if count > 1]

def check_orderbook(orderbook_info, orderbook_check):
    # 거래소별 socket 연결을 통해 필요한 코인정보가 있어서 대기
    for ticker in orderbook_info:
        if ticker in ["TON"]:  # 스테이블코인은 비교 제외
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
                if bid_amount > BALANCE * OPEN_INSTALLMENT and balance_bid_check == 0:
                    balance_bid_average = float(bid_amount / bid_size) if bid_size != 0 else 0
                    balance_bid_check += 1

                if ask_amount > BALANCE * OPEN_INSTALLMENT and balance_ask_check == 0:
                    balance_ask_average = float(ask_amount / ask_size) if ask_size != 0 else 0
                    balance_ask_check += 1

            if bid_size == 0 or ask_size == 0:
                continue

            bid_average = float(bid_amount / bid_size)
            ask_average = float(ask_amount / ask_size)

            orderbook_check[ticker][exchange] = \
                {"bid_amount": bid_amount, "bid_average": bid_average,
                 "ask_amount": ask_amount, "ask_average": ask_average,
                 "balance_bid_average": balance_bid_average, "balance_ask_average": balance_ask_average}