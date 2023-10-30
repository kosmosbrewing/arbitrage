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
        history_file_path = '/root/arbitrage/log/premium_data_' + yesterday
    elif ENV == 'local':
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data_' + yesterday

    if os.path.exists(history_file_path):
        print(history_file_path)
        with open(history_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    else:
        print(f"{history_file_path} 파일이 존재하지 않습니다.")

    return lines


def get_measure_ticker():
    check_data = {}
    trade_data = {}
    position_data = {}
    measure_ticker = {}

    lines = load_history_data()
    btc_open_gap = 0

    for line in lines:
        split_data = line.split('|')
        date_time = split_data[0].split('[INFO')[0]
        ticker = split_data[1]
        open_gap = float(split_data[5])
        open_data = split_data[6].split('/')
        open_bid = float(open_data[0].replace(',', ''))  ## 매수 평단가
        open_ask = float(open_data[1].replace(',', ''))  ## 매도(숏) 평단가
        close_gap = float(split_data[8])
        close_data = split_data[9].split('/')
        close_bid = float(close_data[0].replace(',', ''))  ## 매도(매수 종료) 평단가
        close_ask = float(close_data[1].replace(',', ''))  ## 매수(매도(숏) 종료) 평단가
        usd = float(split_data[15])

        if ticker == "BTC":
            btc_open_gap = open_gap

        ## 데이터 값 초기화
        if ticker not in check_data:
            check_data[ticker] = {"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask,
                                  "close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask,
                                  "front_open_gap": open_gap, "front_close_gap": close_gap}
        if ticker not in position_data:
            position_data[ticker] = {"open_count": 0, "position": 0, "position_gap": 0,
                                     "position_gap_accum": 0, "installment_count": 0}
        if ticker not in trade_data:
            trade_data[ticker] = {"open_bid_amount": 0, "open_ask_amount": 0, "close_bid_amount": 0,
                                  "close_ask_amount": 0,
                                  "trade_quantity": 0, "trade_profit": 0, "profit_count": 0, "total_profit": 0}

        front_open_gap = check_data[ticker]['front_open_gap']
        front_close_gap = check_data[ticker]['front_close_gap']
        check_data[ticker]['front_open_gap'] = open_gap
        check_data[ticker]['front_close_gap'] = close_gap

        if open_gap - front_open_gap > FRONT_GAP or front_close_gap - close_gap > FRONT_GAP:
            print(f"{date_time} {ticker} 허수 값 PASS | {open_gap} | {front_open_gap} | {close_gap} | {front_close_gap}")
            continue

        ## Open 저점 계산, BTC 김프 보단 낮아야 함 < btc_open_gap
        # if open_gap < check_data[ticker]['open_gap'] and open_gap < btc_open_gap:
        if open_gap <= check_data[ticker]['open_gap']:
            # open_gap 이 Update 되면 close_gap은 그 시점으로 gap 수정
            check_data[ticker].update({"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask})
            check_data[ticker].update({"close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask})

        ## Close 고점 계산
        if close_gap > check_data[ticker]['close_gap']:
            # Close 고점 데이터 갱신
            check_data[ticker].update({"close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask})

            check_diff_gap = check_data[ticker]['close_gap'] - check_data[ticker]['open_gap']
            close_diff_gap = check_data[ticker]['close_gap'] - position_data[ticker]['position_gap']
            ## 변동성 확인
            # if check_diff_gap > MEASURE_OPEN_GAP and open_flag[ticker] == 0:
            if check_diff_gap > MEASURE_OPEN_GAP:
                position_data[ticker]['open_count'] += 1

                print(f"{ticker} 변동성 포착 |LOW_OPEN|{check_data[ticker]['open_gap']}|"
                      f"CURR_CLOSE|{close_gap}|CURR_OPEN|{open_gap}|OPEN_COUNT|{position_data[ticker]['open_count']}")
                check_data[ticker].update({"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask})

            if position_data[ticker]['open_count'] >= 3:
                measure_ticker[ticker] = {"units": []}

    return measure_ticker

if __name__ == "__main__":
    get_measure_ticker()