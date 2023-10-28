import asyncio
import os
import matplotlib.pyplot as plt
import datetime
import math
import util
from consts import *


def load_history_data():
    # 오늘 날짜 가져오기
    today = datetime.date.today()
    # 하루 전 날짜 계산
    yesterday = today - datetime.timedelta(days=1)
    yesterday = yesterday.strftime("%Y%m%d")

    if ENV == 'real':
        history_file_path = '/root/arbitrage/log/premium_data.log_'+yesterday
    elif ENV == 'local':
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data.log_'+yesterday

    if os.path.exists(history_file_path):
        with open(history_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    else:
        print(f"{history_file_path} 파일이 존재하지 않습니다.")

    return lines


def get_measure_ticker():
    exchange_measure = {}
    trade_data = {}
    measure_ticker = {}

    lines = load_history_data()

    for line in lines:
        split_data = line.split('|')

        ticker = split_data[1]
        #base_exchange = split_data[2]
        #compare_exchange = split_data[3]
        open_gap = float(split_data[5])
        open_data = split_data[6].split('/')
        open_bid = float(open_data[0].replace(',', '')) ## 매수 평단가
        open_ask = float(open_data[1].replace(',', '')) ## 매도(숏) 평단가
        close_gap = float(split_data[8])
        close_data = split_data[9].split('/')
        close_bid = float(close_data[0].replace(',', '')) ## 매도(매수 종료) 평단가
        close_ask = float(close_data[1].replace(',', '')) ## 매수(매도(숏) 종료) 평단가
        amount = split_data[13]
        usd = float(split_data[15])
        trade_quantity = 0

        if ticker not in exchange_measure:
            exchange_measure[ticker] = {"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask,
                                        "close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask}

        if ticker not in trade_data:
            trade_data[ticker] = {"open_bid_amount": 0, "open_ask_amount": 0,
                                    "close_bid_amount": 0, "close_ask_amount": 0,
                                  "trade_quantity": 0, "total_profit": 0}

        if exchange_measure[ticker]['open_gap'] > open_gap:
            # open_gap 이 Update 되면 close_gap은 그 시점으로 gap 수정
            exchange_measure[ticker].update({"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask})
            exchange_measure[ticker].update({"close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask})

            if open_bid > open_ask:
                trade_price = open_bid
            else:
                trade_price = open_ask

            trade_quantity = math.floor(BALANCE / trade_price)
            open_bid_amount = float(open_bid * trade_quantity)
            open_ask_amount = float(open_ask * trade_quantity)

            trade_data[ticker].update({"open_bid_amount": open_bid_amount, "open_ask_amount": open_ask_amount,
                                       "trade_quantity": trade_quantity})

            if ticker in measure_ticker:
                del measure_ticker[ticker]

        if exchange_measure[ticker]['close_gap'] < close_gap:
            exchange_measure[ticker].update({"close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask})

            trade_quantity = trade_data[ticker]['trade_quantity']
            close_bid_amount = float(close_bid * trade_quantity)
            close_ask_amount = float(close_ask * trade_quantity)
            trade_data[ticker].update({"close_bid_amount": close_bid_amount, "close_ask_amount": close_ask_amount})

        diff_gap = exchange_measure[ticker]['close_gap'] - exchange_measure[ticker]['open_gap']

        if diff_gap > MEASURE_GAP:
            measure_ticker[ticker] = {"units": []}

    for ticker in measure_ticker:
        print(f"{ticker} DIFF : "
              f"{exchange_measure[ticker]['close_gap']} - ({exchange_measure[ticker]['open_gap']}) = "
              f"{round(exchange_measure[ticker]['close_gap'] - exchange_measure[ticker]['open_gap'], 2)}")


        open_profit = trade_data[ticker]['close_bid_amount'] - trade_data[ticker]['open_bid_amount']
        close_profit = trade_data[ticker]['open_ask_amount'] - trade_data[ticker]['close_ask_amount']

        open_fee = trade_data[ticker]['open_bid_amount'] * UPBIT_FEE + trade_data[ticker]['open_ask_amount'] * BINANCE_FEE
        close_fee = trade_data[ticker]['close_bid_amount'] * UPBIT_FEE + trade_data[ticker]['close_ask_amount'] * BINANCE_FEE

        total_fee = open_fee + close_fee
        total_profit = open_profit + close_profit - total_fee

        trade_data[ticker].update({"total_profit": total_profit})

        print(exchange_measure[ticker])
        print((trade_data[ticker]), total_fee)

    return measure_ticker

if __name__ == "__main__":
    get_measure_ticker()