import asyncio
import os
import matplotlib.pyplot as plt
import datetime
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
        image_file_path = '/root/arbitrage/image/arbitrage_'+yesterday
    elif ENV == 'local':
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data.log_'+yesterday
        image_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/image/arbitrage_'+yesterday

    if os.path.exists(history_file_path):
        with open(history_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    else:
        print(f"{history_file_path} 파일이 존재하지 않습니다.")

    return lines


def get_measure_ticker():
    exchange_measure = {}
    measure_ticker = {}

    lines = load_history_data()

    for line in lines:
        split_data = line.split('|')

        ticker = split_data[1]
        #base_exchange = split_data[2]
        #compare_exchange = split_data[3]
        open_gap = split_data[5]
        open_data = split_data[6]
        close_gap = split_data[8]
        close_data = split_data[9]
        amount = split_data[13]
        #usd = split_data[15]

        if ticker not in exchange_measure:
            exchange_measure[ticker] = {"open_gap": open_gap, "open_data": open_data, "open_gap_avg": 0,
                                        "close_gap": close_gap, "close_data": close_data, "close_gap_avg": 0}

        if exchange_measure[ticker]['open_gap'] > open_gap:
            exchange_measure[ticker].update({"open_gap": open_gap, "open_data": open_data})

        if exchange_measure[ticker]['close_gap'] < close_gap:
            exchange_measure[ticker].update({"close_gap": close_gap, "close_data": close_data})

        for ticker in exchange_measure:
            diff_gap = float(exchange_measure[ticker]['close_gap']) - float(exchange_measure[ticker]['open_gap'])

            if diff_gap > MEASURE_GAP:
                measure_ticker[ticker] = {"units": []}

    return measure_ticker