import asyncio
import os
import matplotlib.pyplot as plt
import datetime
import util
from consts import *

async def get_history_data():
    exchange_measure = {}
    measure_ticker = {}

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


        #print(split_data[1], split_data[10], split_data[11], split_data[12], split_data[13], split_data[14])

    for ticker in exchange_measure:
        diff_gap = float(exchange_measure[ticker]['close_gap']) - float(exchange_measure[ticker]['open_gap'])

        if diff_gap > 0.1:
            print(f"{ticker} : {diff_gap}")
            measure_ticker[ticker] = {"units": []}

    for line in lines:
        split_data = line.split('|')

        ticker = split_data[1]
        # base_exchange = split_data[2]
        # compare_exchange = split_data[3]
        open_gap = split_data[5]
        open_data = split_data[6]
        close_gap = split_data[8]
        close_data = split_data[9]
        amount = split_data[13]
        # usd = split_data[15]

        if ticker in measure_ticker:
            measure_ticker[ticker]['units'].append({"open_gap": open_gap, "open_data": open_data, "open_gap_avg": 0,
                                                    "close_gap": close_gap, "close_data": close_data, "close_gap_avg": 0})

    figure_idx = 0
    subplot_idx = 0
    subplot_loc = [[331, 332, 333, 334, 335, 336, 337, 338, 339],
                 [331, 332, 333, 334, 335, 336, 337, 338, 339],
                 [331, 332, 333, 334, 335, 336, 337, 338, 339],
                 [331, 332, 333, 334, 335, 336, 337, 338, 339],
                 [331, 332, 333, 334, 335, 336, 337, 338, 339]]
    image_set = []

    for graph_ticker in measure_ticker:
        # 데이터 준비
        open_gap = []
        close_gap = []

        for i in range(0, len(measure_ticker[graph_ticker]['units'])):
            open_gap.append(float(measure_ticker[graph_ticker]['units'][i]['open_gap']))
            close_gap.append(float(measure_ticker[graph_ticker]['units'][i]['close_gap']))

        # 그래프 그리기
        plt.figure(figure_idx,figsize=(15, 10)) # 그래프 개수
        plt.subplot(subplot_loc[figure_idx][subplot_idx]) # 그래프 위치
        plt.title(graph_ticker)
        plt.plot(open_gap, label='open', color='blue')
        plt.plot(close_gap, label='close', color='red')
        plt.ylabel('gap')
        subplot_idx += 1

        if subplot_idx == 9:
            image_temp = image_file_path + '_' + str(figure_idx+1) + '.png'
            image_set.append(image_temp)
            plt.savefig(image_temp + '_' + str(figure_idx+1) + '.png', format='png')
            figure_idx += 1
            subplot_idx = 0

    image_temp = image_file_path + '_' + str(figure_idx + 1) + '.png'
    image_set.append(image_temp)
    plt.savefig(image_temp, format='png')

    for image in image_set:
        await util.send_to_telegram_image(image)

if __name__ == "__main__":
    asyncio.run(get_history_data())
    #get_history_data()