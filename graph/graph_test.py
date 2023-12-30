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

    measure_ticker = {}

    if ENV == 'real':
        history_file_path = '/root/arbitrage/log/premium_data_test'
    elif ENV == 'local':
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data_test'

    if os.path.exists(history_file_path):
        with open(history_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    else:
        print(f"There is no File {history_file_path}")
    # BTC랑 ETH는 무조건 추가
    measure_ticker['ETH'] = {"units": []}

    front_gap = {}
    line_count = 0
    for line in lines:
        try:
            line_count += 1
            split_data = line.split('|')
            date_time = split_data[0].split('[INFO')[0]
            date = date_time.split(' ')[0].split('[')[1]
            date_hour = date_time.split(' ')[1].split(':')[0]
            date_min = date_time.split(' ')[1].split(':')[1]
            date_second = date_time.split(' ')[1].split(':')[2].split(',')[0]
            hour_min_second = date_hour + ":" + date_min + ":" + date_second

            if line_count == 1:
                start_date = date_time.split(' ')[0].split('[')[1]

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
        subplot_loc.append([111])

    figure_idx = 0
    subplot_idx = 0
    image_set = []

    if ENV == 'real':
        image_file_path = '/root/arbitrage/image/arbitrage_test'
    elif ENV == 'local':
        image_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/image/arbitrage_test'

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

        # 그래프 그리기
        plt.figure(figure_idx,figsize=(18, 12)) # 그래프 개수
        plt.subplot(subplot_loc[figure_idx][subplot_idx]) # 그래프 위치
        plt.title(graph_ticker + '[' + start_date + '-' + date + ']')

        plt.plot(open_gap, label='open', color='blue', linewidth=0.6)
        plt.plot(close_gap, label='close', color='red', linewidth=0.6)
        plt.plot(btc_open_gap, label='open', color='black', linewidth=0.6)

        plt.ylabel('gap')
        subplot_idx += 1

        image_temp = image_file_path + '~' + str(figure_idx + 1) + '.png'
        image_set.append(image_temp)
        plt.savefig(image_temp, format='png')

    #plt.show()
    message = '[News Coo 🦤]\n🔵진입김프(UPBIT⬆️/BINANCE⬇️)|\n🔴탈출김프(UPBIT⬇️/BINANCE⬆️)|\n⚫️Bitcoin진입김프(UPBIT⬆️/BINANCE⬇️)'
    await graphUtil.send_to_telegram(message)

    for image in image_set:
        await graphUtil.send_to_telegram_image(image)

if __name__ == "__main__":
    asyncio.run(make_graph())