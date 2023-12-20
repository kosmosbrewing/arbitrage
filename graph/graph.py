import asyncio
from matplotlib import pyplot as plt
import measure
import graphUtil
from measure import *

async def make_graph():
    today = datetime.date.today()

    # 하루 전 날짜 계산
    yesterday = today - datetime.timedelta(days=1)
    yesterday = yesterday.strftime("%Y%m%d")
    ENV = graphUtil.ENV

    if ENV == 'real':
        image_file_path = '/root/arbitrage/image/arbitrage_' + yesterday
    elif ENV == 'local':
        image_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/image/arbitrage_' + yesterday

    lines = graphUtil.load_history_data()
    measure_ticker = measure.get_measure_ticker()

    # BTC랑 ETH는 무조건 추가
    measure_ticker['BTC'] = {"units": []}
    measure_ticker['ETH'] = {"units": []}
    measure_ticker['XRP'] = {"units": []}
    measure_ticker['SOL'] = {"units": []}

    front_gap = {}

    for line in lines:
        try:
            split_data = line.split('|')
            date_time = split_data[0].split('[INFO')[0]
            date = date_time.split(' ')[0].split('[')[1]
            date_hour = date_time.split(' ')[1].split(':')[0]
            date_min = date_time.split(' ')[1].split(':')[1]
            date_second = date_time.split(' ')[1].split(':')[2].split(',')[0]
            hour_min_second = date_hour + ":" + date_min + ":" + date_second

            ticker = split_data[1]
            open_gap = float(split_data[3])
            close_gap = float(split_data[6])
            btc_open_gap = float(split_data[9])
        except:
            continue

        if ticker not in front_gap:
            front_gap[ticker] = {"front_open_gap": open_gap, "front_close_gap": close_gap, "front_btc_open_gap": btc_open_gap}

        front_open_gap = front_gap[ticker]['front_open_gap']
        front_close_gap = front_gap[ticker]['front_close_gap']
        front_btc_open_gap = front_gap[ticker]['front_btc_open_gap']

        if abs(open_gap - front_open_gap) > 3 or abs(close_gap - front_close_gap) > 3 or abs(btc_open_gap - front_btc_open_gap) > 3:
            continue

        front_gap[ticker]['front_open_gap'] = open_gap
        front_gap[ticker]['front_close_gap'] = close_gap
        front_gap[ticker]['front_btc_open_gap'] = btc_open_gap

        # 전일자 데이터 담기
        if ticker in measure_ticker:
            measure_ticker[ticker]['units'].append({"open_gap": open_gap, "close_gap": close_gap,
                                                    "btc_open_gap": btc_open_gap, "hour_min_second": hour_min_second})

    # 그래프 변수 초기화
    subplot_loc = []
    for i in range(0,100):
        subplot_loc.append([221, 222, 223, 224])

    figure_idx = 0
    subplot_idx = 0
    image_set = []

    for graph_ticker in measure_ticker:
        # 데이터 준비
        open_gap = []
        close_gap = []
        btc_open_gap = []
        time = []

        for i in range(0, len(measure_ticker[graph_ticker]['units'])):
            open_gap.append(float(measure_ticker[graph_ticker]['units'][i]['open_gap']))
            close_gap.append(float(measure_ticker[graph_ticker]['units'][i]['close_gap']))
            btc_open_gap.append(float(measure_ticker[graph_ticker]['units'][i]['btc_open_gap']))
            time.append(measure_ticker[graph_ticker]['units'][i]['hour_min_second'])

        time_len = len(time)

        # 그래프 그리기
        plt.figure(figure_idx,figsize=(18, 12)) # 그래프 개수
        plt.subplot(subplot_loc[figure_idx][subplot_idx]) # 그래프 위치
        plt.title(graph_ticker + '[' + date + ']')

        #plt.plot(open_gap, label='open', color='blue', linewidth=0.6)
        #plt.plot(close_gap, label='close', color='red', linewidth=0.6)
        #plt.plot(btc_open_gap, label='open', color='black', linewidth=0.6)

        plt.xlabel('time')
        plt.ylabel('gap')

        plt.plot(time, open_gap, label='open', color='blue', linewidth=0.6)
        plt.plot(time, close_gap, label='close', color='red', linewidth=0.6)
        plt.plot(time, btc_open_gap, label='open', color='black', linewidth=0.6)

        show_x_values = [time[0], time[round(time_len/6)], time[round(time_len*2/6)], time[round(time_len*3/6)],
                         time[round(time_len*4/6)], time[round(time_len*5/6)], time[time_len-1]]
        plt.xticks(show_x_values)
        for val in show_x_values:
            plt.axvline(x=val, color='lightgray', linestyle='--', linewidth=0.7)

        subplot_idx += 1

        if subplot_idx == 4:
            image_temp = image_file_path + '_' + str(figure_idx+1) + '.png'
            image_set.append(image_temp)
            plt.savefig(image_temp, format='png')
            figure_idx += 1
            subplot_idx = 0

    if subplot_idx != 4:
        image_temp = image_file_path + '_' + str(figure_idx + 1) + '.png'
        image_set.append(image_temp)
        plt.savefig(image_temp, format='png')

    #plt.show()
    message = '[News Coo 🦤]\n🔵진입김프(UPBIT⬆️/BINANCE⬇️)|\n🔴탈출김프(UPBIT⬇️/BINANCE⬆️)|\n⚫️Bitcoin진입김프(UPBIT⬆️/BINANCE⬇️)'
    await graphUtil.send_to_telegram(message)

    for image in image_set:
        await graphUtil.send_to_telegram_image(image)

if __name__ == "__main__":
    asyncio.run(make_graph())