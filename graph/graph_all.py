import asyncio
import logging
import sys
import traceback
from matplotlib import pyplot as plt
import measure
import graphUtil
from measure import *
from api import upbit

today = datetime.date.today()
# 하루 전 날짜 계산
yesterday = today - datetime.timedelta(days=1)
yesterday = yesterday.strftime("%Y%m%d")

async def make_graph(date=yesterday):
    ENV = graphUtil.ENV
    logging.info(f"기준 일자: {date}")

    if ENV == 'real':
        image_file_path = '/root/arbitrage/image/arbitrage_' + str(date)
    elif ENV == 'local':
        image_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/image/arbitrage_' + str(date)

    lines = graphUtil.load_history_data(date)

    temp_list = {}
    measure_ticker = {}

    measure_ticker['BTC'] = {"units": []}
    measure_ticker['ETH'] = {"units": []}

    front_gap = {}
    i = 0


    for line in lines:
        try:
            split_data = line.split('|')
            date_time = split_data[0].split('[INFO')[0]

            if i==0:
                s_date = date_time.split(' ')[0].split('[')[1]

            date = date_time.split(' ')[0].split('[')[1]
            date_hour = date_time.split(' ')[1].split(':')[0]
            date_min = date_time.split(' ')[1].split(':')[1]
            date_second = date_time.split(' ')[1].split(':')[2].split(',')[0]
            hour_min_second = date_hour + ":" + date_min + ":" + date_second

            ticker = split_data[1]
            open_gap = float(split_data[3])
            close_gap = float(split_data[6])
            btc_open_gap = float(split_data[9])

            upbit_15_rsi = float(split_data[17].split('/')[0])
            binance_15_rsi = float(split_data[19].split('/')[0])
            upbit_240_rsi = float(split_data[17].split('/')[1])
            binance_240_rsi = float(split_data[19].split('/')[1])
            rsi_15_gap = float(split_data[21].split('/')[0])
            rsi_240_gap = float(split_data[21].split('/')[1])
            i += 1
        except:
            continue

        if ticker not in front_gap:
            front_gap[ticker] = {"front_open_gap": open_gap, "front_close_gap": close_gap,
                                 "front_btc_open_gap": btc_open_gap}

        try:
            front_open_gap = front_gap[ticker]['front_open_gap']
            front_close_gap = front_gap[ticker]['front_close_gap']
            front_btc_open_gap = front_gap[ticker]['front_btc_open_gap']

            if abs(open_gap - front_open_gap) > 1 or abs(close_gap - front_close_gap) > 1 or abs(
                    btc_open_gap - front_btc_open_gap) > 1:
                continue

            front_gap[ticker]['front_open_gap'] = open_gap
            front_gap[ticker]['front_close_gap'] = close_gap
            front_gap[ticker]['front_btc_open_gap'] = btc_open_gap

            # 전일자 데이터 담기
            if ticker in measure_ticker:
                measure_ticker[ticker]['units'].append({"open_gap": open_gap, "close_gap": close_gap,
                                                        "btc_open_gap": btc_open_gap, "hour_min_second": hour_min_second,
                                                        "upbit_15_rsi": upbit_15_rsi, "binance_15_rsi": binance_15_rsi,
                                                        "upbit_240_rsi": upbit_240_rsi, "binance_240_rsi": binance_240_rsi,
                                                        "rsi_15_gap": rsi_15_gap, "rsi_240_gap": rsi_240_gap})
        except Exception as e:
            logging.info(e)

    # 그래프 변수 초기화
    subplot_loc = []
    for i in range(0, 100):
        subplot_loc.append([411, 412, 413, 414])

    figure_idx = 0
    subplot_idx = 0
    image_set = []

    for graph_ticker in measure_ticker:
        # 그래프 그리기
        open_gap = []
        close_gap = []
        btc_open_gap = []
        upbit_15_rsi = []
        upbit_240_rsi = []
        binance_15_rsi = []
        binance_240_rsi = []

        rsi_15_gap = []
        rsi_240_gap = []
        remain_dix = 0

        try:
            for i in range(0, len(measure_ticker[graph_ticker]['units'])):
                open_gap.append(float(measure_ticker[graph_ticker]['units'][i]['open_gap']))
                close_gap.append(float(measure_ticker[graph_ticker]['units'][i]['close_gap']))
                btc_open_gap.append(float(measure_ticker[graph_ticker]['units'][i]['btc_open_gap']))
                upbit_15_rsi.append(float(measure_ticker[graph_ticker]['units'][i]['upbit_15_rsi']))
                upbit_240_rsi.append(float(measure_ticker[graph_ticker]['units'][i]['upbit_240_rsi']))
                binance_15_rsi.append(float(measure_ticker[graph_ticker]['units'][i]['binance_15_rsi']))
                binance_240_rsi.append(float(measure_ticker[graph_ticker]['units'][i]['binance_240_rsi']))
                rsi_15_gap.append(float(measure_ticker[graph_ticker]['units'][i]['rsi_15_gap']))
                rsi_240_gap.append(float(measure_ticker[graph_ticker]['units'][i]['rsi_240_gap']))

        except Exception as e:
            logging.info(f"Exception : {e}")

        try:
            #### 데이터 그래프
            plt.figure(figure_idx, figsize=(18, 12))  # 그래프 개수
            plt.subplot(subplot_loc[figure_idx][subplot_idx])  # 그래프 위치
            plt.title(graph_ticker + '_' + s_date + '_' + date)
            plt.plot(open_gap, label='open', color='blue', linewidth=0.4)
            plt.plot(close_gap, label='close', color='red', linewidth=0.6)
            plt.plot(btc_open_gap, label='open', color='black', linewidth=0.6)
            plt.ylabel('gap')
            subplot_idx += 1

            #### RSI GAP 그래프
            plt.figure(figure_idx, figsize=(18, 12))
            plt.subplot(subplot_loc[figure_idx][subplot_idx])  # 그래프 위치
            # plt.title(graph_ticker + '_RSI_GAP_' + s_date + '_' + date)
            plt.plot(rsi_15_gap, label='open', color='purple', linewidth=0.6)
            plt.ylabel('rsi 15 gap')
            image_temp = image_file_path + '_' + str(figure_idx + 1) + '.png'
            image_set.append(image_temp)
            plt.savefig(image_temp, format='png')
            subplot_idx += 1

            #### RSI GAP 그래프
            plt.figure(figure_idx, figsize=(18, 12))
            plt.subplot(subplot_loc[figure_idx][subplot_idx])  # 그래프 위치
            # plt.title(graph_ticker + '_RSI_GAP_' + s_date + '_' + date)
            plt.plot(rsi_240_gap, label='open', color='pink', linewidth=0.6)
            plt.ylabel('rsi 240 gap')
            subplot_idx += 1

            #### RSI 그래프
            plt.figure(figure_idx, figsize=(18, 12))
            plt.subplot(subplot_loc[figure_idx][subplot_idx])  # 그래프 위치
            # plt.title(graph_ticker + '_RSI15_' + s_date + '_' + date)
            dark_yellow = '#FFB700'
            plt.plot(upbit_15_rsi, label='open', color='blue', linewidth=0.3)
            plt.plot(binance_15_rsi, label='open', color=dark_yellow, linewidth=0.3)
            plt.plot(upbit_240_rsi, label='open', color='blue', linewidth=1.75)
            plt.plot(binance_240_rsi, label='open', color=dark_yellow, linewidth=1.75)
            plt.ylabel('rsi 15')
            subplot_idx += 1

            if subplot_idx == len(subplot_loc[0]):
                image_temp = image_file_path + '_' + str(figure_idx + 1) + '.png'
                image_set.append(image_temp)
                plt.savefig(image_temp, format='png')
                figure_idx += 1
                subplot_idx = 0
                remain_dix = 1

        except Exception as e:
            logging.info(f"{ticker} 오류.. Continue... {e}")

    try:
        image_set = list(set(image_set))

        for image in image_set:
            await graphUtil.send_to_telegram_image(image)
    except Exception as e:
        logging.info(e)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        date = sys.argv[1]
        asyncio.run(make_graph(date))
    else:
        asyncio.run(make_graph())
