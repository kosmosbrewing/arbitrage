import asyncio
import os
import matplotlib.pyplot as plt
import datetime
import measure
from measure import *

async def make_graph():
    today = datetime.date.today()
    # 하루 전 날짜 계산
    yesterday = today - datetime.timedelta(days=1)
    yesterday = yesterday.strftime("%Y%m%d")

    if ENV == 'real':
        image_file_path = '/root/arbitrage/image/arbitrage_' + yesterday
    elif ENV == 'local':
        image_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/image/arbitrage_' + yesterday

    lines = measure.load_history_data()
    measure_ticker = measure.get_measure_ticker()

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
                                                    "close_gap": close_gap, "close_data": close_data,
                                                    "close_gap_avg": 0})
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
        plt.figure(figure_idx,figsize=(18, 12)) # 그래프 개수
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
    asyncio.run(make_graph())